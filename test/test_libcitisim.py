# -*- coding: utf-8; mode: python -*-

import os
from time import time
from subprocess import Popen, PIPE
from select import select
from io import StringIO
import contextlib
import shutil
import Ice
import IceStorm
from doublex import (
    assert_that, called, method_returning, method_raising, Mimic, Spy
)
from hamcrest import (
    calling, raises, is_not, anything, close_to, greater_than, equal_to
)
from unittest import TestCase

from libcitisim import MetadataHelper, MetadataField, SmartObject
import libcitisim

import json

class EventSinkI(SmartObject.EventSink):
    def notify(self, source, metdata, current=None):
        pass


class MetadataHelperTests(TestCase):
    def test_empty_to_dict(self):
        sut = MetadataHelper()
        self.assertEquals(sut.to_dict(), {})

    def test_timestamp_to_dict(self):
        sut = MetadataHelper(timestamp=0)
        self.assertEquals(sut.to_dict(), {MetadataField.Timestamp: '0'})

    def test_2_fields_to_dict(self):
        sut = MetadataHelper(quality=125, latitude=123.4)
        dct = sut.to_dict()
        self.assertEquals(dct, {
            MetadataField.Quality: '125',
            MetadataField.Latitude: '123.4'
        })

    def test_quality_type_check(self):
        with self.assertRaises(TypeError):
            MetadataHelper(quality=300)

    def test_expiration_type_check(self):
        with self.assertRaises(TypeError):
            MetadataHelper(expiration=2**16)

    def test_set_invalid_key(self):
        with self.assertRaises(KeyError):
            MetadataHelper(missing=10)

    def test_get_field(self):
        sut = MetadataHelper(quality=125, latitude=123.4)
        self.assertEquals(sut.quality, 125)

    def test_get_field_by_get(self):
        sut = MetadataHelper(timestamp=10)
        self.assertEquals(sut.get('timestamp'), 10)

    def test_get_value_dict_by_name_field(self):
        sut = MetadataHelper(timestamp=10).to_dict()
        self.assertEquals(int(sut.get(MetadataField.Timestamp)), 10)

    def test_get_values(self):
        sut = MetadataHelper(
            timestamp=10,
            quality=100,
            expiration=10).to_dict()
        self.assertEquals(list(sut.values()), ['10', '100', '10'])


class MetadataHelperMarshallTests(TestCase):
    def setUp(self):
        self.broker = Ice.initialize()
        self.adapter = self.broker.createObjectAdapterWithEndpoints(
            'adapter', 'tcp')
        self.adapter.activate()

    def tearDown(self):
        self.broker.destroy()

    def adapter_add(self, cast, servant):
        proxy = self.adapter.addWithUUID(servant)
        return cast.uncheckedCast(proxy)

    def test_empty(self):
        servant = Mimic(Spy, SmartObject.EventSink)
        sink = self.adapter_add(SmartObject.EventSinkPrx, servant)

        meta = MetadataHelper()
        sink.notify('', meta.to_dict())

    def test_timestamp(self):
        servant = Mimic(Spy, SmartObject.EventSink)
        sink = self.adapter_add(SmartObject.EventSinkPrx, servant)

        meta = MetadataHelper(timestamp=10).to_dict()
        sink.notify('', meta)


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
        "Temperature", "Power", "Vibration", "WindVane", "PluviometerLastDay",
        "Anemometer", "Battery", "CarbonDioxide", "Humidity", "Ozone",
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


class CommonSubscriberTests(AnalogEventsMixin, TestCase):
    def test_subscribe_to_an_unknown_topic_is_not_possible(self):
        # this should raise a ValueError exception
        process_event = method_returning(None)
        assert_that(
            calling(self.broker.subscribe).with_args(
                "UnknownTopic", process_event),
            raises(ValueError))

        assert_that(
            calling(self.broker.publish).
            with_args("Temperature", 123.5, meta={"quality": "invalidvalue"}),
            raises(TypeError))

    def test_subscriber_received_metadata_with_stringfied_keys(self):
        process_event = method_returning(None)
        self.broker.subscribe("WindVane", process_event)
        self._publish_event("WindVane", meta={"quality": 123})

        assert_that(process_event, called().async(timeout=3))
        meta = process_event.calls[0].args[2]
        for key in meta.keys():
            self.assertIsInstance(key, str)


