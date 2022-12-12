PyMAPE can be simply installed using pip, directly in your [`system`][system] or in a separated [`virtual environment`][virtual environment] to keep clean your main system.

[system]: javascript:document.querySelector("label[for=__tabbed_1_1]").click()
[virtual environment]: javascript:document.querySelector("label[for=__tabbed_1_2]").click()

=== "System"

    ``` {.console .termy}
    $ pip install pymape
    
    ---> 100%
    ```

=== "Virtualenv"
  
    ``` {.console .termy}
    $ python -m venv venv
    $ source venv/bin/activate
    # (venv) $ pip install pymape
    ---> 100%
    ```

???+ info "Examples dependencies"
    
    If you intend play with the provided [examples] of different MAPE-K patterns, you should also install the dependency `#!console pip install -r examples/requirements.txt`.

    Anyway before play with them, we need to run some docker containers. We will see them soon. 

[examples]: https://github.com/elbowz/PyMAPE/tree/main/examples

## Installation for Developers and Contributors

If you want to contribute to the project, you have use [poetry] and follow the steps below:

[poetry]: https://python-poetry.org/

``` {.console .termy}
$ git clone https://github.com/elbowz/PyMAPE.git
$ cd PyMAPE
$ poetry install
---> 100%
```

Then use `#!console poetry shell` and/or `#!console poetry run` (eg. `#!console poetry run examples/coordinated-ambulance.py --speed 80`) to exec a script inside the development environment.

??? info "Poetry and examples dependencies"

    Using [poetry] you won't have to install the python packages dependencies needed to execute the [examples].


