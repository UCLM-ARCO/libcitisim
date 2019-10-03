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
        SLICE_DIR = "/usr/share/slice/citisim"

Ice.loadSlice('{}/iot.ice --all'.format(SLICE_DIR))
Ice.loadSlice('{}/citizen.ice -I{} --all'.format(SLICE_DIR, os.path.join(SLICE_DIR, "..")))
Ice.loadSlice('{}/services.ice -I{} --all'.format(SLICE_DIR, os.path.join(SLICE_DIR, "..")))
Ice.loadSlice('{}/infosystem.ice -I{} --all'.format(SLICE_DIR, os.path.join(SLICE_DIR, "..")))
Ice.loadSlice('{}/PersonTracker.ice --all'.format(SLICE_DIR))

import SmartObject
import SmartServices
import SmartEnvironment
import KinectData
from citisim import infosystem
from Citisim import Citizen


def bool_cast(value):
    false_values = [0, False, 'False', 'false']
    true_values = [1, True, 'True', 'true']

    if value in false_values:
        return False
    if value in true_values:
        return True

    raise TypeError("a valid boolean value: {}".format(false_values + true_values))


def valid_enum(values):
    def caster(x):
        if x in values:
            return x
        raise TypeError(values)

    return caster


def int_range(min_, max_):
    def caster(value):
        try:
            retval = int(value)
        except ValueError:
            raise TypeError("invalid value for int: {}".format(value))

        if not min_ <= retval <= max_:
            raise TypeError("range [{}, {}]".format(min_, max_))

        return retval

    return caster


type_casters = {
    bool: bool_cast,
}


class TypeCast:
    def __init__(self, caster=str, n=1, desc=''):
        self.caster = type_casters.get(caster, caster)
        self.len = n

    def apply(self, value):
        if self.len > 1:
            return list(self.apply_list(value))

        return self.apply_item(value)

    def apply_item(self, value):
        try:
            return self.caster(value)
        except TypeError as e:
            raise TypeError("'{}' should match '{}'".format(value, e))

    def apply_list(self, value):
        if len(value) != self.len:
            raise TypeError("value len is {}, but it should be {}".format(
                len(value), self.len))

        for i in range(self.len):
            yield self.apply_item(value[i])


topic_types = {
    "ActivePower": SmartObject.AnalogSink,
    "AirPollutants1": SmartObject.AnalogSink,
    "AirPollutants2": SmartObject.AnalogSink,
    "ApparentPower": SmartObject.AnalogSink,
    "Anemometer": SmartObject.AnalogSink,
    "Battery": SmartObject.AnalogSink,
    "CarbonDioxide": SmartObject.AnalogSink,
    "CarbonMonoxide": SmartObject.AnalogSink,
    "Current": SmartObject.AnalogSink,
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
    "PowerFactor": SmartObject.AnalogSink,
    "Pressure": SmartObject.AnalogSink,
    "SoilMoisture": SmartObject.AnalogSink,
    "SoilTemperature": SmartObject.AnalogSink,
    "SolarRadiation": SmartObject.AnalogSink,
    "StemDiameter": SmartObject.AnalogSink,
    "Temperature": SmartObject.AnalogSink,
    "Vibration": SmartObject.AnalogSink,
    "Voltage": SmartObject.AnalogSink,
    "WindVane": SmartObject.AnalogSink,

    "Unconfigured": SmartObject.AnalogSink,

    "DoorState": SmartObject.DigitalSink,
    "Twilight": SmartObject.DigitalSink,

    "CitizenReport": Citizen.ReportSink,
    "EvacuationRoute": SmartServices.RoutingSink,
    "SpeakerMessages": infosystem.LoudSpeakerManager,
    "Alarm": SmartObject.EventSink,
    "PersonTracking": KinectData.PersonTracker,
    "OccupancyChanges": SmartEnvironment.OccupancyMonitor,
}


