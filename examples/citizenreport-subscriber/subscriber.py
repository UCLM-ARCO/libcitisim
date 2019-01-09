#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import sys
from libcitisim import Broker

NOTIFY_MSG = '''
New notification:
  * data: {:.2f}
  * source: {}'''


class CitizenReportSubscriber:
    def run(self, args):
        config = 'subscriber.config'
        if len(args) > 1:
            config = args[1]

        topic_name = "CitizenReport"
        broker = Broker(config)

        print("Subscribing to '" + topic_name + "' topic")
        broker.subscribe(topic_name, self.report_printer)

        print("Awaiting data...")
        broker.wait_for_events()

    def report_printer(self, value, source, metadata):
        print(NOTIFY_MSG.format(value, source))

        for key in metadata:
            print("  * {}: {}".format(key, metadata[key]))


if __name__ == "__main__":
    CitizenReportSubscriber().run(sys.argv)
