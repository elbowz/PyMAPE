#!/usr/bin/env python3

import logging

import mape
from mape.utils import LogObserver, init_logger, task_exception, setdefaultattr
from mape.loop import Loop
from mape.base_elements import Element
from mape import operators as ops
from mape.remote.redis import SubObservable
from mape.remote.influxdb import InfluxObserver

from coordinated_common import prompt_setup

logger = init_logger(lvl=logging.INFO)


async def async_main(name, init_speed, with_redis=False):
    from fixtures import VirtualAmbulance

    # Managed elements
    ambulance = VirtualAmbulance(name, speed=init_speed)
    # Stdin/key bindings setup for user input
    prompt_setup(ambulance)

    """ MAPE Loop and elements definition """
    loop = Loop(uid='ambulance_emergency')

    # External monitor element
    from coordinated_common import emergency_detect_cls

    emergency_detect = emergency_detect_cls(loop=loop)

    ambulance.set_callback('speed', emergency_detect)
    ambulance.set_callback('speed_limit', emergency_detect)
    ambulance.set_callback('emergency_detect', emergency_detect)

    @loop.plan(ops_in=ops.distinct_until_changed())
    async def emergency_policy(emergency, on_next, self):
        if emergency is True:
            self.last_speed_limit = self.loop.k.speed_limit
            new_speed = max(self.last_speed_limit, self.emergency_speed)

            on_next({'speed': new_speed})
            on_next({'siren': True})
        else:
            last_speed_limit = setdefaultattr(self, 'last_speed_limit', self.loop.k.speed_limit)

            on_next({'speed': last_speed_limit})
            on_next({'siren': False})

    emergency_policy.emergency_speed = 160

    @loop.execute(ops_in=ops.distinct_until_changed())
    def emergency_exec(item: dict, on_next):
        if 'speed' in item:
            ambulance.speed_limit = item['speed']
        if 'siren' in item:
            ambulance.siren = item['siren']

    # for element in loop:
    #     element.debug(Element.Debug.IN)

    """ MAPE Elements LOCAL connection """
    emergency_detect.subscribe(emergency_policy)
    emergency_policy.subscribe(emergency_exec)

    # Push monitored state to InfluxDB
    emergency_detect.subscribe(
        # All args are optional (more info see InfluxObserver source)
        InfluxObserver(
            measurement='coordinated-ambulance',
            tags=('name', name),
            fields_mapper=lambda item: ('emergency', item)
        )
    )

    # Service monitor for monitor speed
    from coordinated_common import push_to_influx_cls
    push_to_influx = push_to_influx_cls(loop=loop)
    push_to_influx.subscribe(InfluxObserver())
    ambulance.set_callback('speed', push_to_influx)

    """ MAPE Elements REMOTE connection """

    if with_redis:
        # Listen/Subscribe for others cars emergency_detect output
        # notes: for clarity can be used "emergency_policy.port_in" and "emergency_detect.uid"
        SubObservable(f"car_*_safety.{emergency_detect}").subscribe(emergency_policy)

    # Starting monitor...
    logger.info(f"{emergency_detect} element started")
    emergency_detect.start()


if __name__ == '__main__':
    logger.debug('START...')

    # CLI EXAMPLES
    # * Redis: python -m coordinated-ambulance --speed 80
    # * REST: python -m coordinated-ambulance --speed 80 --web-server 0.0.0.0:6000
    #
    # notes:
    #   * "python -m coordinated-ambulance" == "python coordinated-ambulance.py" == "./coordinated-ambulance.py"
    #   * Use F1/F2 keys to report the start/stop of an emergency

    import argparse
    parser = argparse.ArgumentParser(description='MAPE Loop')
    parser.add_argument('-n', '--name', type=str, metavar='CAR_NAME', default='Ambulance')
    parser.add_argument('-s', '--speed', type=int, metavar='CAR_SPEED', default=80)
    parser.add_argument('-w', '--web-server', type=str, metavar='HOST_PORT')
    args = parser.parse_args()

    from os import path

    init_kwargs = {'rest_host_port': args.web_server} if args.web_server else {'redis_url': 'redis://localhost:6379'}
    init_kwargs = {**init_kwargs, 'config_file': path.dirname(path.realpath(__file__)) + '/coordinated.yml'}

    mape.init(debug=False, **init_kwargs)
    mape.run(entrypoint=async_main(args.name, init_speed=args.speed, with_redis=('redis_url' in init_kwargs)))

    logger.debug('...STOP')
