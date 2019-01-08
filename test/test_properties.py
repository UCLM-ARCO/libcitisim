# -*- coding: utf-8; mode: python -*-

from time import time
import Ice
import json
from doublex import assert_that, method_returning
from hamcrest import calling, raises, equal_to
from unittest import TestCase

import libcitisim
from utils import PropertyMixin


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
            print(sut.topic_manager)
        except ValueError:
            self.fail("Default 'TopicManager.Proxy' property not set")
        except Ice.NoEndpointException:
            pass
