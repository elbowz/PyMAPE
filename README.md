## TODO
* MapeElement dependency start
  * Start order based on subscribers.
    Visita grafo in profondità e start() dalle foglie
* MapeElement debug IN e OUT  (https://github.com/ReactiveX/RxPY/issues/497)
  Valuta se meglio metterlo (per dare un ordine migliore nel log?!) nel port_in e port_out, facendo start e stop, o fisso (ie do_action()) inibendo la print
* ~~Test _add_func() with a CustomElement user Class~~
* ~~mape.get('loop/element') or mape.get('loop')~~
* Run a docker container directly form the python code (eg. sub/client/minor-loop autostart)?!
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
* Add Redis
  * share loops/elements 
  * as shared memory
  ~~* pub/sub or stream for distributed communication~~
  * asyncio event shared?
  * https://stackoverflow.com/questions/28785383/how-to-disable-persistence-with-redis

## CLI
* `sudo docker run --name mape-redis -p 6379:6379 --rm redis`
* `CONFIG SET notify-keyspace-events KE$` (https://redis.io/topics/notifications)