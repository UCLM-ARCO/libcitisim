# -*- coding: utf-8; mode: python -*-

import sys
import logging
import Ice
import IceStorm
import json
from ipaddress import ip_address
from time import time

from . import datamodel
from .util import memoizedproperty

if sys.platform == "win32":
    SLICE_DIR = Ice.getSliceDir()
else:
    SLICE_DIR = "/usr/share/slice"

Ice.loadSlice('{}/citisim/services.ice --all'.format(SLICE_DIR))
Ice.loadSlice('{}/citisim/PersonTracker.ice --all'.format(SLICE_DIR))
Ice.loadSlice('-I{0} {0}/citisim/wiring.ice --all'.format(SLICE_DIR))
Ice.loadSlice('{}/PropertyService/PropertyService.ice --all'.format(SLICE_DIR))
Ice.loadSlice('{0}/citisim/citizen.ice -I{0} --all'.format(SLICE_DIR))
Ice.loadSlice('{}/citisim/energy.ice'.format(SLICE_DIR))
Ice.loadSlice('{}/citisim/infosystem.ice'.format(SLICE_DIR))

import PropertyService as PS
import SmartObject  # noqa
import SmartServices  # noqa
from SmartObject import MetadataField  # noqa

# NOTE: expose this modules to users
import SmartEnvironment  # noqa
import KinectData  # noqa
from Citisim import Citizen  # noqa
from citisim.energy import EnergyForecastPrx
from citisim import infosystem

logger = logging.getLogger('libcitisim')
logger.setLevel(logging.ERROR)
logger.propagate = False
handler = logging.StreamHandler()
logger.addHandler(handler)
handler.setFormatter(logging.Formatter('[%(name)s]:%(levelname)s %(message)s'))

# Common Ice property names
WELCOME_SERVER_PROXY = "WelcomeServer.Proxy"
TOPICMANAGER_PROXY = 'TopicManager.Proxy'
PROPERTY_SERVER_PROXY = 'PropertyServer.Proxy'
WIRING_SERVER_PROXY = 'WiringServer.Proxy'
ENERGY_MODEL_SERVER_PROXY = "EnergyModelServer.Proxy"

default_config = {
    TOPICMANAGER_PROXY:        'IceStorm/TopicManager',
    PROPERTY_SERVER_PROXY:     'PropertyServer',
    WELCOME_SERVER_PROXY:      'WelcomeServer',
    WIRING_SERVER_PROXY:       'WiringServer',
    ENERGY_MODEL_SERVER_PROXY: 'EnergyModel',
}


