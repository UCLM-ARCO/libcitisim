#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import sys
from libcitisim import Broker
from libcitisim import KinectData


class PersonTrackerPublisher:
    def run(self, args):
        config = 'publisher.config'
        if len(args) > 1:
            config = args[1]

        broker = Broker(config)

        publisher = broker.get_publisher(
            source = "FFFF735700000001",
            transducer_type = "PersonTracker")

        points = [
            KinectData.KinectPoint(
                "trackid", "state", .0, .1, .2, .5, .6, .9, 12, 12345623
            )
        ]
        publisher.publish(points)
        print("Events published.")


if __name__ == "__main__":
    PersonTrackerPublisher().run(sys.argv)
