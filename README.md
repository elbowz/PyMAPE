[![PyPI Version][pypi-shield]][pypi-url]
[![Py Version][pyversion-shield]][pypi-url]
[![Issues][issues-shield]][issues-url]
[![GPL License][license-shield]][license-url]
[![Homie][rxpy-shield]][rxpy-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<p align="center">
  <img src="https://github.com/elbowz/PyMAPE/raw/main/docs/img/logo.png" alt="PyMAPE" width="400">
  <h3 align="center">Decentralized Monitor Analyze Plan Execute Knowledge loops</h3>
  <p align="center">
    Software framework to support the development and deployment of Autonomous (Self-Adaptive) Systems
  </p>
</p>
<br />

## Getting Started

### Install

```bash
pip install pymape
```

See [Examples](https://github.com/elbowz/PyMAPE#examples) for play with some MAPE-K patterns.

### Install for Developers and Contributors

```bash
git clone https://github.com/elbowz/PyMAPE.git
cd PyMAPE
poetry install
```
*note:* you need to have already installed [poetry](https://python-poetry.org/)

Then use `poetry shell` and/or `poetry run` (eg. `poetry run examples/coordinated-ambulance.py --speed 80`) to exec your script inside the development environment.

### First loop (Ambulance)

![ambulance diagram](https://github.com/elbowz/PyMAPE/raw/main/docs/img/mape-ambulance.png)

```python
import mape
from mape.loop import Loop

""" MAPE Loop and elements definition """
loop = Loop(uid='ambulance_emergency')

@loop.monitor
def detect(item, on_next, self):
    if 'speed_limit' in item:
        # Local volatile knowledge
        self.loop.k.speed_limit = item['speed_limit']
    elif 'emergency_detect' in item:
        on_next(item['emergency_detect'])

@loop.plan(ops_in=ops.distinct_until_changed())
async def policy(emergency, on_next, self):
    if emergency is True:
        self.last_speed_limit = self.loop.k.speed_limit
        new_speed = max(self.last_speed_limit, self.emergency_speed)

        on_next({'speed': new_speed})
        on_next({'siren': True})
    else:
        on_next({'speed': self.last_speed_limit})
        on_next({'siren': False})

policy.emergency_speed = 160

@loop.execute
def exec(item: dict, on_next):
    if 'speed' in item:
        ambulance.speed_limit = item['speed']
    if 'siren' in item:
        ambulance.siren = item['siren']

for element in loop:
    element.debug(Element.Debug.IN)

""" MAPE Elements connection """
detect.subscribe(policy)
policy.subscribe(exec)

# Starting monitor...
detect.start()
```
### Traversing

```python
# Iterate over loops and element
for loop in mape.app:
    logger.debug(f"* {loop.uid}")
    for element in loop:
        logger.debug(f" - {element.uid}")

# Get all Execute elements
[element for element in loop_obj if isinstance(element, Execute)]

# Different access way to loop/element through dot-notation (path)
mape.app.loop_uid.element_uid
mape.app['loop_uid.element_uid']
```

## Docs

### Slides

[Introduction to PyMAPE](https://github.com/elbowz/PyMAPE/raw/main/docs/slides.pdf) with examples

### Examples

Implementation of the 5 decentralized (and distributed) MAPE patterns described in the paper:  
["On Patterns for Decentralized Control in Self-Adaptive Systems", Danny Weyns](https://www.ics.uci.edu/~seal/publications/2012aSefSAS.pdf)

* **Ambulance-Car Emergency** (Information Sharing and Coordinated Control)
* **Average Speed Enforcement** (Master/Slave)
* **Dynamic Carriageway** (Regional Planning)
* **Cruise Control with Distance Hold** (Hierarchical Control)

If you want try some examples (path `examples/`), refer to section `# CLI EXAMPLES` inside the source code of each one.  

The examples need furthers requirements, please see [pyproject.toml](https://github.com/elbowz/PyMAPE/raw/main/pyproject.toml) or use poetry to [install them](https://github.com/elbowz/PyMAPE#install-for-developers-and-contributors).  

You also need a Redis and InfluxDB instance running, for example:

```bash
docker run --name mape-redis -p 6379:6379  \
-v $(pwd)/docker/redis:/usr/local/etc/redis  \
--rm redis redis-server /usr/local/etc/redis/redis.conf
```

```bash
docker run --name mape-influxdb -p 8086:8086 \
-v $(pwd)/docker/influxdb/data:/var/lib/influxdb2 \
-v $(pwd)/docker/influxdb/conf:/etc/influxdb2 \
-e DOCKER_INFLUXDB_INIT_MODE=setup \
-e DOCKER_INFLUXDB_INIT_USERNAME=user \
-e DOCKER_INFLUXDB_INIT_PASSWORD=qwerty123456 \
-e DOCKER_INFLUXDB_INIT_ORG=univaq \
-e DOCKER_INFLUXDB_INIT_BUCKET=mape \
-e DOCKER_INFLUXDB_INIT_RETENTION=1w \
-e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=<GENERATE_OR_TAKE_FROM_CONFIG_YAML> \
--rm influxdb:2.0
```

See source for more information.

[pypi-shield]: https://img.shields.io/pypi/v/pymape?style=for-the-badge
[pypi-url]: https://pypi.org/project/pymape/
[pyversion-shield]: https://img.shields.io/pypi/pyversions/pymape?style=for-the-badge
[issues-shield]: https://img.shields.io/github/issues/elbowz/pymape.svg?style=for-the-badge
[issues-url]: https://github.com/elbowz/pymape/issues
[license-shield]: https://img.shields.io/github/license/elbowz/pymape.svg?style=for-the-badge
[license-url]: /LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/emanuele-palombo/
[rxpy-shield]: https://img.shields.io/static/v1?label=Powered&message=RxPY&style=for-the-badge&color=informational
[rxpy-url]: https://github.com/ReactiveX/RxPY