class MetadataHelper:
    name_to_field = {
        'timestamp':     MetadataField.Timestamp,
        'quality':       MetadataField.Quality,
        'expiration':    MetadataField.Expiration,
        'latitude':      MetadataField.Latitude,
        'longitude':     MetadataField.Longitude,
        'altitude':      MetadataField.Altitude,
        'place':         MetadataField.Place,
        'category':      MetadataField.Category,
        'citizenemail':  MetadataField.CitizenEmail,
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
            if not isinstance(key, MetadataField):
                logger.warn(
                    "Invalid metadata key: '{}'. MetadataField type required.".format(key))
                continue

            key = key.name.lower()
            cast = datamodel.metadata.get(key)
            if cast is None:
                logger.warn("Invalid metadata key: '{}'".format(key))
                continue

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


class ObservableMixin:
    observer_cast = None

    def __init__(self):
        assert self.observer_cast is not None, \
            "observer_cast class attribute should be defined"
        self.observer = None

    def setObserver(self, observer, current):
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


class RoutingSinkI(SmartServices.RoutingSink):
    def __init__(self, topic_name, callback):
        self._topic_name = topic_name
        self._callback = callback

    def notify(self, value, current):
        try:
            logger.debug(
                "event arrived on '{}', value: {}".format(self._topic_name, value)
            )
            self._callback(value)

        except TypeError as e:
            logger.error(e)
            logger.error(
                "There were some error on provided callback '{}', do you "
                "provide the right signature?\n"
                "Expected signature: 'def callback(value)'".format(self._callback))


class LoudSpeakerManagerI(infosystem.LoudSpeakerManager):
    def __init__(self, topic_name, callback):
        self._topic_name = topic_name
        self._callback = callback

    def sayInPlace(self, placeid, message, current):
        try:
            self._callback.sayInPlace(placeid, message)
        except (AttributeError, TypeError) as e:
            logger.error(e)
            logger.error(
                "There were some error on provided callback object '{}', "
                "do you implement the expected methods?\n"
                "- method signature: 'def sayInPlace(self, place, message)'"
                .format(self._callback)
            )

    def sayInSpeaker(self, speakerid, message, current):
        try:
            self._callback.sayInSpeaker(speakerid, message)
        except (AttributeError, TypeError) as e:
            logger.error(e)
            logger.error(
                "There were some error on provided callback object '{}', "
                "do you implement the expected methods?\n"
                "- method signature: 'def sayInSpeaker(self, speaker, message)'"
                .format(self._callback)
            )


class ObservablePublisher(SmartObject.Observable, ObservableMixin):
    proxy_types = {
        SmartObject.AnalogSink: SmartObject.AnalogSinkPrx,
        SmartObject.DigitalSink: SmartObject.DigitalSinkPrx,
        Citizen.ReportSink: Citizen.ReportSinkPrx,
        SmartServices.RoutingSink: SmartServices.RoutingSinkPrx,
        # infosystem.LoudSpeakerManager: infosystem.LoudSpeakerManagerPrx,
    }

    def __init__(self, broker, source, transducer_type, meta):
        try:
            self.observer_cast = self.proxy_types[
                datamodel.transducer_types[transducer_type]
            ]
        except KeyError:
            raise TypeError("Unknown transducer type: {}".format(transducer_type))

        ObservableMixin.__init__(self)

        assert source is not None, "Invalid provided source"
        source = source.strip()
        assert source != "", "Invalid provided source"

        if meta is None:
            meta = {}

        self.broker = broker
        self.source = source
        self.meta = meta

    def setObserver(self, observer, current):
        ObservableMixin.setObserver(self, observer, current)

    def publish(self, value, meta=None):
        if self.observer is None:
            raise ValueError("Publisher not yet configured!")

        if meta is None:
            meta = self.meta

        # if there is "timestamp" but explicitly set to None, then
        # remove ts from meta, otherwise (there is no "timestamp" key
        # in meta), set it as now
        if "timestamp" not in meta:
            meta["timestamp"] = int(time())
        elif meta.get("timestamp") is None:
            meta.pop("timestamp")

        meta = MetadataHelper(**meta).to_dict()
        if self.observer_cast == SmartServices.RoutingSinkPrx:
            self.observer.notify(value)
            logger.debug(
                "publish event to '{}', value: {}".format(self.observer, value)
            )
        else:
            self.observer.notify(value, self.source, meta)
            logger.debug(
                "publish event to '{}', value: {}, source: {}, meta: {}"
                .format(self.observer, value, self.source, meta)
            )

    def subscribe(self, observer):
        prop_key = self.source + " | private-channel"
        channel_name = self.broker.get_property(prop_key)
        topic = self.broker.get_topic(channel_name)
        topic.subscribeAndGetPublisher({}, observer)


class ObservableInfosystemPublisher(SmartObject.Observable, ObservableMixin):
    proxy_types = {
        infosystem.LoudSpeakerManager: infosystem.LoudSpeakerManagerPrx,
    }

    def __init__(self, broker, source, transducer_type):
        try:
            self.observer_cast = self.proxy_types[
                datamodel.transducer_types[transducer_type]
            ]
        except KeyError:
            raise TypeError("Unknown transducer type: {}".format(transducer_type))

        ObservableMixin.__init__(self)

        assert source is not None, "Invalid provided source"
        source = source.strip()
        assert source != "", "Invalid provided source"

        self.broker = broker
        self.source = source

    def setObserver(self, observer, current):
        ObservableMixin.setObserver(self, observer, current)

    def sayInPlace(self, place, message):
        if self.observer is None:
            raise ValueError("Publisher not yet configured!")

        self.observer.sayInPlace(place, message)
        logger.debug(
            "publish event sayInPlace() to '{}', place: {}, message: {}"
            .format(self.observer, place, message)
        )

    def sayInSpeaker(self, speaker, message):
        if self.observer is None:
            raise ValueError("Publisher not yet configured!")

        self.observer.sayInSpeaker(speaker, message)
        logger.debug(
            "publish event sayInSpeaker() to '{}', speaker: {}, message: {}"
            .format(self.observer, speaker, message)
        )

    def subscribe(self, observer):
        prop_key = self.source + " | private-channel"
        channel_name = self.broker.get_property(prop_key)
        topic = self.broker.get_topic(channel_name)
        topic.subscribeAndGetPublisher({}, observer)


class Broker:
    servant_types = {
        SmartObject.AnalogSink: AnalogSinkI,
        SmartObject.DigitalSink: DigitalSinkI,
        Citizen.ReportSink: ReportSinkI,
        SmartServices.RoutingSink: RoutingSinkI,
        infosystem.LoudSpeakerManager: LoudSpeakerManagerI,
    }

    def __init__(self, arg=None, ic=None):
        self._ic = ic
        if ic is None:
            if isinstance(arg, str):
                self._ic = Ice.initialize([sys.argv[0], "--Ice.Config=" + arg])
            elif isinstance(arg, list):
                self._ic = Ice.initialize(arg)
            else:
                raise Exception(
                    "Broker argument should be filename (str) or command line (str list)")

        self.props = self._ic.getProperties()
        self.is_bidir = self.props.getProperty("LibCitisim.UseBiDir") == "True"

        # enable logging, if specified to do so
        if self.props.getProperty("LibCitisim.Debug") == "True":
            logger.setLevel(logging.DEBUG)
            logger.debug("debug mode active")

        self._set_default_properties()

    def __del__(self):
        if hasattr(self, '_adapter_created'):
            self.adapter.deactivate()
        if self._ic is not None:
            self._ic.destroy()

    def _set_default_properties(self):
        for key, value in default_config.items():
            if not self.props.getProperty(key):
                logger.info("setting default value for property '{}' = '{}'".format(key, value))
                self.props.setProperty(key, value)

    @memoizedproperty
    def adapter(self):
        if self.is_bidir:
            adapter_name = ""
            logger.info("using bi-dir connections")

        else:
            adapter_name = "LibCitisimAdapter"
            endpoints_prop = adapter_name + ".Endpoints"
            endpoints = self.props.getProperty(endpoints_prop)
            if not endpoints:
                raise RuntimeError(
                    "You must provide the '{}' configuration property.".format(
                        endpoints_prop))

            logger.info("creating adapter with endpoints: '{}'".format(endpoints))

        adapter = self._ic.createObjectAdapter(adapter_name)
        adapter.activate()
        self._adapter_created = True

        return adapter

    def adapter_add(self, servant, identity):
        if not isinstance(identity, Ice.Identity):
            identity = self._ic.stringToIdentity(normalize_addr(identity))
        return self.adapter.add(servant, identity)

    @memoizedproperty
    def welcome_server(self):
        proxy = self._ic.propertyToProxy(WELCOME_SERVER_PROXY)
        if proxy is None:
            raise RuntimeError(
                "You must provide the '{}' configuration property.".format(
                    WELCOME_SERVER_PROXY))

        return SmartObject.WelcomeServicePrx.checkedCast(proxy)

    @memoizedproperty
    def wiring_server(self):
        proxy = self._ic.propertyToProxy(WIRING_SERVER_PROXY)
        if proxy is None:
            raise RuntimeError(
                "You must provide the '{}' configuration property.".format(
                    WIRING_SERVER_PROXY))

        return SmartServices.WiringServicePrx.checkedCast(proxy)

    @memoizedproperty
    def energy_model(self):
        proxy = self._ic.propertyToProxy(ENERGY_MODEL_SERVER_PROXY)
        if proxy is None:
            raise RuntimeError(
                "You must provide the '{}' configuration property.".format(
                    ENERGY_MODEL_SERVER_PROXY))

        return EnergyForecastPrx.checkedCast(proxy)

    def hello(self, address, transducer_type):
        if self.is_bidir:
            logger.debug("calling helloBidir() on WelcomeServer")
            self.welcome_server.ice_getConnection().setAdapter(self.adapter)
            self.welcome_server.helloBidir(address, transducer_type)
        else:
            logger.debug("calling hello() on WelcomeServer")
            self.welcome_server.hello(address, transducer_type)

    def subscribe(self, topic_name, callback):
        proxy = self._get_servant_proxy(topic_name, callback)
        return self._subscribe_proxy(topic_name, proxy)

    def subscribe_to_publisher(self, source, callback):
        try:
            private_channel_key = source + " | private-channel"
            topic_name = self.get_property(private_channel_key)

            type_key = source + " | transducer-type"
            transducer_type = self.get_property(type_key)

            type_ = datamodel.transducer_types.get(transducer_type)
            assert type_ is not None
        except (PS.PropertyException, AssertionError):
            raise ValueError("Unknown or invalid publisher: {}".format(source))

        servant = self.servant_types[type_](topic_name, callback)
        proxy = self.adapter.addWithUUID(servant)

        return self._subscribe_proxy(topic_name, proxy)

    def _subscribe_proxy(self, topic_name, proxy):
        logger.debug("subscribing proxy {}".format(proxy))
        logger.debug("  to topic {}".format(topic_name))
        topic = self.get_topic(topic_name)

        # support for bidir connections
        if self.is_bidir:
            topic.ice_getConnection().setAdapter(self.adapter)

        topic.subscribeAndGetPublisher({}, proxy)

    def get_publisher(self, source, transducer_type, meta={}):
        logger.debug("retrieving publisher for '{}'...".format(source))

        if transducer_type in ["SpeakerManager"]:
            pub = ObservableInfosystemPublisher(self, source, transducer_type)
        else:
            pub = ObservablePublisher(self, source, transducer_type, meta)

        pub_prx = self.adapter.add(pub, Ice.stringToIdentity(source))
        self.hello(str(pub_prx), transducer_type)
        return pub

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
        return proxy

    def get_topic(self, name):
        try:
            return self.topic_manager.retrieve(name)
        except IceStorm.NoSuchTopic:
            return self.topic_manager.create(name)

    @memoizedproperty
    def topic_manager(self):
        proxy = self._ic.propertyToProxy(TOPICMANAGER_PROXY)
        if proxy is None:
            raise ValueError(
                "You must provide the '{}' configuration property.".format(TOPICMANAGER_PROXY))

        return IceStorm.TopicManagerPrx.checkedCast(proxy)

    def set_property(self, path, value):
        self.property_manager.set(path, json.dumps(value))

    def get_property(self, path):
        return json.loads(self.property_manager.get(path))

    @memoizedproperty
    def property_manager(self):
        manager = self._ic.propertyToProxy(PROPERTY_SERVER_PROXY)
        if manager is None:
            raise ValueError(
                "Missing configuration property: {}".format(PROPERTY_SERVER_PROXY))

        return PS.PropertyServerPrx.checkedCast(manager)


def normalize_addr(address):
    return address.replace(':', '')


def remove_private_endpoints(proxy):
    def is_private(endpoint):
        if sys.version_info.major is 3:
            return ip_address(endpoint.getInfo().host).is_private
        return ip_address(str(endpoint.getInfo().host)).is_private

    endpoints = [e for e in proxy.ice_getEndpoints() if not is_private(e)]
    return proxy.ice_endpoints(endpoints)
