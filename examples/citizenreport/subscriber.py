#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import sys
from libcitisim import Broker

NOTIFY_MSG = '''
New notification:
  * data: {}
  * source: {}'''


class CitizenReportSubscriber:
    def run(self, args):
        config = 'subscriber.config'
        if len(args) > 1:
            config = args[1]

        broker = Broker(config)

        # - subscribe only to a specific publisher
        source = "FFFF735700000001"
        broker.subscribe_to_publisher(source, self.report_printer)
        print("Subscribing to '" + source + "' publisher")

        # - subscribe to all publishers of a channel
        topic_name = "CitizenReport"
        broker.subscribe(topic_name, self.report_printer)
        print("Subscribing to '" + topic_name + "' topic")

        print("Awaiting data...")
        broker.wait_for_events()

    def report_printer(self, value, source, metadata):
        print(NOTIFY_MSG.format(value, source))

        for key in metadata:
            print("  * {}: {}".format(key, metadata[key]))


if __name__ == "__main__":
    CitizenReportSubscriber().run(sys.argv)
