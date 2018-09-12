# -*- coding: utf-8; mode: python -*-

import os
import sys
import uuid
import logging
from time import time
import Ice
import IceStorm
from ipaddress import ip_address

from . import datamodel

PWD = os.path.dirname(__file__)
SLICE_DIR = os.path.join(PWD, "../../../slice")
if not os.path.exists(SLICE_DIR):
    if sys.platform == "win32":
        SLICE_DIR = os.path.join(Ice.getSliceDir(), "citisim")
    else:
        SLICE_DIR = "/usr/share/slice/citisim/"

Ice.loadSlice('{}/iot.ice --all'.format(SLICE_DIR))
Ice.loadSlice('{}/services.ice --all'.format(SLICE_DIR))
Ice.loadSlice('{}/PersonTracker.ice --all'.format(SLICE_DIR))

#FIXME Load slice in the same way as the previous ones
ps_slice_path = "/usr/share/slice/PropertyService/PropertyService.ice"
Ice.loadSlice(ps_slice_path)
import PropertyService as PS
import json

import SmartObject  # noqa
from SmartObject import MetadataField  # noqa

# NOTE: expose this modules to users
import SmartEnvironment  # noqa
import KinectData  # noqa

logger = logging.getLogger('libcitisim')
logger.setLevel(logging.ERROR)
handler = logging.StreamHandler()
logger.addHandler(handler)
handler.setFormatter(logging.Formatter('[%(name)s]:%(levelname)s %(message)s'))


class Cast:
    def __init__(self, type_, check=None):
        self.type = type_
        self.check = check or (lambda x: True)


class MetadataHelper:
    name_to_field = {
        'timestamp':  MetadataField.Timestamp,
        'quality':    MetadataField.Quality,
        'expiration': MetadataField.Expiration,
        'latitude':   MetadataField.Latitude,
        'longitude':  MetadataField.Longitude,
        'altitude':   MetadataField.Altitude,
        'place':      MetadataField.Place,
    }

    def __init__(self, **kargs):
        args = kargs.copy()

        for key, cast in datamodel.metadata.items():
            value = args.get(key)
            if value is None:
                continue

            if not cast.check(value):
                raise TypeError(key)

            setattr(self, key, cast.type(value))
            del args[key]

        if args:
            raise KeyError(list(args.keys()))

    @classmethod
    def from_metadata(self, meta):
        fields = {}
        for key, value in meta.items():
            key = key.name.lower()
            cast = datamodel.metadata.get(key)
            fields[key] = cast.type(value)
        return MetadataHelper(**fields)

    def get(self, key):
        return getattr(self, key)

    def to_string_dict(self):
        retval = self.to_dict()
        return {k.name.lower(): v for k, v in retval.items()}

    def to_dict(self):
        retval = {}

        for key in datamodel.metadata.keys():
            value = getattr(self, key, None)
            if value is not None:
                retval[self.name_to_field[key]] = str(value)

        return retval


def remove_private_endpoints(proxy):
    def is_private(endpoint):
        if sys.version_info.major is 3:
            return ip_address(endpoint.getInfo().host).is_private
        return ip_address(str(endpoint.getInfo().host)).is_private

    endpoints = [e for e in proxy.ice_getEndpoints() if not is_private(e)]
    return proxy.ice_endpoints(endpoints)


class ObservableMixin:
    observer_cast = None

    def __init__(self):
        assert self.observer_cast is not None, \
            "observer_cast class attribute should be defined"
        self.observer = None

    def setObserver(self, observer, current=None):
        ic = current.adapter.getCommunicator()
        proxy = ic.stringToProxy(observer)
        self.observer = self.observer_cast.uncheckedCast(proxy)
        logger.info("new observer {} for {}".format(observer, current.id.name))


