#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import sys
import time
from libcitisim import Broker


class TemperaturePublisher:
    def run(self, args):
        broker = Broker('publisher.config')
        publisher = broker.get_publisher(
            topic_name = "Temperature",
            source = "TestSensor")

        value = 16.5
        while True:
            try:
                publisher.publish(value)
                print("Published Temperature event: {}. C".format(value))
                time.sleep(10)
            except KeyboardInterrupt:
                break


if __name__ == "__main__":
    TemperaturePublisher().run(sys.argv)
