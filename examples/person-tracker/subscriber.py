#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import sys
from libcitisim import Broker


class PersonTrackerSubscriber:
    def run(self, args):
        config = 'subscriber.config'
        if len(args) > 1:
            config = args[1]

        broker = Broker(config)

        # - subscribe only to a specific publisher
        source = "FFFF735700000001"
        broker.subscribe_to_publisher(source, self.notify)
        print("Subscribing to '" + source + "' publisher")

        # - subscribe to all publishers of a channel
        topic_name = "PersonTracking"
        broker.subscribe(topic_name, self.notify)
        print("Subscribing to '" + topic_name + "' topic")

        print("Awaiting data...")
        broker.wait_for_events()

    def notify(self, points, source):
        print(f"- new event: source: {source}, points: {points}")



if __name__ == "__main__":
    PersonTrackerSubscriber().run(sys.argv)
