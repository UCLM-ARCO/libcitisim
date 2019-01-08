# # -*- coding: utf-8; mode: python -*-

import os
# from time import time
from subprocess import Popen, PIPE
from select import select
# from io import StringIO
# import contextlib
import shutil
# import json
import Ice
import IceStorm
# from doublex import (
#     assert_that, called, method_returning, method_raising, Mimic, Spy
# )
# from hamcrest import (
#     calling, raises, is_not, anything, close_to, greater_than, equal_to
# )
# from unittest import TestCase

from libcitisim import MetadataHelper, SmartObject
import libcitisim

Ice.loadSlice("/usr/share/slice/PropertyService/PropertyService.ice")
Ice.loadSlice("{0}/citisim/citizen.ice --all -I{0}".format("/usr/share/slice"))
import PropertyService as PS
from Citisim import Citizen


class EventsMixin:
    @classmethod
    def setUpClass(cls):
        pwd = os.path.dirname(__file__)
        db_path = "/tmp/test-libcitisim-is-db"
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
        os.makedirs(db_path)

        cls.config = os.path.join(pwd, "tests.config")
        cmd = "icebox --Ice.Config=" + cls.config
        cls.is_server = Popen(cmd.split(), cwd=pwd, stdout=PIPE)

        # wait for IceStorm to be ready
        pipe = select([cls.is_server.stdout], [], [], 3)[0]
        assert len(pipe), "IceStorm service did not launch correctly"
        assert pipe[0].readline() == b"IceStorm is ready\n"

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "is_server"):
            cls.is_server.terminate()
            cls.is_server.kill()

    def setUp(self):
        # for testing purposes only
        args = ["", "--Ice.Config=" + self.config]
        self.ic = Ice.initialize(args)
        self.adapter = self.ic.createObjectAdapterWithEndpoints(
            'adapter', 'tcp -h 127.0.0.1')
        self.adapter.activate()

        # the real subject under testing
        self.broker = libcitisim.Broker(self.config)

    def tearDown(self):
        self.ic.destroy()

    def _get_topic(self, name):
        manager = self.ic.propertyToProxy("TopicManager.Proxy")
        manager = IceStorm.TopicManagerPrx.checkedCast(manager)
        try:
            return manager.retrieve(name)
        except IceStorm.NoSuchTopic:
            return manager.create(name)

    def _subscribe(self, topic_name, proxy):
        topic = self._get_topic(topic_name)
        topic.subscribeAndGetPublisher({}, proxy)

    def _adapter_add(self, servant):
        return self.adapter.addWithUUID(servant)


class AnalogEventsMixin(EventsMixin):
    known_topics = [
        "ActivePower",
        "AirPollutants1",
        "AirPollutants2",
        "ApparentPower",
        "Anemometer",
        "Battery",
        "CarbonDioxide",
        "CarbonMonoxide",
        "Current",
        "Dioxygen",
        "Energy",
        "HydrocarbonsVOC",
        "Humidity",
        "NitrogenDioxide",
        "Ozone",
        "ParticulateMatter1um",
        "ParticulateMatter2.5um",
        "ParticulateMatter10um",
        "PluviometerCurrent",
        "PluviometerLastDay",
        "PluviometerLastHour",
        "Power",
        "PowerFactor",
        "Pressure",
        "SoilMoisture",
        "SoilTemperature",
        "SolarRadiation",
        "StemDiameter",
        "Temperature",
        "Vibration",
        "Voltage",
        "WindVane",
    ]

    def _publish_event(self, topic_name, source=None, meta={}):
        topic = self._get_topic(topic_name)
        publisher = topic.getPublisher()
        if meta:
            meta = MetadataHelper(**meta).to_dict()
        publisher = SmartObject.AnalogSinkPrx.uncheckedCast(publisher)
        publisher.notify(123.4, "Test", meta)


class DigitalEventsMixin(EventsMixin):
    known_topics = ["Twilight"]

    def _publish_event(self, topic_name, source=None, meta={}, value=True):
        topic = self._get_topic(topic_name)
        publisher = topic.getPublisher()
        if meta:
            meta = MetadataHelper(**meta).to_dict()
        publisher = SmartObject.DigitalSinkPrx.uncheckedCast(publisher)
        publisher.notify(value, "Test", meta)


class ReportEventsMixin(EventsMixin):
    known_topics = ["CitizenReport"]

    def _publish_event(self, topic_name, source=None, meta={}, value=None):
        topic = self._get_topic(topic_name)
        publisher = topic.getPublisher()
        if meta:
            meta = MetadataHelper(**meta).to_dict()
        publisher = Citizen.ReportSinkPrx.uncheckedCast(publisher)
        publisher.notify(value, "Test", meta)


class PropertyMixin:
    @classmethod
    def setUpClass(cls):
        pwd = os.path.dirname(__file__)

        cls.config = os.path.join(pwd, "tests.config")
        cmd = "property-server --Ice.Config=" + cls.config
        cls.is_server = Popen(cmd.split(), cwd=pwd, stdout=PIPE)

        pipe = select([cls.is_server.stdout], [], [], 3)[0]
        assert len(pipe), "Property service did not launch correctly"
        assert pipe[0].readline()[:31] == b'PropertyServer -t -e 1.1:tcp -h'

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "is_server"):
            cls.is_server.terminate()
            cls.is_server.kill()

    def setUp(self):
        # for testing purposes only
        args = ["", "--Ice.Config=" + self.config]
        self.ic = Ice.initialize(args)

        # the real subject under testing
        self.broker = libcitisim.Broker(self.config)

    def tearDown(self):
        self.ic.destroy()

    # FIXME: make manager a memoized property!
    def _get_property(self, path):
        manager = self.ic.propertyToProxy("PropertyService.Proxy")
        manager = PS.PropertyServerPrx.checkedCast(manager)
        return manager.get(path)

    # FIXME: make manager a memoized property!
    def _set_property(self, path, value):
        manager = self.ic.propertyToProxy("PropertyService.Proxy")
        manager = PS.PropertyServerPrx.checkedCast(manager)
        return manager.set(path, value)

