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

    def check(self, value):
        if not self.checker(value):
            raise TypeError("'{}' should be of type '{}'".format(value, self.type))

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


def check_enum(values):
    return lambda x: x in values

UNITS = [
    'wats', 'celsius', 'kWh', '%', 'ppm'
]

properties = {
    'units':              Cast(str, checker=check_enum(UNITS),
                               desc='units of the readings'),
                              
    'hw-range':           Cast(float, 2, desc='[min, max] allowed sensor values'),
    'orientation':        Cast(float, 3, desc='[x, y, z]'),
    'manufacturer':       Cast(str),
    'deployment-date':    Cast(str,      desc='physical deployment date: 2001-01-01'),  # FXIME: add checker
    'last-revision-date': Cast(str,      desc='maintenance last revision date: 2001-01-01'),  # FIXME: add checker
    'sw-version':         Cast(str,      desc='running software version'),
    'hw-version':         Cast(str,      desc='device hw version'),

    # TO REMOVE
    'position':           Cast(float, 3, desc='[longitude, latitude, altitude] (only if fixed)'),  # to geogash service
    'place':              Cast(str,      desc='place textual identifier'),  # to geogash service

    # NEW
    'interface':          Cast(str,      desc='Citisim SmartObject interface'),
    'asset':              Cast(str,      desc='icon or shape name (e: bulb)'),
    'magnitude':          Cast(str),  # enumerate
    'model':              Cast(str,      desc='Device model'),
    'delta':              Cast(int,      desc='Number of seconds between updates')
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
