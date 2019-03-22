# -*- coding: utf-8; mode: python -*-

from unittest import TestCase
from doublex import (
    assert_that, called, method_returning, method_raising, Mimic, Spy
)
from hamcrest import (
    calling, raises, is_not, anything, close_to, greater_than, equal_to
)

from utils import AnalogEventsMixin


class WelcomeAndPublisherIntegration(AnalogEventsMixin, TestCase):
    def setUp(self):
        AnalogEventsMixin.setUp(self)

    def test_publisher_calls_hello_on_welcome_server(self):
        source = "TestSource"
        type_ =  "LightSensor"
        p = self.broker.get_publisher(source, type_)

        assert_that(self.welcome.hello,
                    called().
                    with_args(anything(), type_, anything()).
                    async(timeout=2))

