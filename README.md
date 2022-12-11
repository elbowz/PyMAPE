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
    <img src="https://github.com/elbowz/PyMAPE/raw/main/docs/img/logo.png" alt="PyMAPE" width="400">
    <h4 align="center">Distributed and decentralized MonitorAnalyzePlanExecute-Knowledge loops framework</h3>
    <p align="center">
        Framework to support the development and deployment of Autonomous (Self-Adaptive) Systems
    </p>
</p>

---

* __Source Code__: [https://github.com/elbowz/PyMAPE](https://github.com/elbowz/PyMAPE)
* __Documentation__: [https://elbowz.github.io/PyMAPE](https://elbowz.github.io/PyMAPE) - _WIP_

---

## Install

```bash
pip install pymape
```

## Examples

Implementation of the 5 decentralized (and distributed) MAPE patterns described in the paper:  
["On Patterns for Decentralized Control in Self-Adaptive Systems", Danny Weyns](https://www.ics.uci.edu/~seal/publications/2012aSefSAS.pdf)

* **Ambulance-Car Emergency** (Information Sharing and Coordinated Control)
* **Average Speed Enforcement** (Master/Slave)
* **Dynamic Carriageway** (Regional Planning)
* **Cruise Control with Distance Hold** (Hierarchical Control)

If you want try some examples (path `examples/`), refer to section `# CLI EXAMPLES` inside the source code of each one.

[Slide - Introduction to PyMAPE](https://github.com/elbowz/PyMAPE/raw/main/docs/slides.pdf) with examples

The examples need furthers requirements, please see [pyproject.toml](https://github.com/elbowz/PyMAPE/raw/main/pyproject.toml) or use poetry to [install them](https://github.com/elbowz/PyMAPE#install-for-developers-and-contributors).  

You also need a Redis and InfluxDB instance running, for example:

```bash
docker run --name mape-redis -p 6379:6379  \
-v $(pwd)/docker/redis:/usr/local/etc/redis  \
--rm redis redis-server /usr/local/etc/redis/redis.conf
```

```bash
docker run --name mape-influxdb -p 8086:8086 \
-v $(pwd)/docker/influxdb/data:/var/lib/influxdb2 \
-v $(pwd)/docker/influxdb/conf:/etc/influxdb2 \
-e DOCKER_INFLUXDB_INIT_MODE=setup \
-e DOCKER_INFLUXDB_INIT_USERNAME=user \
-e DOCKER_INFLUXDB_INIT_PASSWORD=qwerty123456 \
-e DOCKER_INFLUXDB_INIT_ORG=univaq \
-e DOCKER_INFLUXDB_INIT_BUCKET=mape \
-e DOCKER_INFLUXDB_INIT_RETENTION=1w \
-e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=<GENERATE_OR_TAKE_FROM_CONFIG_YAML> \
--rm influxdb:2.0
```

See source for more information.