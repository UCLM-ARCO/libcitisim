# Kafka Citisim Connector

This repo contains files to generate an image to forward events from citisim to Kafka.

## Requirements

Before to build the docker image we need next files:

- [libcitisim](https://bitbucket.org/arco_group/libcitisim/src/master/): You can download the latest build.
- [kafka-mirror](https://bitbucket.org/arco_group/libcitisim/src/master/examples/kafka-mirror/): You need to download all files.

### Kafka-mirror fix

If you inspect `kafka-mirror.py` you should see the declared shebang as `#!/usr/bin/python3`, you must change it to `#!/usr/bin/env python3`. This shebang is necessary for portability across different systems in case they have the language interpreter installed in different locations.

## Build

To build this project you only need to run the next command:

```
make
```

This command will create a new docker image named `kafka-connector-citisim:<DOCKER_IMAGE_TAG>`. Next, you can see the default values defined in `.env` file used to create the docker image.

|Variable   |Default Value   |Description   |
|:-:|:-:|---|
|PYTHON_VER   |3.6   |Python docker image base  |
|LIBCITISIM_VER   |latest   |Downloaded libcititism library version from its Bitbucket repo   |
|DOCKER_IMAGE_TAG   |latest   |Docker image tag   |

## Run

You must run the next command to use minimal `kafka-mirror` configuration

```
docker run --name kafka2citisim -e KAFKA_BROKER="10.0.150.70:9092" kafka-connector-citisim:latest
```

or use the docker compose file:

```
docker-compose up -d
```

Next, you can see the default configuration in `.env` file:

|Variable   |Default Value   |Description   |
|:-:|:-:|---|
|KAFKA_BROKER   |127.0.0.1:9092   |Kafka broker server  |

### Advanced custom configuration

If you wish to apply an advanced configuration you can run the next command

```
docker run --name kafka2citisim kafka-connector-citisim:latest ./kafka-mirror.py --help
```