class CommonPublisherTests(AnalogEventsMixin, TestCase):
    def test_publish_to_unknown_topic_is_not_possible(self):
        assert_that(
            calling(self.broker.publish).with_args("UnknownTopic", 1.263),
            raises(ValueError))


class AnalogSinkSubscriberTests(AnalogEventsMixin, TestCase):
    def test_subscribe_callback_is_called(self):
        process_event = method_returning(None)
        self.broker.subscribe("Temperature", process_event)
        self._publish_event("Temperature")
        assert_that(process_event, called().async(timeout=3))

    def test_subscribe_to_all_current_topics(self):
        # this not raising an exception means the topic is known for
        # the library
        process_event = method_returning(None)
        for name in self.known_topics:
            assert_that(
                calling(self.broker.subscribe).with_args(name, process_event),
                is_not(raises(Exception)))

    def test_wrong_subcriber_callback(self):
        process_event = method_raising(TypeError)
        self.broker.subscribe("WindVane", process_event)

        temp_stderr = StringIO()

        import logging
        logger = logging.getLogger('libcitisim')
        logger.handlers = []
        handler = logging.StreamHandler(stream=temp_stderr)
        logger.addHandler(handler)

        with contextlib.redirect_stderr(temp_stderr):
            self._publish_event("WindVane")

            assert_that(process_event, called().async(timeout=1))
            output = temp_stderr.getvalue().strip()
            expected = "There were some error on provided callback"
            print("OUT:", output)
            self.assertIn(expected, output)


