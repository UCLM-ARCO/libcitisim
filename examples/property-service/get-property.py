#!/usr/bin/python3
# -*- coding: utf-8; mode: python -*-

import sys
import libcitisim

if __name__ == "__main__":
    citisim_broker = libcitisim.Broker('libcitisim.config')
    
    full_path_property = '0A06175100007E57 | position'
    obtained_value = citisim_broker.get_property(full_path_property)

    print("Path: {}".format(full_path_property))
    print("Obtained value: {}".format(obtained_value))