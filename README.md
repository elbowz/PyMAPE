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
  * REST 
  * gRPC
  ~~* Redis~~
* Implementare esempio per il coordinated e per l'information sharing (magari entrambi in due modi diverse: CallMethod / link the port-out of Element with a filter)
* Add __slots__ to class where can be useful (App, Loop, Element) (https://stackoverflow.com/questions/472000/usage-of-slots)
* ~~Add level class (aggregate loop)~~
~~* Add class Knowledge, an object compose loop, app, level~~
* Generalize (eredita): App, Level, Loop, Element
* Sanitize uid (no RESERVED_SEPARATOR, RESRVED_PREPEND)
* Merge mape.__init__ e Application.app ?!
* convert  Optional[str] = None => str | None = None

## CLI
* `sudo docker run --name mape-redis -p 6379:6379 -v $(pwd)/docker/redis:/usr/local/etc/redis --rm redis redis-server /usr/local/etc/redis/redis.conf`
* `CONFIG SET notify-keyspace-events KA` (https://redis.io/topics/notifications)
* `curl -X POST -H "Content-Type: text/plain" --data "this is raw data" http://localhost:6060/loops/{loop_uid}/element/{element_uid}`
* `sudo docker exec -it mape-redis bash`
* `pyenv activate venv-3.8.12`
