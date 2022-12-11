## First loop

Let's write your first MAPE loop. You'll write a simplified loop of an ambulance that switch on/off the siren and increase speed in case of an emergency detected.

```python
import mape

mape.init() # (1)

# Our ambulance loop definition, named "ambulance"
loop = mape.Loop(uid='ambulance') # (2)

# Monitor element of ambulance loop
@loop.monitor # (3)
def detect(emergency, on_next): # (4)
    on_next(emergency)
```

1.  `#!py mape.init()` accept different params to setup `pymape`, allowing configuration by a config file and/or directly in the source code.
2.  `uid` is an __unique__ identification for the defined loop. If you don't pass an `uid`, system provide a random one for you.
3.  Decorator create and register the new element monitor to the ambulance `loop`.
4.  The function name `#!py detect` is used as `uid` of our element inside the ambulance loop.

So, we have a loop (`ambulance`) made up of a single monitor element called `detect`.

??? info "Loop and Element `uid`"

    Loop uid `ambulance` must be unique in the whole app, instead `detect` (monitor uid) must be so only within the loop to which it belongs. This allow to address an element by its path (eg. `ambulance.detect`). 

`#!py detect()` function is the monitor element. It accepts at least two params:

* __stream item__ (`emergency`) - the value in input of an element. The elements talk with each other by streams as [ReactiveX] philosophy.
* __on_next__ - is the function to call with the value to pass to the next linked elements (`#!py subscribed()`). It can be called 0 or N times, you haven't to confused with the function `#!py return`.

[ReactiveX]: https://en.wikipedia.org/wiki/ReactiveX

Go ahead with a `plan` for add policies in case of an emergency detected.

```python
@loop.plan(uid='custom_policy') # (1)
def policy(emergency, on_next, self):
    # Emergency plans
    if emergency is True:
        on_next({'speed': self.emergency_speed}) # (2)
        on_next({'siren': True})
    else:
        on_next({'speed': 80})
        on_next({'siren': False})
                 
policy.emergency_speed = 180
```

1.  Differently from the monitor, here we choose the element `uid` (`custom_policy` instead of `policy`).
2.  Use the object property `emergency_speed` set externally.

In this case, `#!py policy()` has a third param `self`. When you add it to the function signature, you can directly access to the `Element` object behind the scene.

This time, respect previous `#!py detect()`, you pass a `dict` to the next linked element.

The last element defined and registered is the execute element, `exec` applies the plan on the managed system (ie. ambulance), in our case simply print an output.

```python
@loop.execute
def exec(item, on_next):
    if 'speed' in item:
        print(f"Speed: {item['speed']} Km/h")
    if 'siren' in item:
        print(f"Siren is {'ON' if item['siren'] else 'OFF'}")
```

The last step to complete ambulance loop is to connect (`subscribe()`) the three elements:

=== "Subscribe"

    ```python
    detect.subscribe(policy)
    policy.subscribe(exec)
    ```

=== "Pipe"

    ```python
    from mape import operators as ops # (1)
    
    # Alternative way
    detect.pipe(
      ops.through(policy),
      ops.through(exec)
    ).subscribe()
    ```

    1.  `ops` are all the RxPY [operators] plus some more extras.

You are finally ready to try your ambulance emergency system, sending a detected emergency to the monitor element `detect`:

```python
detect(True) # (1)
```

1.  Just call the `#!py detect()` function and pass the item as param.

As you can see, __nothing happens__!

This is the wanted behaviour, because you have to start element `detect` whenever you are ready to receive the stream.

??? info "Different elements behaviour"

    Elements can have 3 different behaviours respect to the stream passing through them:
  
    * __manual start__ (_monitor_): the element cannot send or receive items until the `.start()` method invocation. This is often related to internal resource lifetime (eg. DB connection, socket, ...). This allow to connect all loops and elements before start receiving the stream.
    * __start on subscribe__ (_analyzer, planner_): the element will be started when someone is interested to it (ie. `subscribed()`).
    * __start on init__ (_executer_): the element is ready from its initialization.

So, we start del monitor element and simulate an emergency:

```python
detect.start()
detect(True)
```

Get the results:

    Speed: 180
    Siren is ON

Again, ending the emergency (ie. `False`):

```python
detect(False)
```

Get the results:

    Speed: 80
    Siren is OFF

## Operators

Inspired by the functional programming, there are plenty [operators] available in RxPY, they can be chained in a pipeline, allowing _transformations, combinations, filtering, grouping, error managing, applying conditions, making math operations, and so on_.

There are more than 140 operators (about 400 variants), and we advise and encourage the creation of your custom operators following your need.

## Traversing

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


[operators]: https://rxpy.readthedocs.io/en/latest/operators.html