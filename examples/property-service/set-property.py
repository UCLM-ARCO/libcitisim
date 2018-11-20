#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import sys
import libcitisim

if __name__ == "__main__":
    citisim_broker = libcitisim.Broker('libcitisim.config')

    path = '0A06175100007E57'
    value = {'Units':'C', 'hwRange':[80.0, -40.0],
    'position':[38.997904, -3.919873, 639.10], 'manufacturer':"Libelium"}
    citisim_broker.set_property(path, value)

    print('Property set correctly.')