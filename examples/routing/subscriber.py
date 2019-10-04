#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-
import sys
from libcitisim import Broker
from libcitisim import SmartServices

class RoutingSinkSubscriber:
    def run(self, args):
        config = 'subscriber.config'
        if len(args)> 1:
                config = args[1]

        broker = Broker(config)
        topic_name = "EvacuationRoute"
        broker.subscribe(topic_name, self.notify)
        print("Subscribing to '" + topic_name + "' topic")
        print("Awaiting data...")
        broker.wait_for_events()

    def notify(self, change, source):
        print(f"- new event: source: {source}, change: {change}")

if __name__ == "__main__":
    RoutingSinkSubscriber().run(sys.argv)