transducer_types = {
    'LightSensor': SmartObject.AnalogSink,
    'TemperatureSensor': SmartObject.AnalogSink,
    'HumiditySensor': SmartObject.AnalogSink,
    'PressureSensor': SmartObject.AnalogSink,
    'Anemometer': SmartObject.AnalogSink,
    'Windvane': SmartObject.AnalogSink,
    'Pluviometer': SmartObject.AnalogSink,
    'VibrationSensor': SmartObject.AnalogSink,
    'VoltageSensor': SmartObject.AnalogSink,
    'CurrentSensor': SmartObject.AnalogSink,
    'PowerSensor': SmartObject.AnalogSink,
    'CapacitySensor': SmartObject.AnalogSink,
    'EnergySensor': SmartObject.AnalogSink,
    'ParticulateMatterSensor': SmartObject.AnalogSink,
    'GasSensor': SmartObject.AnalogSink,
    'VolumeSensor': SmartObject.AnalogSink,
    'RadiationSensor': SmartObject.AnalogSink,
    'MotorActuator': SmartObject.AnalogSink,
    'DimmableLightActuator': SmartObject.AnalogSink,
    'Accelerometer': SmartObject.AnalogSink,
    'PositionSensor': SmartObject.AnalogSink,
    'AngleSensor': SmartObject.AnalogSink,

    'TwilightSensor': SmartObject.DigitalSink,
    'DoorSensor': SmartObject.DigitalSink,
    'PIRSensor': SmartObject.DigitalSink,
    'FluxSensor': SmartObject.DigitalSink,
    'RelayActuator': SmartObject.DigitalSink,
    'ValveActuator': SmartObject.DigitalSink,
    'SwitchActuator': SmartObject.DigitalSink,

    'CitizenReporter': Citizen.ReportSink,

    'RouteService': SmartServices.RoutingSink,

    'SmartScreen': SmartServices.MessageRender,
    'Speaker': SmartServices.MessageRender,
    'SpeakerManager': infosystem.LoudSpeakerManager,
    'AlarmNotifier': SmartObject.EventSink,
    'PersonTracker': KinectData.PersonTracker,
    'OccupancyReporter': SmartEnvironment.OccupancyMonitor,
}


UNITS = [
    'watts',         # energy
    'kWh',           # energy
    'volts',         # voltage
    'amperes',       # current
    'volt-amperes',  # apparent power
    'mAh',           # battery capacity
    'celsius',       # temperature
    'degrees',       # angle
    '%',             # percentage
    '%RH',           # relative humidity
    'ppm',           # parts per million
    'mm',            # distance, width, length...
    'mm/hour',       # volume, speed
    'mm/day',        # volume, speed
    'km/h',          # speed
    'bool',          # presence, ausence, binary properties
]


MAGNITUDES = [
    'electrical-power',
    'temperature',
    'humidity',
    'level',
]


properties = {
    'units':              TypeCast(valid_enum(UNITS), desc='units of the readings'),
    'hw-range':           TypeCast(float, 2, desc='[min, max] allowed sensor values'),
    'orientation':        TypeCast(float, 3, desc='[x, y, z]'),
    'manufacturer':       TypeCast(),
    'deployment-date':    TypeCast(desc='physical deployment date: 2001-01-01'),  # FXIME: add checker
    'last-revision-date': TypeCast(desc='maintenance last revision date: 2001-01-01'),  # FIXME: add checker
    'sw-version':         TypeCast(desc='running software version'),
    'hw-version':         TypeCast(desc='device hw version'),

    # TO REMOVE
    # 'position':           TypeCast(float, 3, desc='[longitude, latitude, altitude] (only if fixed)'),  # to location service
    # 'place':              TypeCast(desc='place textual identifier'),  # to location service

    # NEW
    'proxy':              TypeCast(desc='transducer object stringfied proxy'),
    'interface':          TypeCast(desc='citisim SmartObject interface'),
    'asset':              TypeCast(desc='icon or shape name (e: bulb)'),
    'magnitude':          TypeCast(valid_enum(MAGNITUDES), desc='physical magnitude'),
    'model':              TypeCast(desc='device model'),
    'delta':              TypeCast(int,  desc='number of seconds between updates'),
    'common-channel':     TypeCast(desc='common public topic name where event will be sent'),

    # FIXME: not needed due to Welcome, nobody need to invoke tranducer.setObserver anymore.
    'observable':         TypeCast(bool, desc='True if a publisher implements SmartObject::Observable'),
    'derive-from':        TypeCast(desc='Physical sensor identity for a virtual sensor'),

    # 'wiring:observers':   TypeCast(list, desc='List of observers for an observable (managed by the wiring service')
}


metadata = {
    'timestamp':     TypeCast(int),
    'quality':       TypeCast(int_range(0, 256)),
    'expiration':    TypeCast(int_range(0, 2**15 - 1), desc='validity for the sent value (in seconds)'),
    'latitude':      TypeCast(float),
    'longitude':     TypeCast(float),
    'altitude':      TypeCast(float),
    'place':         TypeCast(desc='Standard placeID'),
    'category':      TypeCast(desc='Tags or categories'),
    'citizenemail':  TypeCast(desc='Citizen Report user identifier'),
}
