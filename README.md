## TODO
* MapeElement dependency start
  * Start order based on subscribers.
    Visita grafo in profondità e start() dalle foglie
* MapeElement debug IN e OUT  
  Valuta se meglio metterlo (per dare un ordine migliore nel log?!) nel port_in e port_out, facendo start e stop, o fisso (ie do_action()) inibendo la print
* Test _add_func() with a CustomElement user Class
* ~~mape.get('loop/element') or mape.get('loop')~~
* Run a docker container directly form the python code (eg. sub/client/minor-loop autostart)?!
* MapeLoop/Application auto-link/subscribe MapeElement following order (maybe pattern):
  * MANUAL: DIY
  * REGISTER: Follow loop registering order
  * TYPE: M -> A -> P -> E
* MapeElement have to manage different kind of item/value:
  * MSG: classic msg with: payload/value, from (?!), through (?!), to (?!), timestamp (?!), hops (?!), 
  * METHOD: serialization object method call: method, params
* MapeLoop @decorator accept coroutine
* MapeLoop @decorator: @toclass, @instance, @register ?!
* Set default scheduler for pipe, subscribe, start, etc...
* Refactor mape.init() moving on top and add a mape.run() ?!
* ~~Change mape to a class, and implement similar to MapeLoop~~
* Remove param_self (form decorator), and insert automatically when self is in func signature
* Add Redis
  * share loops/elements 
  * as shared memory
  * pub/sub or stream for distributed communication
  * asyncio event shared?