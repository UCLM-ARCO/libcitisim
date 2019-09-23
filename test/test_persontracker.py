# -*- coding: utf-8; mode: python -*-

import os
import contextlib
import logging
from io import StringIO
from doublex import (
    assert_that, called, method_returning, method_raising, Mimic, Spy
)
from hamcrest import calling, raises, is_not, anything
from unittest import TestCase
from utils import PersonTrackerMixin
from libcitisim import KinectData


class PersonTrackerSubscriberTests(PersonTrackerMixin, TestCase):
    def test_subscribe_callback_is_called(self):
        process_event = method_returning(None)
        self.broker.subscribe("PersonTracking", process_event)
        self._publish_event("PersonTracking")
        assert_that(process_event, called().async_mode(timeout=3))

    def test_subscribe_to_all_current_topics(self):
        process_event = method_returning(None)
        for name in self.known_topics:
            assert_that(
                calling(self.broker.subscribe).with_args(name, process_event),
                is_not(raises(Exception)))

    def test_wrong_subcriber_callback(self):
        process_event = method_raising(TypeError)
        self.broker.subscribe("PersonTracking", process_event)

        temp_stderr = StringIO()
        logger = logging.getLogger('libcitisim')
        logger.handlers = []
        handler = logging.StreamHandler(stream=temp_stderr)
        logger.addHandler(handler)

        with contextlib.redirect_stderr(temp_stderr):
            self._publish_event("PersonTracking")

            assert_that(process_event, called().async_mode(timeout=1))
            output = temp_stderr.getvalue().strip()
            expected = "There were some error on provided callback"
            print("OUT:", output)
            self.assertIn(expected, output)


class PersonTrackerI(KinectData.PersonTracker):
    def __init__(self, servant):
        self.servant = servant

    def notify(self, *args, **kwargs):
        self.servant.notify(*args, **kwargs)


class PersonTrackerPublisherTests(PersonTrackerMixin, TestCase):
    def setUp(self):
        PersonTrackerMixin.setUp(self)

        self.source = "0011223344556677"
        self.transducer_type = "PersonTracker"
        self.points = [
            KinectData.KinectPoint(
                "trackid", "state", .0, .25, 1.5, .5, 4.75, .125, 12, 12345623
            )
        ]
        self.servant = Mimic(Spy, KinectData.PersonTracker)
        self.proxy = self._adapter_add(PersonTrackerI(self.servant))

    def test_publisher_simple_event(self):
        p = self.broker.get_publisher(self.source, self.transducer_type)
        p.subscribe(self.proxy)
        p.publish(self.points)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.points, self.source, anything()).
                    async_mode(timeout=2))


class BidirPersonTrackerPublisherTests(PersonTrackerMixin, TestCase):
    @classmethod
    def setUpClass(cls):
        print("- setting up class...")
        cls.pwd = os.path.dirname(__file__)
        cls.config = os.path.join(cls.pwd, "tests-bidir.config")

        cls.run_icestorm_server()
        cls.run_property_server()
        cls.run_welcome_server()

    def setUp(self):
        PersonTrackerMixin.setUp(self)

        self.source = "0011223344556677"
        self.transducer_type = "PersonTracker"
        self.points = [
            KinectData.KinectPoint(
                "trackid", "state", .0, .25, 1.5, .5, 4.75, .125, 12, 12345623
            )
        ]
        self.servant = Mimic(Spy, KinectData.PersonTracker)
        self.proxy = self._adapter_add(PersonTrackerI(self.servant))

    def test_bidir_publisher_simple_event(self):
        p = self.broker.get_publisher(self.source, self.transducer_type)
        p.subscribe(self.proxy)
        p.publish(self.points)

        assert_that(self.servant.notify,
                    called().
                    with_args(self.points, self.source, anything()).
                    async_mode(timeout=2))