class AnalogSinkPublisherTests(AnalogEventsMixin, TestCase):
    def setUp(self):
        AnalogEventsMixin.setUp(self)

        self.topic_name = "Temperature"
        self.value = 123.5
        self.source = "TestSource"
        self.meta = {"quality": 200}

        self.servant = Mimic(Spy, SmartObject.AnalogSink)
        self.proxy = self._adapter_add(self.servant)
        self._subscribe(self.topic_name, self.proxy)

    def test_one_time_publish_event_is_ok(self):
        # create a one-time-usage publisher, set source as a random
        # string, meta with timestamp updated
        self.broker.publish(self.topic_name, self.value)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, anything(), anything(), anything()).
                    async(timeout=2))

        got_meta = self.servant.notify.calls[0].args[2]
        got_ts = int(got_meta[SmartObject.MetadataField.Timestamp])
        assert_that(got_ts, close_to(time(), 10))

        got_source = self.servant.notify.calls[0].args[1]
        assert_that(len(got_source), greater_than(5))

    def test_one_time_publish_given_source_and_meta(self):
        # create a one-time-usage publisher, set source as given, and
        # meta with Timestamp and also what you set here

        self.broker.publish(
            self.topic_name, self.value, self.source, self.meta)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, self.source, anything(), anything()).
                    async(timeout=2))

        got_meta = self.servant.notify.calls[0].args[2]
        got_ts = int(got_meta[SmartObject.MetadataField.Timestamp])
        assert_that(got_ts, close_to(time(), 1))

        got_quality = int(got_meta[SmartObject.MetadataField.Quality])
        assert_that(got_quality, equal_to(self.meta["quality"]))

    def test_one_time_publish_with_incorrect_meta(self):
        # it should raise an exception as it uses the MetadataHelper
        assert_that(
            calling(self.broker.publish).
            with_args("Temperature", 123.5, meta={"someunknownkey": True}),
            raises(KeyError))

        assert_that(
            calling(self.broker.publish).
            with_args("Temperature", 123.5, meta={"quality": "invalidvalue"}),
            raises(TypeError))

    def test_publisher_simple_event(self):
        # create a reusable publisher for the given topic, source as a
        # random string, meta with timestamp updated
        topic_name = "Temperature"
        p = self.broker.get_publisher(topic_name)
        p.publish(self.value)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, anything(), anything(), anything()).
                    async(timeout=2))

        got_meta = self.servant.notify.calls[0].args[2]
        got_ts = int(got_meta[SmartObject.MetadataField.Timestamp])
        assert_that(got_ts, close_to(time(), 10))

        got_source = self.servant.notify.calls[0].args[1]
        assert_that(len(got_source), greater_than(5))

    def test_publisher_with_default_source_and_meta(self):
        # create a reusable publisher, set source and meta as
        # specified plus Timestamp field
        source = "Source123"
        meta = {"quality": 24}
        p = self.broker.get_publisher("Temperature", source=source, meta=meta)
        p.publish(self.value)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, source, anything(), anything()).
                    async(timeout=2))

        got_meta = self.servant.notify.calls[0].args[2]
        got_ts = int(got_meta[SmartObject.MetadataField.Timestamp])
        assert_that(got_ts, close_to(time(), 1))

        got_quality = int(got_meta[SmartObject.MetadataField.Quality])
        assert_that(got_quality, equal_to(meta["quality"]))

    def test_publisher_with_overridden_source_just_once(self):
        # change source only for this specific event
        p = self.broker.get_publisher("Temperature")

        p.publish(self.value)
        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, anything(), anything(), anything()).
                    async(timeout=2))

        source = "Source1"
        p.publish(self.value, source=source)
        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, source, anything(), anything()).
                    async(timeout=2))

    def test_publisher_with_overridden_meta_just_once(self):
        # update meta only for this specific event, it will have
        # Timestamp and also what you say here
        p = self.broker.get_publisher("Temperature")
        meta = {"quality": 120}
        p.publish(self.value, meta=meta)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, anything(), anything(), anything()).
                    async(timeout=2))

        got_meta = self.servant.notify.calls[0].args[2]
        got_ts = int(got_meta[SmartObject.MetadataField.Timestamp])
        assert_that(got_ts, close_to(time(), 10))

        got_quality = int(got_meta[SmartObject.MetadataField.Quality])
        assert_that(got_quality, equal_to(meta["quality"]))

    def test_publisher_with_overridden_invalid_meta_just_once(self):
        # it should raise an exception as it uses the MetadataHelper
        p = self.broker.get_publisher("Temperature")

        assert_that(
            calling(p.publish).
            with_args(123.5, meta={"invalidkey": 1}),
            raises(KeyError))

        assert_that(
            calling(p.publish).
            with_args(123.5, meta={"quality": "invalidvalue"}),
            raises(TypeError))

    def test_publisher_with_no_meta_just_once(self):
        # create a reusable publisher for the given topic, source as a
        # random string, no meta
        p = self.broker.get_publisher("Temperature", meta={"timestamp": None})
        p.publish(self.value)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, anything(), anything(), anything()).
                    async(timeout=2))

        got_meta = self.servant.notify.calls[0].args[2]
        assert_that(SmartObject.MetadataField.Timestamp not in got_meta)

    def test_publish_to_all_current_topics(self):
        # this not raising an exception means the topic is known for
        # the library
        value = 12
        for name in self.known_topics:
            servant = Mimic(Spy, SmartObject.AnalogSink)
            proxy = self._adapter_add(servant)
            self._subscribe(name, proxy)

            self.broker.publish(name, value)
            assert_that(servant.notify,
                        called().
                        with_args(value, anything(), anything(), anything()).
                        async(timeout=2))
            value += 5


