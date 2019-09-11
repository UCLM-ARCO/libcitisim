# -*- coding: utf-8; mode: python -*-

import contextlib
import logging
from io import StringIO
from doublex import (
    method_returning, assert_that, called, Spy, method_raising, Mimic, Stub,
    set_default_behavior
)
from hamcrest import (
    calling, raises, is_not, anything, close_to, greater_than, equal_to
)
from unittest import TestCase

from utils import SpeakerManagerEventsMixin, infosystem


class LoudSpeakerManagerSubscriberTests(SpeakerManagerEventsMixin, TestCase):
    def test_sayInPlace_callback_is_called(self):
        with Spy() as callback:
            callback.sayInPlace().returns(None)

        self.broker.subscribe("SpeakerMessages", callback)
        self._publish_sayInPlace("SpeakerMessages")
        assert_that(callback.sayInPlace, called().async_mode(timeout=3))

    def test_sayInSpeaker_callback_is_called(self):
        with Spy() as callback:
            callback.sayInSpeaker().returns(None)

        self.broker.subscribe("SpeakerMessages", callback)
        self._publish_sayInSpeaker("SpeakerMessages")
        assert_that(callback.sayInSpeaker, called().async_mode(timeout=3))

    def test_subscribe_to_all_current_topics(self):
        # this not raising an exception means the topic is known for
        # the library
        process_event = Spy()
        for name in self.known_topics:
            assert_that(
                calling(self.broker.subscribe).with_args(name, process_event),
                is_not(raises(Exception)))

    def test_subscriber_callback_missing_sayInPlace(self):
        callback = Spy()
        set_default_behavior(callback, method_raising(AttributeError))

        self.broker.subscribe("SpeakerMessages", callback)
        temp_stderr = StringIO()

        logger = logging.getLogger('libcitisim')
        logger.handlers = []
        handler = logging.StreamHandler(stream=temp_stderr)
        logger.addHandler(handler)

        with contextlib.redirect_stderr(temp_stderr):
            self._publish_sayInPlace("SpeakerMessages")
            assert_that(callback.sayInPlace, called().async_mode(timeout=1))
            output = temp_stderr.getvalue().strip()
            expected = "There were some error on provided callback"
            self.assertIn(expected, output)

    def test_subscriber_callback_missing_sayInSpeaker(self):
        callback = Spy()
        set_default_behavior(callback, method_raising(AttributeError))

        self.broker.subscribe("SpeakerMessages", callback)
        temp_stderr = StringIO()

        logger = logging.getLogger('libcitisim')
        logger.handlers = []
        handler = logging.StreamHandler(stream=temp_stderr)
        logger.addHandler(handler)

        with contextlib.redirect_stderr(temp_stderr):
            self._publish_sayInSpeaker("SpeakerMessages")
            assert_that(callback.sayInSpeaker, called().async_mode(timeout=1))
            output = temp_stderr.getvalue().strip()
            expected = "There were some error on provided callback"
            self.assertIn(expected, output)


class LoudSpeakerManagerI(infosystem.LoudSpeakerManager):
    def __init__(self, servant):
        self.servant = servant

    def sayInPlace(self, *args, **kwargs):
        self.servant.sayInPlace(*args, **kwargs)

    def sayInSpeaker(self, *args, **kwargs):
        self.servant.sayInSpeaker(*args, **kwargs)


class LoudSpeakerManagerPublisherTests(SpeakerManagerEventsMixin, TestCase):
    def setUp(self):
        SpeakerManagerEventsMixin.setUp(self)

        self.source = "TestPublisher"
        self.topic_name = "SpeakerMessages"
        self.place = "someplace"
        self.speaker = "spkr-05"
        self.message = "fire-alarm-2"

        self.servant = Mimic(Spy, infosystem.LoudSpeakerManager)
        self.proxy = self._adapter_add(LoudSpeakerManagerI(self.servant))
        self._subscribe(self.topic_name, self.proxy)

    def test_publish_sayInPlace_event(self):
        transducer_type = "SpeakerManager"

        p = self.broker.get_publisher(self.source, transducer_type)
        p.subscribe(self.proxy)
        p.sayInPlace(self.place, self.message)

        assert_that(self.servant.sayInPlace,
                    called().
                    with_args(self.place, self.message, anything()).
                    async_mode(timeout=2))

    def test_publish_sayInSpeaker_event(self):
        transducer_type = "SpeakerManager"

        p = self.broker.get_publisher(self.source, transducer_type)
        p.subscribe(self.proxy)
        p.sayInSpeaker(self.speaker, self.message)

        assert_that(self.servant.sayInSpeaker,
                    called().
                    with_args(self.speaker, self.message, anything()).
                    async_mode(timeout=2))
