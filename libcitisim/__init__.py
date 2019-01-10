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
from .util import memoizedproperty

PWD = os.path.dirname(__file__)
# FIXME: SLICE_DIR = os.path.join(PWD, "../../../slice")
if True:  #if not os.path.exists(SLICE_DIR):
    if sys.platform == "win32":
        SLICE_DIR = Ice.getSliceDir()
    else:
        SLICE_DIR = "/usr/share/slice"

Ice.loadSlice('{}/citisim/services.ice --all'.format(SLICE_DIR))
Ice.loadSlice('{}/citisim/PersonTracker.ice --all'.format(SLICE_DIR))
Ice.loadSlice('-I{0} {0}/citisim/wiring.ice --all'.format(SLICE_DIR))
Ice.loadSlice('{}/PropertyService/PropertyService.ice --all'.format(SLICE_DIR))
Ice.loadSlice('{0}/citisim/citizen.ice -I{0} --all'.format(SLICE_DIR))

import PropertyService as PS
import json

import SmartObject  # noqa
import SmartServices  # noqa
from SmartObject import MetadataField  # noqa

# NOTE: expose this modules to users
import SmartEnvironment  # noqa
import KinectData  # noqa
from Citisim import Citizen  # noqa

logger = logging.getLogger('libcitisim')
logger.setLevel(logging.ERROR)
handler = logging.StreamHandler()
logger.addHandler(handler)
handler.setFormatter(logging.Formatter('[%(name)s]:%(levelname)s %(message)s'))

# Common Ice property names
WELCOME_SERVER_PROXY = "Welcome.Proxy"
TOPICMANAGER_PROXY = 'TopicManager.Proxy'
PROPERTY_SERVER_PROXY = 'PropertyService.Proxy'  # FIXME: should be "PropertyServer.Proxy"
WIRING_SERVER_PROXY = 'WiringServer.Proxy'

default_config = {
    TOPICMANAGER_PROXY:    'IceStorm/TopicManager',
    PROPERTY_SERVER_PROXY: 'PropertyServer',
    WELCOME_SERVER_PROXY:  'WelcomeServer',
    WIRING_SERVER_PROXY:   'WiringServer'
}

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

            setattr(self, key, cast.apply(value))
            del args[key]

        if args:
            raise KeyError(list(args.keys()))

    @classmethod
    def from_metadata(self, meta):
        fields = {}
        for key, value in meta.items():
            key = key.name.lower()
            cast = datamodel.metadata.get(key)
            if cast is None:
                logging.warn("Invalid metadata key: '{}'".format(key))
            else:
                fields[key] = cast.apply(value)
                
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
                "There were some error on provided callback '{}', do you "
                "provide the right signature?\n"
                "Expected signature: 'def callback(value, source, metadata)'".format(self._callback))


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


class ReportSinkI(Citizen.ReportSink, EventWithValueMixin):
    def __init__(self, topic_name, callback):
        self._topic_name = topic_name
        self._callback = callback

    def notify(self, value, source, meta, current):
        return self._notify(value, source, meta, current)


class NotifyPublisher:
    def __init__(self, broker, topic_name, source=None, meta={}):
        if source is None:
            source = uuid.uuid4().hex[:8]
        if meta is None:
            meta = {}

        self._broker = broker
        self._topic_name = topic_name
        self._source = source
        self._meta = meta
        self._type = datamodel.topic_types.get(topic_name)
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
        topic = self._broker.get_topic(self._topic_name)
        publisher = topic.getPublisher()
        cast = self._broker.proxy_types[self._type]
        self._publisher = cast.uncheckedCast(publisher)


