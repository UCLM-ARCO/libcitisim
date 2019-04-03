#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import sys
import time
from libcitisim import Broker


class TemperaturePublisher:
    def run(self, args):
        broker = Broker('publisher.config')

        publisher = broker.get_publisher(
            source = "FFFF735700000002",
            transducer_type = "TemperatureSensor"
        )

        value = 16.5
        publisher.publish(value)
        print("Published Temperature event: {} C".format(value))


if __name__ == "__main__":
    TemperaturePublisher().run(sys.argv)
