One important point of PyMAPE is the capability of decentralize (functionalities and data) and distribute loops on more devices. These features are reached by the remote package.

## Class diagram

PyMAPE tries to preserve the best flexibility to the user design choices. You know pros and cons of different communication architect based on __request-response__ (eg. polling) respect to __publish-subscribe__ (eg. data centralization). So there are some domains (and patterns) that prefer one approach over the other, or again hybrid one to exploit the advantage of each one.  

You can choose between:

* __RESTful__ implementation, allowing reading and writing access to the elements of your application
* __Redis__ as DB and message broker, allowing the communication between elements and also as shared memory (`Knowledge`) for distribute nodes.

![Remote package](../assets/img/remote-package.png){ .figure }

???+ info "Observable and Observer"

    In the class diagram there are some class with the post-fix ["Observer" and "Observable"][observable contract], key concepts in the ReactiveX library. Also the element ports use the same idea. You can think them as sink and source for your stream. 

### Graphical Notation

![Remote package](../assets/img/remote-notation.png){ .figure }

## REST

For enable the REST support you have to provide an `host:port` for the web server ([Uvicorn] used by [FastAPI]). For do that you can:

=== "init()" 

    ```python
    mape.init(rest_host_port="0.0.0.0:6060")
    ```

=== "mape.yml"

    ```yaml
    rest:
        host_port: 0.0.0.0:6060
    ```

Now you can get information about levels, loops, ad elements defined in your app, but mainly you can push items to any element port through a POST request (`POSTObserver` class).  

??? note "API documentation"

    API documentation and a web ui for test is available:
    
    * OpenAPI: [/openapi.json](http://0.0.0.0:6060/openapi.json)
    * Swagger: [/docs](http://0.0.0.0:6060/docs)
    * ReDoc: [/redoc](http://0.0.0.0:6060/redoc)
    
    Thanks to the [FastAPI] library.
    
    ![Rest swagger ui](../assets/img/remote-rest-swagger-ui.png){ .figure }

* `#!py POSTObserver(base_url, path, port, serializer, session)` 

    It behaves like a sink, sending the stream to the `host:port` device selected and element selected by the path.

    `base_url: str`
    
    :   In the format `host:port` of the REST API web server target.
    
    `path: str`
    
    :   Element path (`loop_uid.element_uid`) target
    
    `port: Port = Port.p_in`
    
    :   Destination port where inject the stream
    
    `serializer = None`

    `session: aiohttp.ClientSession = None`

### Example

In the following example you see a communication between two distributed devices (`Car_panda` and `Ambulance`), specifically between the port out of `detect` element of `car_panda` (`car_panda.detect`) and port in of `policy` element of `ambulance` (`ambulance.policy`).

![Remote package](../assets/img/remote-rest-example.png){ .figure }

Translated in python on device `Car_panda`

```python
from mape.remote.rest import POSTObserver

car = mape.Loop(uid='car_panda')

@car.monitor
def detect(item, on_next):
  ...

# Create the sink
ambulance_policy = POSTObserver("http://0.0.0.0:6060", "ambulance.policy")
# Connect detect to the sink
detect.subscribe(ambulance_policy)
```

and device `Ambulance`

```python
# Enable REST support
mape.init(rest_host_port="0.0.0.0:6060")

ambulance = mape.Loop(uid='ambulance')
...
@ambulance.plan(ops_in=ops.distinct_until_changed())
def policy(item, on_next):
    ...  
```

## Redis

For enable the Redis support you have to provide an url for your instance `redis://localhost:6379`. For do that you can:

=== "init()"

    ```python
    mape.init(redis_url="redis://localhost:6379")
    ```

=== "mape.yml"

    ```yaml
    redis:
        url: redis://localhost:6379
    ```

??? note "Redis instance"

    PyMAPE doesn't provide (yet) an instance of Redis so you have to run your own, for example using a docker container:

    ``` {.console .termy}
    $ docker run --name mape-redis -p 6379:6379 -v $(pwd)/docker/redis:/usr/local/etc/redis --rm redis redis-server /usr/local/etc/redis/redis.conf
    oO0OoO0OoO0Oo Redis is starting oO0OoO0OoO0Oo
    Redis version=6.2.6, bits=64, commit=00000000, modified=0, pid=1, just started
    Configuration loaded
    * monotonic clock: POSIX clock_gettime
    * Running mode=standalone, port=6379.
    Server initialized
    ```

Redis unlike REST have two class to allow stream communication (on distributed devices): `PubObserve` e `SubObservable`. 

This mean that you have to choose a channel name, and publish/subscribe a stream on it.

??? tip "Pattern matching"

    Redis supports channel pattern matching, allowing multi-points communication.

    * `car_?.detect`: can receive from `car_a.detect`, `car_b.detect`, etc...
    * `car_[xy].detect`: can receive only from `car_x.detect`, `car_y.detect`
    * `car_*`: can receive from `car_foo`, `car_bar`, etc...

### Example

Let's implement the previous example with Redis.

![Remote package](../assets/img/remote-redis-example.png){ .figure }

Translated in python on device `Car_panda`

```python
from mape.remote.redis import PubObserver
# Enable Redis support
mape.init(redis_url="redis://localhost:6379")

car = mape.Loop(uid='car_panda')

@car.monitor
def detect(item, on_next):
  ...

# Publish detect output on channel named "car_panda.detect"
detect.subscribe(PubObserver(detect.path))
```

and device `Ambulance`

```python
from mape.remote.redis import SubObservable
# Enable Redis support
mape.init(redis_url="redis://localhost:6379")

ambulance = mape.Loop(uid='ambulance')
...
@ambulance.plan(ops_in=ops.distinct_until_changed())
def policy(item, on_next):
    ...

# Subscribe to others cars 
# note: for clarity can be used "policy.port_in"
SubObservable("car_*.detect").subscribe(policy) # (1)
```

1. if you have access to car detect element you can use `#!py f"car_*.{detect}" == f"car_*.{detect.uid}"`  