class Broker:
    servant_types = {
        SmartObject.AnalogSink: AnalogSinkI,
        SmartObject.DigitalSink: DigitalSinkI,
        Citizen.ReportSink: ReportSinkI,
    }

    proxy_types = {
        SmartObject.AnalogSink: SmartObject.AnalogSinkPrx,
        SmartObject.DigitalSink: SmartObject.DigitalSinkPrx,
        Citizen.ReportSink: Citizen.ReportSinkPrx,
    }

    def __init__(self, arg, ic=None):
        self._ic = ic
        if ic is None:
            if isinstance(arg, str):
                self._ic = Ice.initialize([sys.argv[0], "--Ice.Config=" + arg])
            elif isinstance(arg, list):
                self._ic = Ice.initialize(arg)
            else:
                raise Exception("Broker argument should be filename (str) or command line (str list)")

        self.props = self._ic.getProperties()
        self._is_bidir = self.props.getProperty("LibCitisim.UseBiDir") == "True"

        # enable logging, if specified to do so
        if self.props.getProperty("LibCitisim.Debug") == "True":
            logger.setLevel(logging.DEBUG)
            logger.debug("debug mode active")

        self._set_default_properties()

    def __del__(self):
        if hasattr(self, '_adapter_created'):
            self.adapter.deactivate()
        self._ic.destroy()

    def _set_default_properties(self):
        for key, value in default_config.items():
            if not self.props.getProperty(key):
                logging.info("Setting default value for property '{}' = '{}'".format(key, value))
                self.props.setProperty(key, value)

    # FIXME: deprecated
    def create_adapter(self):
        logging.warning("Method create_adapter() is deprecated. User .adapter. property instead.")
        return self.adapter

    @memoizedproperty
    def adapter(self):
        if self._is_bidir:
            adapter_name = ""
            logger.info("using bi-dir connections")

        else:
            adapter_name = "Adapter"
            endpoints = self.props.getProperty("Adapter.Endpoints")
            if not endpoints:
                raise RuntimeError(
                    "You must provide the 'Adapter.Endpoints' configuration property.")

            logger.info("creating adapter with endpoints: '{}'".format(endpoints))

        adapter = self._ic.createObjectAdapter(adapter_name)
        adapter.activate()
        self._adapter_created = True

        return adapter

    # FIXME: not tested
    def adapter_add(self, servant, identity)    :
        if not isinstance(identity, Ice.Identity):
            identity = self._ic.stringToIdentity(normalize_addr(identity))

        return self.adapter.add(servant, identity)

    # FIXME: not tested
    @memoizedproperty
    def welcome_server(self):
        proxy = self._ic.propertyToProxy(WELCOME_SERVER_PROXY)
        if proxy is None:
            raise RuntimeError(
                "You must provide the '{}' configuration property.".format(WELCOME_SERVER_PROXY))

        return SmartObject.WelcomeServicePrx.uncheckedCast(proxy.ice_oneway())

    # FIXME: not tested
    @memoizedproperty
    def wiring_server(self):
        proxy = self._ic.propertyToProxy(WIRING_SERVER_PROXY)
        if proxy is None:
            raise RuntimeError(
                "You must provide the '{}' configuration property.".format(WIRING_SERVER_PROXY))

        return SmartServices.WiringServicePrx.checkedCast(proxy)

    # FIXME: not tested
    def hello(self, address):
        self.welcome_server.hello(address)

    def subscribe(self, topic_name, callback):
        proxy = self._get_servant_proxy(topic_name, callback)
        topic = self.get_topic(topic_name)

        # support for bidir connections
        if self._is_bidir:
            topic.ice_getConnection().setAdapter(self.adapter)

        topic.subscribeAndGetPublisher({}, proxy)

    def publish(self, topic_name, value, source=None, meta={}):
        p = NotifyPublisher(self, topic_name, source, meta)
        p.publish(value)

    def get_publisher(self, topic_name, source=None, meta={}):
        return NotifyPublisher(self, topic_name, source, meta)

    # FIXME: not tested
    def wait_for_events(self):
        try:
            self._ic.waitForShutdown()
        except KeyboardInterrupt:
            pass

    def _get_servant_proxy(self, topic_name, callback):
        type_ = datamodel.topic_types.get(topic_name)
        if type_ is None:
            raise ValueError("Unknown topic name: {}".format(topic_name))

        servant = self.servant_types[type_](topic_name, callback)
        proxy = self.adapter.addWithUUID(servant)
        if proxy.ice_isTwoway():
            proxy = proxy.ice_oneway()
        return proxy

    def get_topic(self, name):
        manager = self.topic_manager
        try:
            return manager.retrieve(name)
        except IceStorm.NoSuchTopic:
            return manager.create(name)

    @memoizedproperty
    def topic_manager(self):
        proxy = self._ic.propertyToProxy(TOPICMANAGER_PROXY)
        if proxy is None:
            raise ValueError(
                "You must provide the '{}' configuration property.".format(TOPICMANAGER_PROXY))

        return IceStorm.TopicManagerPrx.checkedCast(proxy)

    def set_property(self, path, value):
        serialized_value = json.dumps(value)
        manager = self._get_property_manager()
        manager.set(path, serialized_value)

    def get_property(self, path):
        manager = self._get_property_manager()
        return manager.get(path)

    def _get_property_manager(self):
        if not hasattr(self, "_property_manager"):
            manager = self._ic.propertyToProxy(PROPERTY_SERVER_PROXY)
            if manager is None:
                raise ValueError(
                    "Missing configuration property: {}".format(PROPERTY_SERVER_PROXY))

            self._property_manager = PS.PropertyServerPrx.checkedCast(manager)
        return self._property_manager


def normalize_addr(address):
    return address.replace(':', '')
