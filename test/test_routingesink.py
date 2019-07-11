# -*- coding: utf-8; mode: python -*-

import contextlib
from io import StringIO
from doublex import (
    assert_that, called, method_returning, method_raising, Mimic, Spy
)
from hamcrest import calling, raises, is_not, anything
from unittest import TestCase

from libcitisim import SmartServices
from utils import RoutingEventsMixin


class RoutingSinkSubscriberTests(RoutingEventsMixin, TestCase):
    def test_subscribe_callback_is_called(self):
        process_event = method_returning(None)
        topic = "EvacuationRoute"
        self.broker.subscribe(topic, process_event)
        self._publish_event(topic)
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
        topic = "EvacuationRoute"
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


class RoutingSinkI(SmartServices.RoutingSink):
    def __init__(self, servant):
        self.servant = servant

    def notify(self, *args, **kwargs):
        self.servant.notify(*args, **kwargs)


class RoutingSinkPublisherTests(RoutingEventsMixin, TestCase):
    def setUp(self):
        RoutingEventsMixin.setUp(self)

        self.value = ["CELL1", "CELL2", "CELL3"]
        self.servant = Mimic(Spy, SmartServices.RoutingSink)
        self.proxy = self._adapter_add(RoutingSinkI(self.servant))

    def test_publisher_simple_event(self):
        source = "0011223344556687"
        transducer_type = "RouteService"

        p = self.broker.get_publisher(source, transducer_type)
        p.subscribe(self.proxy)
        p.publish(self.value)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.value, anything()).
                    async_mode(timeout=2))
