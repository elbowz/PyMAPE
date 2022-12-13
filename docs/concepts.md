## Self-Adaptive System

A Self-Adaptive system (SAS) is able to automatically modify itself in response to changes in its operating __environment__ [^1].

The _"self"_ prefix indicates that the systems decide autonomously (i.e. without or with minimal interference) how to adapt changes in their contexts. While some self-adaptive system may be able to function without any human intervention, guidance in the form of higher-level __goals__ is useful and realized in many systems.

## MAPE-K loop

A system could be made Self-Adaptive by adding __sensors__ to monitor its runtime state, __actuators__ to change it at runtime, and a separate reasoning mechanism to decide when it is appropriate to adapt the system, and how best to do so.

This was famously referred to as the MAPE-K loop, or __Monitor-Analyze-Plan-Execute__ using a shared base of __Knowledge__ [^2]. This architecture exposes explicitly the concept of __feedback control loop__ and indentify the components and interfaces.

![MAPE-L loop](assets/img/mape-k.png){ .figure }

`Monitor`

:   Monitor the managed system and its context, filter the collected data and store relevant events in Knowledge.

`Analyze`

:   Explore the data, comparing it with known patterns, identifying any symptoms and saving them in the Knowledge as needed.

`Plan`

:   Interprets symptoms and devises a plan to achieve adaptation (or goal), usually according to guidelines and strategies.

`Execute`

:   Provides the control mechanisms to ensure the execution of the plan on the managed system.

`Knowledge`

:   Contains managed system information that can be shared among all MAPE components. It contains all the knowledge useful for the loop (eg. representation, policies to follow, metrics for evaluation, specific inference rules for each task, history, adaptation strategies, system topology, etc).

## Distributed and Decentralized

When systems are large, complex, and heterogeneous, a single MAPE-K loop may not be sufficient for managing adaptation. In such cases, multiple MAPE-K loops may be employed that manage different parts of the system.

In self-adaptive systems with multiple loops, the functions for monitoring, analyzing, planning, and effecting may be made by multiple components that coordinate with one another. That is, the functions may be __decentralized__ throughout the multiple MAPE-K loops __distributed__ on different nodes. [^3]

Different __patterns__ of interacting control loops have been used in practice by centralizing and decentralizing the functions of self-adaption in different ways.

!!! info

    Further and deeply information about different patterns related to decentralized and distributed system can be found in the paper ["On Patterns for Decentralized Control in Self-Adaptive Systems", Danny Weyns][weyns paper]

In the next sections of documentations, we will see these patterns through the implementation of some ad-hoc examples. Discovering different approaches, trade-off, and of course the PyMAPE framework.

[^1]: _"A survey on engineering approaches for self-adaptive systems"_, C. Krupitzer, F. M. Roth, S. VanSyckel, G. Schiele, and C. Becker
[^2]: _"An architectural blueprint for autonomic computing"_, IBM White Paper, vol. 31, no. 2006
[^3]: _"On Patterns for Decentralized Control in Self-Adaptive Systems"_, D. Weyns, B. Schmerl, V. Grassi, S. Malek, R. Mirandola, C. Prehofer, J. Wuttke, J. Andersson, H. Giese, and K. M. Göschka

--8<-- "docs/append.md"