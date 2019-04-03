#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import sys
from libcitisim import Broker

NOTIFY_MSG = '''
New notification:
  * data: {:.2f}
  * source: {}'''


class TemperatureSubscriber:
    def run(self, args):
        config = 'subscriber.config'
        if len(args) > 1:
            config = args[1]

        broker = Broker(config)

        # - subscribe only to a specific publisher
        source = "FFFF735700000002"
        broker.subscribe_to_publisher(source, self.event_printer)
        print("Subscribing to '" + source + "' publisher")

        # - subscribe to all publishers of a channel
        topic_name = "Temperature"
        broker.subscribe(topic_name, self.event_printer)
        print("Subscribing to '" + topic_name + "' topic")

        print("Awaiting data...")
        broker.wait_for_events()

    def event_printer(self, value, source, metadata):
        print(NOTIFY_MSG.format(value, source))

        for key in metadata:
            print("  * {}: {}".format(key, metadata[key]))


if __name__ == "__main__":
    TemperatureSubscriber().run(sys.argv)
