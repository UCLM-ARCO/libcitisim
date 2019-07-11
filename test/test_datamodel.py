# -*- coding: utf-8; mode: python -*-

from unittest import TestCase
from libcitisim import datamodel


class TypeCastTests(TestCase):
    def test_str(self):
        sut = datamodel.TypeCast()
        self.assertEquals("hi", sut.apply("hi"))

    def test_bool(self):
        sut = datamodel.TypeCast(bool)
        self.assertEquals(False, sut.apply(0))
        self.assertEquals(False, sut.apply(False))
        self.assertEquals(False, sut.apply("False"))
        self.assertEquals(False, sut.apply("false"))
        self.assertEquals(True, sut.apply(1))
        self.assertEquals(True, sut.apply(True))
        self.assertEquals(True, sut.apply("True"))
        self.assertEquals(True, sut.apply("true"))

    def test_bool_fail(self):
        sut = datamodel.TypeCast(bool)
        wrong_booleans = ['']
        for value in wrong_booleans:
            with self.assertRaises(TypeError) as cm:
                sut.apply(value)

    def test_int(self):
        sut = datamodel.TypeCast(int)
        self.assertEquals(4, sut.apply(4))
        self.assertEquals(4, sut.apply("4"))

    def test_int_list_fail(self):
        sut = datamodel.TypeCast(int)
        with self.assertRaises(TypeError):
            self.assertEquals(4, sut.apply([1]))

    def test_unit(self):
        result = datamodel.properties['units'].apply('watts')
        self.assertEquals('watts', result)

    def test_unit_fail(self):
        with self.assertRaises(TypeError):
            datamodel.properties['units'].apply('wrong')

    def test_fixed_list(self):
        sut = datamodel.TypeCast(float, 2)
        expected = [2.1, 3.2]
        self.assertEquals(expected, sut.apply(expected))

    def test_fixed_list_wrong_len(self):
        sut = datamodel.TypeCast(float, 2)

        try:
            sut.apply([1, 2, 3])
            self.fail()
        except TypeError as e:
            msg = 'value len is 3, but it should be 2'
            self.assertEquals(msg, e.args[0])

    def test_int_range(self):
        sut = datamodel.TypeCast(datamodel.int_range(1, 20))
        self.assertEquals(3, sut.apply(3))
