#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import sys
import time
from libcitisim import Broker, Citizen


class CitizenReportPublisher:
    def run(self, args):
        config = 'publisher.config'
        if len(args) > 1:
            config = args[1]

        broker = Broker(config)

        publisher = broker.get_publisher(
            source = "FFFF735700000001",
            transducer_type = "CitizenReporter")

        value = Citizen.CitizenReport(
          "reportid",
            ["tag1", "tag2", "tag3"],
            "http://image.server.com/picture12352",
        )
        ReportProperties = {"latitude": 23.254466, "longitude": -1.2546855, "altitude": 735}
        publisher.publish(value, meta=ReportProperties)
        print("Published ReportEvent event, id: {}".format(value.reportid))



if __name__ == "__main__":
    CitizenReportPublisher().run(sys.argv)
