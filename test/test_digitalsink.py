# -*- coding: utf-8; mode: python -*-

from time import time
from io import StringIO
import contextlib
from doublex import (
    assert_that, called, method_returning, method_raising, Mimic, Spy
)
from hamcrest import (
    calling, raises, is_not, anything, close_to, greater_than, equal_to
)
from unittest import TestCase

from libcitisim import SmartObject, MetadataHelper, MetadataField
from utils import DigitalEventsMixin


class DigitalSinkSubscriberTests(DigitalEventsMixin, TestCase):
    def test_subscribe_callback_is_called(self):
        process_event = method_returning(None)
        self.broker.subscribe("Twilight", process_event)
        self._publish_event("Twilight")
        assert_that(process_event, called().async_mode(timeout=3))

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

            assert_that(process_event, called().async_mode(timeout=1))
            output = temp_stderr.getvalue().strip()
            expected = "There were some error on provided callback"
            print("OUT:", output)
            self.assertIn(expected, output)


class DigitalSinkI(SmartObject.DigitalSink):
    def __init__(self, servant):
        self.servant = servant

    def notify(self, *args, **kwargs):
        self.servant.notify(*args, **kwargs)


class DigitalSinkPublisherTests(DigitalEventsMixin, TestCase):
    def setUp(self):
        DigitalEventsMixin.setUp(self)

        self.value = True
        self.meta = {"quality": 254}
        self.servant = Mimic(Spy, SmartObject.DigitalSink)
        self.proxy = self._adapter_add(DigitalSinkI(self.servant))

    def test_publisher_simple_event(self):
        # create a reusable publisher for the given topic, source as a
        # random string, meta with timestamp updated
        source = "0011223344556687"
        transducer_type = "DoorSensor"

        p = self.broker.get_publisher(source, transducer_type)
        p.subscribe(self.proxy)
        p.publish(self.value)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, anything(), anything(), anything()).
                    async_mode(timeout=2))

        got_meta = self.servant.notify.calls[0].args[2]
        got_ts = int(got_meta[SmartObject.MetadataField.Timestamp])
        assert_that(got_ts, close_to(time(), 10))

        got_source = self.servant.notify.calls[0].args[1]
        assert_that(len(got_source), greater_than(5))

    def test_publisher_with_default_meta(self):
        # create a reusable publisher, set source and meta as
        # specified plus Timestamp field
        source = "0011223344556687"
        transducer_type = "DoorSensor"
        meta = {"quality": 24}

        p = self.broker.get_publisher(source, transducer_type, meta=meta)
        p.subscribe(self.proxy)
        p.publish(self.value)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, source, anything(), anything()).
                    async_mode(timeout=2))

        got_meta = self.servant.notify.calls[0].args[2]
        got_ts = int(got_meta[SmartObject.MetadataField.Timestamp])
        assert_that(got_ts, close_to(time(), 10))

        got_quality = int(got_meta[SmartObject.MetadataField.Quality])
        assert_that(got_quality, equal_to(meta["quality"]))

    def test_publisher_with_overridden_meta_just_once(self):
        # update meta only for this specific event, it will have
        # Timestamp and also what you say here
        source = "0011223344556687"
        transducer_type = "DoorSensor"
        meta = {"quality": 120}

        p = self.broker.get_publisher(source, transducer_type)
        p.subscribe(self.proxy)
        p.publish(self.value, meta=meta)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, anything(), anything(), anything()).
                    async_mode(timeout=2))

        got_meta = self.servant.notify.calls[0].args[2]
        got_ts = int(got_meta[SmartObject.MetadataField.Timestamp])
        assert_that(got_ts, close_to(time(), 10))

        got_quality = int(got_meta[SmartObject.MetadataField.Quality])
        assert_that(got_quality, equal_to(meta["quality"]))

    def test_publisher_with_overridden_invalid_meta_just_once(self):
        # it should raise an exception as it uses the MetadataHelper
        source = "0011223344556687"
        transducer_type = "DoorSensor"
        p = self.broker.get_publisher(source, transducer_type)

        assert_that(
            calling(p.publish).
            with_args(False, meta={"invalidkey": 1}),
            raises(KeyError))

        assert_that(
            calling(p.publish).
            with_args(True, meta={"quality": "invalidvalue"}),
            raises(TypeError))

    def test_publisher_with_no_timestamp_in_meta_just_once(self):
        # create a reusable publisher for the given topic, source as a
        # random string, no timestamp in meta
        source = "0011223344556687"
        transducer_type = "DoorSensor"
        p = self.broker.get_publisher(
            source, transducer_type,
            meta={"timestamp": None})
        p.subscribe(self.proxy)
        p.publish(self.value)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, anything(), anything(), anything()).
                    async_mode(timeout=2))

        got_meta = self.servant.notify.calls[0].args[2]
        assert_that(SmartObject.MetadataField.Timestamp not in got_meta)
