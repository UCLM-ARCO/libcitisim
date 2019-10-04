#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-
import sys
from libcitisim import Broker
from libcitisim import SmartServices
class RoutingSinkPublisher:
    def run(self, args):
        config = 'publisher.config'
        if len(args)> 1:
                config = args[1]

        broker = Broker(config)
        
        value = ["CELL1","CELL2","CELL3"]
        source = "0011223344556687"
        topic_name = "EvacuationRoute"
        transducer_type = "RouteService"

        p = broker.get_publisher(source, transducer_type)
        p.publish(value)
        print("Sending an event to '" + topic_name + "' topic")


if __name__ == "__main__":
    RoutingSinkPublisher().run(sys.argv)

