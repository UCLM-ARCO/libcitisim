# -*- coding: utf-8; mode: python -*-

import Ice
from unittest import TestCase
from doublex import Mimic, Spy

from libcitisim import MetadataHelper, MetadataField, SmartObject


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

    def test_wrong_keys(self):
        meta = MetadataHelper().to_dict()
        meta[100] = 1
        MetadataHelper.from_metadata(meta)


class EventSinkI(SmartObject.EventSink):
    def __init__(self, servant):
        self.servant = servant

    def notify(self, *args, **kwargs):
        self.servant.notify(*args, **kwargs)


class MetadataHelperMarshallTests(TestCase):
    def setUp(self):
        self.broker = Ice.initialize()
        self.adapter = self.broker.createObjectAdapterWithEndpoints(
            'adapter', 'tcp')
        self.adapter.activate()

    def tearDown(self):
        self.broker.destroy()

    def adapter_add(self, cast, servant):
        proxy = self.adapter.addWithUUID(EventSinkI(servant))
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