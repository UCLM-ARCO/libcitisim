# # -*- coding: utf-8; mode: python -*-

import os
import shutil
import Ice
import IceStorm
import libcitisim
from subprocess import Popen, PIPE
from select import select
from libcitisim import MetadataHelper, SmartObject

Ice.loadSlice("/usr/share/slice/PropertyService/PropertyService.ice")
Ice.loadSlice("{0}/citisim/citizen.ice --all -I{0}".format("/usr/share/slice"))
import PropertyService as PS
from Citisim import Citizen


class EventsMixin:
    @classmethod
    def setUpClass(cls):
        print("- setting up class...")
        cls.pwd = os.path.dirname(__file__)
        cls.config = os.path.join(cls.pwd, "tests.config")

        cls.run_icestorm_server()
        cls.run_property_server()
        cls.run_welcome_server()

    @classmethod
    def run_icestorm_server(cls):
        db_path = "/tmp/test-libcitisim-is-db"
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
        os.makedirs(db_path)

        config = os.path.join(cls.pwd, "is.config")
        cmd = "icebox --Ice.Config=" + config
        cls.is_server = Popen(cmd.split(), cwd=cls.pwd, stdout=PIPE)

        print("- waiting for IS to launch...")
        pipe = select([cls.is_server.stdout], [], [], 3)[0]
        assert len(pipe), "IceStorm service did not launch correctly"
        assert pipe[0].readline() == b"IceStorm is ready\n"
        print("- IceStorm server OK")

    @classmethod
    def run_property_server(cls):
        config = os.path.join(cls.pwd, "ps.config")
        cmd = "property-server --Ice.Config=" + config

        if os.path.exists("/tmp/ps.json"):
            os.unlink("/tmp/ps.json")

        cls.ps_server = Popen(cmd.split(), cwd=cls.pwd, stdout=PIPE)
        print("- waiting for PropertyServer to launch...")
        while True:
            pipe = select([cls.ps_server.stdout], [], [], 3)[0]
            out = pipe[0].readline()
            assert len(pipe), "PropertyService did not launch correctly"
            if out.startswith(b"PropertyServer -t -e 1.1:tcp"):
                break
        print("- Property server OK")

    @classmethod
    def run_welcome_server(cls):
        config = os.path.join(cls.pwd, "welcome.config")
        cmd = "citisim-welcome --Ice.Config=" + config

        cls.welcome_server = Popen(
            cmd.split(), cwd=cls.pwd, stdout=PIPE, stderr=PIPE)
        print("- waiting for WelcomeServer to launch...")
        pipe = select([cls.welcome_server.stderr], [], [], 3)[0]
        assert len(pipe), "WelcomeService service did not launch correctly"
        out = pipe[0].readline()
        assert out == b"INFO:Welcome service started\n", out
        print("- Welcome server OK")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "is_server"):
            cls.is_server.terminate()
            cls.is_server.kill()

        if hasattr(cls, "welcome_server"):
            cls.welcome_server.terminate()
            cls.welcome_server.kill()

        if hasattr(cls, "ps_server"):
            cls.ps_server.terminate()
            cls.ps_server.kill()

    def setUp(self):
        print("- setting up instance...")
        # for testing purposes only
        args = ["", "--Ice.Config=" + self.config]
        self.ic = Ice.initialize(args)
        self.adapter = self.ic.createObjectAdapterWithEndpoints(
            'adapter', 'tcp -h 127.0.0.1')
        self.adapter.activate()

        # the real subject under testing
        self.broker = libcitisim.Broker(self.config)
        print("- instance setup OK")

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
        print(topic.subscribeAndGetPublisher({}, proxy))

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