# FIXME: Consider using PropertyService for topic-type mapping
topic_types = {
    "Anemometer": SmartObject.AnalogSink,
    "Battery": SmartObject.AnalogSink,
    "CarbonDioxide": SmartObject.AnalogSink,
    "CarbonMonoxide": SmartObject.AnalogSink,
    "Dioxygen": SmartObject.AnalogSink,
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


class EventWithValueMixin:
    def _notify(self, value, source, meta, current):
        try:
            meta = MetadataHelper.from_metadata(meta).to_string_dict()
            logger.debug(
                "event arrived on '{}', value: {}, source: {}, meta: {}"
                .format(self._topic_name, value, source, meta)
            )
            self._callback(value, source, meta)

        except TypeError as e:
            logger.error(e)
            logger.error(
                "There were some error on provided callback, do you "
                "provide the right signature?\n"
                "Expected signature: 'def callback(value, source, metadata)'")


class AnalogSinkI(SmartObject.AnalogSink, EventWithValueMixin):
    def __init__(self, topic_name, callback):
        self._topic_name = topic_name
        self._callback = callback

    def notify(self, value, source, meta, current):
        return self._notify(value, source, meta, current)


class DigitalSinkI(SmartObject.DigitalSink, EventWithValueMixin):
    def __init__(self, topic_name, callback):
        self._topic_name = topic_name
        self._callback = callback

    def notify(self, value, source, meta, current):
        return self._notify(value, source, meta, current)


class ADPublisher:
    def __init__(self, broker, topic_name, source=None, meta={}):
        if source is None:
            source = uuid.uuid4().hex[:8]
        if meta is None:
            meta = {}

        self._broker = broker
        self._topic_name = topic_name
        self._source = source
        self._meta = meta
        self._type = topic_types.get(topic_name)
        self._publisher = None

        if self._type is None:
            raise ValueError("Unknown topic name: {}".format(topic_name))

    def publish(self, value, source=None, meta=None):
        if self._publisher is None:
            self._retrieve_publisher()

        if source is None:
            source = self._source
        if meta is None:
            meta = self._meta

        # if there is "timestamp" but explicitly set to None, then
        # remove ts from meta, otherwise (there is no "timestamp" key
        # in meta), set it as now
        if "timestamp" not in meta:
            meta["timestamp"] = int(time())
        else:
            if meta.get("timestamp") is None:
                meta.pop("timestamp")

        meta = MetadataHelper(**meta).to_dict()
        self._publisher.notify(value, source, meta)
        logger.debug(
            "publish event on '{}', value: {}, source: {}, meta: {}"
            .format(self._topic_name, value, source, meta)
        )

    def _retrieve_publisher(self):
        topic = self._broker._get_topic(self._topic_name)
        publisher = topic.getPublisher()
        cast = self._broker.proxy_types[self._type]
        self._publisher = cast.uncheckedCast(publisher)


class Broker:
    servant_types = {
        SmartObject.AnalogSink: AnalogSinkI,
        SmartObject.DigitalSink: DigitalSinkI,
    }

    proxy_types = {
        SmartObject.AnalogSink: SmartObject.AnalogSinkPrx,
        SmartObject.DigitalSink: SmartObject.DigitalSinkPrx,
    }

    def __init__(self, config, ic=None):
        self._ic = ic
        if ic is None:
            self._ic = Ice.initialize([sys.argv[0], "--Ice.Config=" + config])
        self._adapter = None

        props = self._ic.getProperties()
        self._is_bidir = props.getProperty("LibCitisim.UseBiDir") == "True"

        # enable logging, if specified to do so
        if props.getProperty("LibCitisim.Debug") == "True":
            logger.setLevel(logging.DEBUG)
            logger.debug("debug mode active")

        # support for bidir communications
        if self._is_bidir:
            self._adapter = self._ic.createObjectAdapter("")
            self._adapter.activate()
            logger.info("using bi-dir connections")

        # normal adapter creation
        elif props.getProperty("Adapter.Endpoints"):
            self._adapter = self._ic.createObjectAdapter("Adapter")
            self._adapter.activate()
            eps = props.getProperty("Adapter.Endpoints")
            logger.info("adapter created with endpoints '{}'".format(eps))

    def __del__(self):
        if self._adapter is not None:
            self._adapter.deactivate()
        self._ic.destroy()

    def subscribe(self, topic_name, callback):
        if self._adapter is None:
            raise RuntimeError(
                "In order to subscribe an object, you need to provide "
                "the 'Adapter.Endpoints' configuration property.")

        proxy = self._get_servant_proxy(topic_name, callback)
        topic = self._get_topic(topic_name)

        # support for bidir connections
        if self._is_bidir:
            topic.ice_getConnection().setAdapter(self._adapter)

        topic.subscribeAndGetPublisher({}, proxy)

    def publish(self, topic_name, value, source=None, meta={}):
        p = ADPublisher(self, topic_name, source, meta)
        p.publish(value)

    def get_publisher(self, topic_name, source=None, meta={}):
        return ADPublisher(self, topic_name, source, meta)

    def wait_for_events(self):
        try:
            self._ic.waitForShutdown()
        except KeyboardInterrupt:
            pass

    def _get_servant_proxy(self, topic_name, callback):
        type_ = topic_types.get(topic_name)
        if type_ is None:
            raise ValueError("Unknown topic name: {}".format(topic_name))

        servant = self.servant_types[type_](topic_name, callback)
        proxy = self._adapter.addWithUUID(servant)
        if proxy.ice_isTwoway():
            proxy = proxy.ice_oneway()
        return proxy

    def _get_topic(self, name):
        manager = self._get_topic_manager()
        try:
            return manager.retrieve(name)
        except IceStorm.NoSuchTopic:
            return manager.create(name)

    def _get_topic_manager(self):
        if not hasattr(self, "_topic_manager"):
            manager = self._ic.propertyToProxy("TopicManager.Proxy")
            if manager is None:
                raise ValueError(
                    "Missing configuration property: TopicManager.Proxy")

            self._topic_manager = IceStorm.TopicManagerPrx.checkedCast(manager)
        return self._topic_manager

    def set_property(self, path, value):
        serializedValue = json.dumps(value)
        manager = self._get_property_manager()
        manager.set(path, serializedValue)

    def get_property(self, path):
        manager = self._get_property_manager()
        return manager.get(path)

    def _get_property_manager(self):
        if not hasattr(self, "_property_manager"):
            manager = self._ic.propertyToProxy("PropertyService.Proxy")
            if manager is None:
                raise ValueError(
                    "Missing configuration property: TopicManager.Proxy")

            self._property_manager = PS.PropertyServerPrx.checkedCast(manager)
            return self._property_manager
