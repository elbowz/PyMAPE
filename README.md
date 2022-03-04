## TODO
* MapeElement dependency start
  * Start order based on subscribers.
    Visita grafo in profondità e start() dalle foglie
* MapeElement debug IN e OUT (https://github.com/ReactiveX/RxPY/issues/497)
  Valuta se meglio metterlo (per dare un ordine migliore nel log?!) nel port_in e port_out, facendo start e stop, o fisso (ie do_action()) inibendo la print
* ~~Test _add_func() with a CustomElement user Class~~
* ~~mape.get('loop/element') or mape.get('loop')~~
* Run a docker container directly from the python code (eg. sub/client/minor-loop autostart)?!
* MapeLoop/Application auto-link/subscribe MapeElement following order (maybe pattern):
  * MANUAL: DIY
  * REGISTER: Follow loop registering order
  * TYPE: M -> A -> P -> E
* ~~MapeElement have to manage different kind of item/value:~~
  * ~~MSG: classic msg with: payload/value, from (?!), through (?!), to (?!), timestamp (?!), hops (?!),~~ 
  * ~~METHOD: serialization object method call: method, params~~
  ~~* MapeLoop @decorator accept coroutine~~
* ~~MapeLoop @decorator: @toclass, @instance, @register ?!~~
* Set default scheduler for pipe, subscribe, start, etc...
* Refactor mape.init() moving on top and add a mape.run() ?!
* ~~Change mape to a class, and implement similar to MapeLoop~~
* Remove param_self (form decorator), and insert automatically when self is in func signature
* Auto import and instance loop from files/modules in ./loops (package)
~~* Message not mandatory in the element (add filter not CallMethod and map on hops if Message)~~
* Gateway, maybe better call it Router
* Create a test (inspiraton: https://github.com/plataux/purse/blob/master/src/purse/collections.py)
* ~~Create Message and CallMethod factory method. Create used in Monitor. eg Message.create(value, element, dst=None)...where form element extract the src path~~
* Add Redis
  * share/sync loops/elements 
  ~~* as shared memory (https://github.com/plataux/purse)~~
  ~~* pub/sub or stream for distributed communication~~
  * asyncio event shared?! (https://docs.python.org/3/library/asyncio-sync.html#event)
    ~~* decorator for event publish/subscribe~~ 
    * namespaced in loop.uid or global
  * https://stackoverflow.com/questions/28785383/how-to-disable-persistence-with-redis
  * embed redis in python (https://pypi.org/project/redislite/, https://github.com/chekart/rediserver/blob/master/rediserver/test/embedded.py)
* SubObservable, PubObserver
  * ~~REST~~
  * gRPC
  * ~~Redis~~
* Implementare esempio per il coordinated e per l'information sharing (magari entrambi in due modi diversi: CallMethod / link the port-out of Element with a filter)
	* CallMethod
	* subscribe_handler 	
* Add __slots__ to class where can be useful (App, Loop, Element) (https://stackoverflow.com/questions/472000/usage-of-slots)
* ~~Add level class (aggregate loop)~~
~~* Add class Knowledge, an object compose loop, app, level~~
* Generalize (eredita): App, Level, Loop, Element
* Sanitize uid (no RESERVED_SEPARATOR, RESRVED_PREPEND)
* Merge mape.__init__ e Application.app ?!
* convert  Optional[str] = None => str | None = None
* Message, CallMethod as pydantic.BaseModel
* Add subscribe_handler* to knowledge, also and mainly declined to key new/change/delete...
* Autostart all unstarted Element on run
~~* move Unvicron start in init~~
* ~~add config file for web_server, redis, influxdb (token, org)~~
* ~~inject "src_host" in Message when receive it (FastAPI) - https://stackoverflow.com/questions/60098005/fastapi-starlette-get-client-real-ip~~ CANNOT BE DONE, MISSIONG THE SRC_PORT (where client listing)
* move loop.monitor/analyze/... under loop.add_monitor (or similar)
* REST OpenAPI documentation (text and other stuff in remote/rest/[api,setup])
* Monitor, Analyze, Plan, Execute should have a param to change the startOnSub, startOnInit
* Add waitForLoop to sync (Data hydratation) loop through redis. Should be used before connect mape element e so use mape.loop.element.uid...take inspiration from redislock (BAH?!)

## CLI
* `sudo docker run --name mape-redis -p 6379:6379 -v $(pwd)/docker/redis:/usr/local/etc/redis --rm redis redis-server /usr/local/etc/redis/redis.conf`
* `sudo docker run --name mape-influxdb -p 8086:8086 \
-v $(pwd)/docker/influxdb/data:/var/lib/influxdb2 \
-v $(pwd)/docker/influxdb/conf:/etc/influxdb2 \
-e DOCKER_INFLUXDB_INIT_MODE=setup \
-e DOCKER_INFLUXDB_INIT_USERNAME=user \
-e DOCKER_INFLUXDB_INIT_PASSWORD=qwerty123456 \
-e DOCKER_INFLUXDB_INIT_ORG=univaq \
-e DOCKER_INFLUXDB_INIT_BUCKET=mape \
-e DOCKER_INFLUXDB_INIT_RETENTION=1w \
-e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=CAUow6RTwUr5__6YE4MRCAyvxEIcStWcxHZD88d0E5yqbvNjziJ-e0x6BnEWTammct6qzHsak8-n7PKMnoMTaA== \
--rm influxdb:2.0`
* `|> toInt()` - bool cast to int (https://docs.influxdata.com/influxdb/v2.0/reference/syntax/flux/flux-vs-influxql/#cast-booleans-to-integers)
* `CONFIG SET notify-keyspace-events KA` (https://redis.io/topics/notifications)
* `curl -X POST -H "Content-Type: text/plain" --data "this is raw data" http://localhost:6060/loops/{loop_uid}/element/{element_uid}`
* `cd Projects/SecondLevelDegrees/courses/Thesis/source/playground/ && pyenv activate venv-3.8.12`
