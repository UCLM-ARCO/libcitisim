# # -*- coding: utf-8; mode: python -*-

import os
import Ice
import IceStorm
import libcitisim
from libcitisim import MetadataHelper, SmartObject, SmartServices
from libcitisim.util import EventsMixin as UtilEventMixin

Ice.loadSlice("/usr/share/slice/PropertyService/PropertyService.ice")
Ice.loadSlice("{0}/citisim/citizen.ice --all -I{0}".format("/usr/share/slice"))
import PropertyService as PS
from Citisim import Citizen


class EventsMixin(UtilEventMixin):
    pwd = os.path.dirname(__file__)
    config = os.path.join(pwd, "tests.config")

    def setUp(self):
        self._ice_setup()
        self.broker = libcitisim.Broker(self.config)
        print("- instance setup OK")

    def tearDown(self):
        self._ice_finish()
        self.broker.property_manager.clear()


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


class RoutingEventsMixin(EventsMixin):
    known_topics = ["EvacuationRoute"]

    def _publish_event(self, topic_name, value=[]):
        topic = self._get_topic(topic_name)
        publisher = topic.getPublisher()
        publisher = SmartServices.RoutingSinkPrx.uncheckedCast(publisher)
        publisher.notify(value)


class PropertyMixin(EventsMixin):
    @classmethod
    def setUpClass(cls):
        print("- setting up class...")
        cls.pwd = os.path.dirname(__file__)
        cls.config = os.path.join(cls.pwd, "tests.config")

        cls.run_property_server()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "ps_server"):
            cls.ps_server.terminate()
            cls.ps_server.kill()

    def setUp(self):
        # for testing purposes only
        args = ["", "--Ice.Config=" + self.config]
        self.ic = Ice.initialize(args)
        self.props = PS.PropertyServerPrx.checkedCast(
            self.ic.propertyToProxy("PropertyServer.Proxy"))

        # the real subject under testing
        self.broker = libcitisim.Broker(self.config)

    def tearDown(self):
        self.ic.destroy()

    def _get_property(self, path):
        return self.props.get(path)

    def _set_property(self, path, value):
        return self.props.set(path, value)



