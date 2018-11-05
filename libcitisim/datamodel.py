#!/usr/bin/python3
# -*- coding:utf-8; mode:python -*-


class Cast:
    def __init__(self, type_, n=1, desc='', checker=None):
        self.type = type_
        self.checker = checker or (lambda x: True)

        if n > 1:
            self.type = list
            self.item_type = type_


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
