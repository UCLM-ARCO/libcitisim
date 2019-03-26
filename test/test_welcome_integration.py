# -*- coding: utf-8; mode: python -*-

from unittest import TestCase
from doublex import assert_that, called, method_returning, Stub
from hamcrest import anything

from utils import AnalogEventsMixin


class WelcomeAndPublisherIntegration(AnalogEventsMixin, TestCase):
    def setUp(self):
        AnalogEventsMixin.setUp(self)

        with Stub() as self.welcome:
            self.welcome.hello = method_returning(None)
        self.broker.welcome_server = self.welcome

    def test_get_publisher_calls_hello_on_welcome_server(self):
        source = "TestSource"
        type_ =  "LightSensor"
        p = self.broker.get_publisher(source=source, transducer_type=type_)

        assert_that(
            self.welcome.hello,
            called().with_args(anything(), type_).async(timeout=2))