class DigitalSinkSinkSubscriberTests(DigitalEventsMixin, TestCase):
    def test_subscribe_callback_is_called(self):
        process_event = method_returning(None)
        self.broker.subscribe("Twilight", process_event)
        self._publish_event("Twilight")
        assert_that(process_event, called().async(timeout=3))

    def test_subscribe_to_all_current_topics(self):
        # this not raising an exception means the topic is known for
        # the library
        process_event = method_returning(None)
        for name in self.known_topics:
            assert_that(
                calling(self.broker.subscribe).with_args(name, process_event),
                is_not(raises(Exception)))

    def test_wrong_subcriber_callback(self):
        process_event = method_raising(TypeError)
        topic = "Twilight"
        self.broker.subscribe(topic, process_event)

        temp_stderr = StringIO()

        import logging
        logger = logging.getLogger('libcitisim')
        logger.handlers = []
        handler = logging.StreamHandler(stream=temp_stderr)
        logger.addHandler(handler)

        with contextlib.redirect_stderr(temp_stderr):
            self._publish_event(topic)

            assert_that(process_event, called().async(timeout=1))
            output = temp_stderr.getvalue().strip()
            expected = "There were some error on provided callback"
            print("OUT:", output)
            self.assertIn(expected, output)


class DigitalSinkPublisherTests(DigitalEventsMixin, TestCase):
    def setUp(self):
        DigitalEventsMixin.setUp(self)

        self.topic_name = "Twilight"
        self.value = True
        self.source = "TestSource"
        self.meta = {"quality": 254}

        self.servant = Mimic(Spy, SmartObject.DigitalSink)
        self.proxy = self._adapter_add(self.servant)
        self._subscribe(self.topic_name, self.proxy)

    def test_one_time_publish_event_is_ok(self):
        # create a one-time-usage publisher, set source as a random
        # string, meta with timestamp updated
        self.broker.publish(self.topic_name, self.value)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, anything(), anything(), anything()).
                    async(timeout=2))

        got_meta = self.servant.notify.calls[0].args[2]
        got_ts = int(got_meta[SmartObject.MetadataField.Timestamp])
        assert_that(got_ts, close_to(time(), 10))

        got_source = self.servant.notify.calls[0].args[1]
        assert_that(len(got_source), greater_than(5))

    def test_one_time_publish_given_source_and_meta(self):
        # create a one-time-usage publisher, set source as given, and
        # meta with Timestamp and also what you set here

        self.broker.publish(
            self.topic_name, self.value, self.source, self.meta)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, self.source, anything(), anything()).
                    async(timeout=2))

        got_meta = self.servant.notify.calls[0].args[2]
        got_ts = int(got_meta[SmartObject.MetadataField.Timestamp])
        assert_that(got_ts, close_to(time(), 10))

        got_quality = int(got_meta[SmartObject.MetadataField.Quality])
        assert_that(got_quality, equal_to(self.meta["quality"]))

    def test_one_time_publish_with_incorrect_meta(self):
        # it should raise an exception as it uses the MetadataHelper
        assert_that(
            calling(self.broker.publish).
            with_args(self.topic_name, self.value,
                      meta={"someunknownkey": True}),
            raises(KeyError))

        assert_that(
            calling(self.broker.publish).
            with_args(self.topic_name, self.value,
                      meta={"quality": "invalidvalue"}),
            raises(TypeError))

    def test_publisher_simple_event(self):
        # create a reusable publisher for the given topic, source as a
        # random string, meta with timestamp updated
        p = self.broker.get_publisher(self.topic_name)
        p.publish(self.value)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, anything(), anything(), anything()).
                    async(timeout=2))

        got_meta = self.servant.notify.calls[0].args[2]
        got_ts = int(got_meta[SmartObject.MetadataField.Timestamp])
        assert_that(got_ts, close_to(time(), 10))

        got_source = self.servant.notify.calls[0].args[1]
        assert_that(len(got_source), greater_than(5))

    def test_publisher_with_default_source_and_meta(self):
        # create a reusable publisher, set source and meta as
        # specified plus Timestamp field
        source = "Source123"
        meta = {"quality": 24}
        p = self.broker.get_publisher(
            self.topic_name, source=source, meta=meta)
        p.publish(self.value)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, source, anything(), anything()).
                    async(timeout=2))

        got_meta = self.servant.notify.calls[0].args[2]
        got_ts = int(got_meta[SmartObject.MetadataField.Timestamp])
        assert_that(got_ts, close_to(time(), 10))

        got_quality = int(got_meta[SmartObject.MetadataField.Quality])
        assert_that(got_quality, equal_to(meta["quality"]))

    def test_publisher_with_overridden_source_just_once(self):
        # change source only for this specific event
        p = self.broker.get_publisher(self.topic_name)

        p.publish(self.value)
        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, anything(), anything(), anything()).
                    async(timeout=2))

        source = "Source1"
        p.publish(self.value, source=source)
        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, source, anything(), anything()).
                    async(timeout=2))

    def test_publisher_with_overridden_meta_just_once(self):
        # update meta only for this specific event, it will have
        # Timestamp and also what you say here
        p = self.broker.get_publisher(self.topic_name)
        meta = {"quality": 120}
        p.publish(self.value, meta=meta)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, anything(), anything(), anything()).
                    async(timeout=2))

        got_meta = self.servant.notify.calls[0].args[2]
        got_ts = int(got_meta[SmartObject.MetadataField.Timestamp])
        assert_that(got_ts, close_to(time(), 10))

        got_quality = int(got_meta[SmartObject.MetadataField.Quality])
        assert_that(got_quality, equal_to(meta["quality"]))

    def test_publisher_with_overridden_invalid_meta_just_once(self):
        # it should raise an exception as it uses the MetadataHelper
        p = self.broker.get_publisher(self.topic_name)

        assert_that(
            calling(p.publish).
            with_args(False, meta={"invalidkey": 1}),
            raises(KeyError))

        assert_that(
            calling(p.publish).
            with_args(True, meta={"quality": "invalidvalue"}),
            raises(TypeError))

    def test_publisher_with_no_meta_just_once(self):
        # create a reusable publisher for the given topic, source as a
        # random string, no meta
        p = self.broker.get_publisher(
            self.topic_name, meta={"timestamp": None})
        p.publish(self.value)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, anything(), anything(), anything()).
                    async(timeout=2))

        got_meta = self.servant.notify.calls[0].args[2]
        assert_that(SmartObject.MetadataField.Timestamp not in got_meta)

    def test_publish_to_all_current_topics(self):
        # this not raising an exception means the topic is known for
        # the library
        value = True
        for name in self.known_topics:
            servant = Mimic(Spy, SmartObject.DigitalSink)
            proxy = self._adapter_add(servant)
            self._subscribe(name, proxy)

            self.broker.publish(name, value)
            assert_that(
                servant.notify,
                called().
                with_args(value, anything(), anything(), anything()).
                async(timeout=2))
            value += 5


