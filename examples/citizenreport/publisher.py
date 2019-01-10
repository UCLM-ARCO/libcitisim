#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import sys
import time
from libcitisim import Broker, Citizen


class CitizenReportPublisher:
    def run(self, args):
        broker = Broker('publisher.config')
        publisher = broker.get_publisher(
            topic_name = "CitizenReport",
            source = "citizenID@citisim.org")

        value = Citizen.CitizenReport(
          "reportid",
            ["tag1", "tag2", "tag3"],
            "http://image.server.com/picture12352",
        )
        ReportProperties = {"latitude": 23.254466, "longitude": -1.2546855, "altitude": 735}    
        publisher.publish(value, meta=ReportProperties)
        print("Published ReportEvent event: {}. C".format(value.reportid))
        


if __name__ == "__main__":
    CitizenReportPublisher().run(sys.argv)
