#!/usr/bin/python3
# -*- coding:utf-8; mode:python -*-

import os
import sys
import Ice

PWD = os.path.dirname(__file__)
SLICE_DIR = os.path.join(PWD, "../../../slice")
if not os.path.exists(SLICE_DIR):
    if sys.platform == "win32":
        SLICE_DIR = os.path.join(Ice.getSliceDir(), "citisim")
    else:
        SLICE_DIR = "/usr/share/slice/citisim/"

Ice.loadSlice('{}/iot.ice --all'.format(SLICE_DIR))

import SmartObject

class Cast:
    def __init__(self, type_, n=1, desc='', checker=None):
        self.type = type_
        self.checker = checker or (lambda x: True)

        if n > 1:
            self.type = list
            self.item_type = type_

# FIXME: Consider using PropertyService for topic-type mapping
topic_types = {
    "ActivePower": SmartObject.AnalogSink,
    "AirPollutants1": SmartObject.AnalogSink,
    "AirPollutants2": SmartObject.AnalogSink,
    "Anemometer": SmartObject.AnalogSink,
    "Battery": SmartObject.AnalogSink,
    "CarbonDioxide": SmartObject.AnalogSink,
    "CarbonMonoxide": SmartObject.AnalogSink,
    "Dioxygen": SmartObject.AnalogSink,
    "Energy": SmartObject.AnalogSink,
    "HydrocarbonsVOC": SmartObject.AnalogSink,
    "Humidity": SmartObject.AnalogSink,
    "NitrogenDioxide": SmartObject.AnalogSink,
    "Ozone": SmartObject.AnalogSink,
    "ParticulateMatter1um": SmartObject.AnalogSink,
    "ParticulateMatter2.5um": SmartObject.AnalogSink,
    "ParticulateMatter10um": SmartObject.AnalogSink,
    "PluviometerCurrent": SmartObject.AnalogSink,
    "PluviometerLastDay": SmartObject.AnalogSink,
    "PluviometerLastHour": SmartObject.AnalogSink,
    "Power": SmartObject.AnalogSink,
    "Pressure": SmartObject.AnalogSink,
    "SoilMoisture": SmartObject.AnalogSink,
    "SoilTemperature": SmartObject.AnalogSink,
    "SolarRadiation": SmartObject.AnalogSink,
    "StemDiameter": SmartObject.AnalogSink,
    "Temperature": SmartObject.AnalogSink,
    "Vibration": SmartObject.AnalogSink,
    "WindVane": SmartObject.AnalogSink,

    "Unconfigured": SmartObject.AnalogSink,

    "Twilight": SmartObject.DigitalSink,
}

properties = {
    'units':              Cast(str,      desc='units of the readings'),
    'hw-range':           Cast(float, 2, desc='[min, max] allowed sensor values'),
    'position':           Cast(float, 3, desc='[longitude, latitude, altitude] (only if fixed)'),
    'orientation':        Cast(float, 3, desc='[x, y, z]'),
    'manufacturer':       Cast(str),
    'deployment-date':    Cast(str,      desc='physical deployment date: 2001-01-01'),  # FXIME: add checker
    'last-revision-date': Cast(str,      desc='maintenance last revision date: 2001-01-01'),  # FIXME: add checker
    'software-version':   Cast(str,      desc='running software version'),
    'hardware-version':   Cast(str,      desc='device hw version'),

    # NEW
    'asset':              Cast(str,      desc='icon or shape name (e: bulb)'),
}

metadata = {
    'timestamp':  Cast(int),
    'quality':    Cast(int, checker=lambda x: 0 <= x <= 256),
    'expiration': Cast(int, checker=lambda x: 0 <= x <= 2**15 - 1),
    'latitude':   Cast(float),
    'longitude':  Cast(float),
    'altitude':   Cast(float),
    'place':      Cast(str)
}
