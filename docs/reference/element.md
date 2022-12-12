L'`Element` is the central part of the framework. It will have to communicate with others elements in the seme loop or with externals ones. Usually you'll have a _Monitor_, followed by an _Analyzer_, then a _Planner_ and finally the _Executer_, but this order is not mandatory, and you can have different combination of them. 

## Internal view

Let's look inside an Element and try to understand how it works:
![Element exploded](../assets/img/notation_element_exploded.png){ style="background-color: white;" }

## Start behaviors

In the top-left corner you can see three icons characterizing the respective behaviour:

* :fontawesome-solid-pause: __manual start__ (_monitor_): the element cannot send or receive items until the `.start()` method invocation. This is often related to internal resource lifetime (eg. DB connection, socket, ...). It allows to connect all loops and elements before start receiving the stream.
* :fontawesome-solid-forward: __start on subscribe__ (_analyzer, planner_): the element will be started when someone is interested to it (ie. `subscribed()`).
* :fontawesome-solid-play: __start on init__ (_executer_): the element is ready from its initialization.

???+ info "Start / Stop"
    
    See in the above figure, the dotted line with at the end a scissor, to better understand the start/stop meaning.

    Each element can be started (`#!py element.start()`) and stopped (`#!py element.stop()`), and check the current state by (`#!py element.is_running`).


The different behaviours are defined in the classes `StartOnSubscrie`, `StartOnInit` allowing extension and change as preferred.

## Ports

On the front and back of the element, there are the `ports` (_IN_ and _OUT_). They allow both writing and reading of the stream. You can configure different architect flows, not only serial communication but also parallelization, multiplexing, fork, and merge of the stream.

???+ note "Stopped (isolated) element"    

    If an element is stopped, the ports are disconnected, and it is isolated, but still allowing the communication of others elements eventually connected to that ports (again see the image above to figure out).

## Pipes

Here you can add the ReactiveX [operators], applying in input and/or output:

* _filtering_ - eg. `filter()`, `distinct()`
* _pre and post processing_ - eg. `throttle()`, `debounce()`
* _minimizing the data exchange_ - eg. `sample()`
* _internal PyMAPE operators_ - eg. `router()`, `group_and_pipe()`
* _your custom ones_, etc...

## Function and CallMethod

The element can compute a "normal" stream, where each item in input can generate 0 or more items in output (with the use of `on_next(item)` function). 

???+ tip "No input"

    Rememeber that you are in the field of reactive programming and push messages. The element can generate a stream (items) without any input, or the contrary (eg. monitor element produce items without any input).

If you send a `CallMethod` object (as item), thanks to its payload you can call an element method with respective params. 

??? info "Message driven"

    `CallMethod` approach is based on the _message driven_ paradigm (part of reactive programming), where you increase the element decoupling between elements and formalize the use of a common interface. Of course, you can still call the element class method.

## Element notation

The framework trys also to introduce a graphical notation. In the figure below, you can see the final and imploded representation of an element.   

<figure markdown>
![Element graphical notation](../assets/img/notation_element_simple.png){ style="background-color: white; width: 300px" }
</figure>

`Start behaviour`, `ports`, `pipe operators`, `uid`, and `class` element are still visible.