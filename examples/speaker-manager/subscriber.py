#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import sys
from libcitisim import Broker


class LoudSpeakerManagerSubscriber:
    def run(self, args):
        config = 'subscriber.config'
        if len(args) > 1:
            config = args[1]

        broker = Broker(config)

        # - subscribe only to a specific publisher
        source = "FFFF735700000001"
        broker.subscribe_to_publisher(source, self)
        print("Subscribing to '" + source + "' publisher")

        # - subscribe to all publishers of a channel
        topic_name = "SpeakerMessages"
        broker.subscribe(topic_name, self)
        print("Subscribing to '" + topic_name + "' topic")

        print("Awaiting data...")
        broker.wait_for_events()

    def sayInPlace(self, place, message):
        print(f"- sayInPlace: {place}, message: {message}")

    def sayInSpeaker(self, speaker, message):
        print(f"- sayInSpeaker: {speaker}, message: {message}")


if __name__ == "__main__":
    LoudSpeakerManagerSubscriber().run(sys.argv)