ps_slice_path = "/usr/share/slice/PropertyService/PropertyService.ice"
Ice.loadSlice(ps_slice_path)
import PropertyService as PS

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

    def _get_property(self, path):
        manager = self.ic.propertyToProxy("PropertyService.Proxy")
        manager = PS.PropertyServerPrx.checkedCast(manager)
        return manager.get(path)

    def _set_property(self, path, value):
        manager = self.ic.propertyToProxy("PropertyService.Proxy")
        manager = PS.PropertyServerPrx.checkedCast(manager)
        return manager.set(path, value)


class PropertyServerTests(PropertyMixin, TestCase):
    def setUp(self):
        PropertyMixin.setUp(self)

    def tearDown(self):
        PropertyMixin.tearDown(self)

    def test_set_property_string(self):
        # set a string property
        path = '17510026 | units'
        value = 'Celsius'
        self.broker.set_property(path, value)
        obtained_value = json.loads(self._get_property(path))
        assert_that(value, equal_to(obtained_value))

    def test_get_property_string(self):
        # get a string property
        path = '17510026 | units'
        value = 'Celsius'
        self._set_property(path, json.dumps(value))
        obtained_value = json.loads(self.broker.get_property(path))
        assert_that(value, equal_to(obtained_value))

    def test_set_property_int(self):
        # set an int property
        path = '17510026 | int'
        value = 6486
        self.broker.set_property(path, value)
        obtained_value = json.loads(self._get_property(path))
        assert_that(value, equal_to(obtained_value))

    def test_get_property_int(self):
        # get a int property
        path = '17510026 | int'
        value = 6486
        self._set_property(path, json.dumps(value))
        obtained_value = json.loads(self.broker.get_property(path))
        assert_that(value, equal_to(obtained_value))

    def test_set_property_float(self):
        # set a float property
        path = '17510026 | float'
        value = 64.86
        self.broker.set_property(path, value)
        obtained_value = json.loads(self._get_property(path))
        assert_that(value, equal_to(obtained_value))

    def test_get_property_float(self):
        # get a float property
        path = '17510026 | float'
        value = 64.86
        self._set_property(path, json.dumps(value))
        obtained_value = json.loads(self.broker.get_property(path))
        assert_that(value, equal_to(obtained_value))

    def test_set_property_tuple(self):
        # set a tuple property
        path = '17510026 | tuple'
        value = (-50, 255)
        self.broker.set_property(path, value)
        obtained_value = self._get_property(path)
        assert_that(json.dumps(value), equal_to(obtained_value))

    def test_get_property_tuple(self):
        # get a tuple property
        path = '17510026 | tuple'
        value = (-50, 255)
        self._set_property(path, json.dumps(value))
        obtained_value = self.broker.get_property(path)
        assert_that(json.dumps(value), equal_to(obtained_value))

    def test_set_property_list(self):
        # set a list property
        path = '17510026 | list'
        value = [-50, 255]
        self.broker.set_property(path, value)
        obtained_value = json.loads(self._get_property(path))
        assert_that(value, equal_to(obtained_value))

    def test_get_property_list(self):
        # get a list property
        path = '17510026 | list'
        value = [-50, 255]
        self._set_property(path, json.dumps(value))
        obtained_value = json.loads(self.broker.get_property(path))
        assert_that(value, equal_to(obtained_value))

    def test_set_property_dict(self):
        # set a dictionary property
        path = '17510026 | dict'
        value = {'key1':'a', 'key2':2, 'key3':3.14}
        self.broker.set_property(path, value)
        obtained_value = json.loads(self._get_property(path))
        assert_that(value, equal_to(obtained_value))
        # individual key values
        key1_value = json.loads(self._get_property('17510026 | dict | key1'))
        assert_that(value['key1'], equal_to(key1_value))
        key2_value = json.loads(self._get_property('17510026 | dict | key2'))
        assert_that(value['key2'], equal_to(key2_value))
        key3_value = json.loads(self._get_property('17510026 | dict | key3'))
        assert_that(value['key3'], equal_to(key3_value))

    def test_get_property_dict(self):
        # get a dictionary property
        path = '17510026 | dict'
        value = {'key1':'a', 'key2':2, 'key3':3.14}
        self._set_property(path, json.dumps(value))
        obtained_value = json.loads(self.broker.get_property(path))
        assert_that(value, equal_to(obtained_value))
        # individual key values
        key1_value = json.loads(self.broker.get_property('17510026 | dict | key1'))
        assert_that(value['key1'], equal_to(key1_value))
        key2_value = json.loads(self.broker.get_property('17510026 | dict | key2'))
        assert_that(value['key2'], equal_to(key2_value))
        key3_value = json.loads(self.broker.get_property('17510026 | dict | key3'))
        assert_that(value['key3'], equal_to(key3_value))

    def test_set_not_serializable(self):
        # set a value that can not be JSON serialized
        path = '17510026 | notSerializable'
        value = time
        # this should raise a TypeError Exception
        process_event = method_returning(None)
        assert_that(
            calling(self.broker.set_property).with_args(path, value,
                process_event), raises(TypeError))


class DefaultPropertyTests(TestCase):
    def test_default_topicmanager_proxy(self):
        sut = libcitisim.Broker('')

        try:
            print(sut._get_topic_manager())
        except ValueError:
            self.fail("Default 'TopicManager.Proxy' property not set")
        except Ice.NoEndpointException:
            pass


class PropertyCastTests(TestCase):
    def test_right_unit(self):
        libcitisim.datamodel.properties['units'].check('wats')

    def test_wrong_unit(self):
        with self.assertRaises(TypeError):
            libcitisim.datamodel.properties['units'].check('wrong')        