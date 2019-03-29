# -*- coding: utf-8; mode: python -*-

from doublex import assert_that, called, method_returning
from hamcrest import calling, raises
from unittest import TestCase

from utils import AnalogEventsMixin


class CommonSubscriberTests(AnalogEventsMixin, TestCase):
    def test_subscribe_to_an_unknown_topic_is_not_possible(self):
        # this should raise a ValueError exception
        process_event = method_returning(None)
        assert_that(
            calling(self.broker.subscribe).with_args(
                "UnknownTopic", process_event),
            raises(ValueError))

    def test_subscriber_received_metadata_with_stringfied_keys(self):
        process_event = method_returning(None)
        self.broker.subscribe("WindVane", process_event)
        self._publish_event("WindVane", meta={"quality": 123})

        assert_that(process_event, called().async(timeout=3))
        meta = process_event.calls[0].args[2]
        for key in meta.keys():
            self.assertIsInstance(key, str)


class CommonPublisherTests(AnalogEventsMixin, TestCase):
    def test_publish_with_unknown_transducer_type(self):
        # this should raise an exception
        source = "0011223344556677"

        assert_that(
            calling(self.broker.get_publisher).
            with_args(source, "InvalidType"),
            raises(TypeError))

