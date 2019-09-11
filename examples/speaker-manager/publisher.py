#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import sys
from libcitisim import Broker


class LoudSpeakerManagerPublisher:
    def run(self, args):
        config = 'publisher.config'
        if len(args) > 1:
            config = args[1]

        broker = Broker(config)

        publisher = broker.get_publisher(
            source = "FFFF735700000001",
            transducer_type = "SpeakerManager")

        publisher.sayInPlace("ITSI", "fire-alarm")
        publisher.sayInSpeaker("speaker-04", "emergency-evacuation")
        print("Events published.")


if __name__ == "__main__":
    LoudSpeakerManagerPublisher().run(sys.argv)
