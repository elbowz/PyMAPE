<p align="center">
    <a href="https://pypi.org/project/pymape/"><img
        src="https://img.shields.io/pypi/v/pymape?style=flat-square"
        alt="PyPI Version"
    /></a>
    <a href="https://pypi.org/project/pymape/"><img
        src="https://img.shields.io/pypi/pyversions/pymape?style=flat-square"
        alt="Py Version"
    /></a>
    <a href="https://github.com/elbowz/pymape/issues"><img
        src="https://img.shields.io/github/issues/elbowz/pymape.svg?style=flat-square"
        alt="Issues"
    /></a>
    <a href="https://raw.githubusercontent.com/elbowz/PyMAPE/main/LICENSE"><img
        src="https://img.shields.io/github/license/elbowz/pymape.svg?style=flat-square"
        alt="GPL License"
    /></a>
    <a href="https://raw.githubusercontent.com/elbowz/PyMAPE/main/LICENSE"><img
        src="https://img.shields.io/static/v1?label=Powered&message=RxPY&style=flat-square&color=informational"
        alt="RxPY"
    /></a>
</p>

<p align="center">
    <img src="https://github.com/elbowz/PyMAPE/raw/main/docs/assets/img/logo.png" alt="PyMAPE" width="400">
    <h4 align="center">Distributed and decentralized MonitorAnalyzePlanExecute-Knowledge loops framework</h3>
    <p align="center">
        Framework to support the development and deployment of Autonomous (Self-Adaptive) Systems
    </p>
</p>

---

* __Source Code__: [https://github.com/elbowz/PyMAPE](https://github.com/elbowz/PyMAPE)
* __Documentation__: [https://elbowz.github.io/PyMAPE](https://elbowz.github.io/PyMAPE) - _WIP_

---

## Requirements

* Python 3.8+
* [RxPY]
* [PyYAML]
* [AIOHTTP]
* [FastAPI]
* [Uvicorn]
* [Redis-purse]
* [Influxdb-client]


## Key features

:   :material-numeric-1-circle-outline: __CONTAINMENT__   
    Reuse, modularity and isolation of MAPE components as __first-class entity__.

:   :material-numeric-2-circle-outline: __COMMUNICATION INTERFACE (STANDARDIZATION)__   
    Shared interface between components that allow __stream__ communication, filtering, pre/post processing, data exchange communication and routing.

:   :material-numeric-3-circle-outline: __DISTRIBUTION__   
    Multi-device distribution of MAPE loops and components.

:   :material-numeric-4-circle-outline: __DECENTRALIZED PATTERNS__   
    __Flat__ p2p and/or __hierarchical__ architectures of loops and components with concerns separation. Allowing runtime pattern reconfiguration (stopping/starting, (un)linking, adding/removing).

:   :material-numeric-5-circle-outline: __NETWORK COMMUNICATION PARADIGMS__   
    Different paradigms (blackboard, direct message) and protocols for various patterns interactions.

:   :material-numeric-6-circle-outline: __STATE / KNOWLEDGE__   
    Distributed __multi-scope__ (global, level, loop) Knowledge with partitioning and/or (full/partial async) replication.

## Paradigms and tools

:   :material-numeric-1-circle: __REACTIVE SYSTEM/PROGRAMMING AND STREAM__   
    System reactive to __external__ event. Pillars: Responsive, Resilient, Elastic and __Message Driven__. Specific case of event-driven programming to avoid callback hell.

:   :material-numeric-2-circle: __REACTIVEX (OBSERVER PATTERN)__   
    Observables represent a __source__ of events. An __observer__ subscribes to an observable to receive items emitted (Hot, Cold, Subject,etc). __Pipe operators__ modify streams flowing through them.

:   :material-numeric-3-circle: __ASYNCHRONOUS PROGRAMMING__   
    Manage (I/O bound) tasks concurrency with non-blocking I/O operations.

:   :material-numeric-4-circle: __REDIS, IN-MEMORY DATA STRUCTURE SERVER__   
    __Distributed__, in-memory key-value data structure (strings, hashes, lists, (ordered) sets, queue, lock) store, cache and __message broker__ with keyspace __notifications__. Partitioning and/or (full/partial async) replication.


!!! tip

    If you already know what is a Self-Adaptive system, a MAPE-K loop and related patterns, jump to:

    [Installation :material-arrow-right:](installation.md){ .md-button }

--8<-- "docs/append.md"