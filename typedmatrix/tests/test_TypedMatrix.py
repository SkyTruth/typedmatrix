import unittest2
from .. import TypedMatrix
from datetime import datetime, timedelta


class TypedMatrixTest(unittest2.TestCase):
    def test_get_columns(self):
        data = {'A': 1}
        cols = TypedMatrix.get_columns(data)
        self.assertEqual(1, len(cols))
        self.assertEqual('A', cols[0]['name'])
        self.assertEqual('Float32', cols[0]['type'])

    def test_pack(self):
        data = {'A': 1}
        packed_str = TypedMatrix.pack(data)
        header, data = TypedMatrix.unpack(packed_str)
        self.assertEqual(1, header['length'])
        self.assertEqual(1, data[0]['A'])
        data = {'A': 1, 'B': 2}
        packed_str = TypedMatrix.pack(data)
        header, data = TypedMatrix.unpack(packed_str)
        self.assertEqual(1, header['length'])
        self.assertEqual(1, data[0]['A'])
        self.assertEqual(2, data[0]['B'])
        data = [{'A': 1, 'B': 2}, {'A': 11, 'B': 22}]
        packed_str = TypedMatrix.pack(data)
        header, data = TypedMatrix.unpack(packed_str)
        self.assertEqual(2, header['length'])
        self.assertEqual(1, data[0]['A'])
        self.assertEqual(22, data[1]['B'])

    def test_header(self):
        data = {'A': 1, 'B': 2}
        header = {'H': 'extra'}
        packed_str = TypedMatrix.pack(data, header)
        header, data = TypedMatrix.unpack(packed_str)
        self.assertEqual('extra', header['H'])
        packed_str = TypedMatrix.pack(data, extra_header_fields=header, orientation='columnwise')
        header, data = TypedMatrix.unpack(packed_str)
        self.assertEqual('extra', header['H'])

    def test_get_packed_float_value(self):
        self.assertEqual(TypedMatrix.get_packed_float_value(1.0), 1.0)
        self.assertEqual(TypedMatrix.get_packed_float_value(1234567890.0), 1234567936.0)

    def test_get_gmt_timestamp(self):
        self.assertEqual(TypedMatrix.get_utc_timestamp(datetime(2012, 1, 1)), 1325375946752.0)

    def test_datetime(self):
        data_in = dict(I=1, F=2.0, D=datetime(2014, 1, 1))
        data_out = data_in
        data_out['D'] = TypedMatrix.get_utc_timestamp(data_out['D'])

        packed_str = TypedMatrix.pack(data_in)
        header, data = TypedMatrix.unpack(packed_str)
        self.assertDictEqual(dict(name='D', type='Float32'), header['cols'][0])
        self.assertDictEqual(dict(name='F', type='Float32'), header['cols'][1])
        self.assertDictEqual(dict(name='I', type='Float32'), header['cols'][2])
        self.assertDictEqual(data[0], data_out)

    def test_unsupported_type(self):
        data_in = dict(I=1, F=2.0, D=datetime(2014, 1, 1), unsupported=timedelta(1))
        self.assertRaises(TypeError, TypedMatrix.pack, data_in)

    def test_bad_format(self):
        self.assertRaises(AssertionError, TypedMatrix.unpack, packed_str='not valid')

    def test_columnwise(self):
        data_in = [{'A': 1, 'B': 2}, {'A': 11, 'B': 22}, {'A': 111, 'B': 222}]
        packed_str = TypedMatrix.pack(data_in, orientation='columnwise')
        header, data_out = TypedMatrix.unpack(packed_str)
        self.assertEqual(3, header['length'])
        self.assertListEqual(data_in, data_out)

        data_in = [{'A': 1, 'B': 2}]
        packed_str = TypedMatrix.pack(data_in, orientation='columnwise')
        header, data_out = TypedMatrix.unpack(packed_str)
        self.assertEqual(1, header['length'])
        self.assertListEqual(data_in, data_out)

    def test_empty(self):
        data = []
        packed_str = TypedMatrix.pack(data)
        header, data = TypedMatrix.unpack(packed_str)
        self.assertEqual(0, header['length'])
        self.assertEqual(len(data), 0)

        packed_str = TypedMatrix.pack(data, orientation='columnwise')
        header, data = TypedMatrix.unpack(packed_str)
        self.assertEqual(0, header['length'])
        self.assertEqual(len(data), 0)
