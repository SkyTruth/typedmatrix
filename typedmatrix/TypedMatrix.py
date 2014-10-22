"""
TypedMatrix.py - read/write TypedMatrix format
"""
import StringIO
import struct
import json
import calendar
from datetime import datetime

# Header Structure
# {
#   length: count of rows of data
#   cols: array of column definitions
#       [{}
#       ]
# }

magic = 'tmtx'
version = 1
typemap = {
    int: 'Float32',
    float: 'Float32',
    datetime: 'Float32',
}
typeformatmap = {
    'Float32': 'f',
}
typedefaultmap = {
    'Float32': 0.0,
}
#orientation_map = {
#    'rowwise': 'r',
#    'columnwise': 'c'
#}
#orientation_unpack_map = {v: k for k, v in orientation_map.items()}


def get_columns(data):
    """
    Gets the column definitions implicit in a dict or list of dicts.
    If any field which has a datatype that is not in typemap, thows TypeException
    """
    # make data iterable
    if type(data) is dict:
        data = [data]

    cols = {}
    for i, d in enumerate(data):
        for key, value in d.iteritems():
            t = type(value)
            if t not in typemap:
                raise TypeError ('TypedMatrix: "%s" is not a supported type in field "%s"' % (type(value), key))
            if key not in cols:
                cols[key] = {'name': key, 'type': typemap[t]}
    cols = cols.values()
    cols.sort(lambda a, b: cmp(a['name'], b['name']))
    return cols


def _datetime2timestamp(dt):
    return calendar.timegm(dt.utctimetuple()) * 1000.0


def conv(data, t, default):
    if 'Float32' == t:
        if type(data) is datetime:
            fn = _datetime2timestamp
        else:
            fn = float
    else:
        assert False, 'Unknown conversion type %s' % t

    # noinspection PyBroadException
    try:
        return fn(data)
    except:
        return default


def row_fmt(columns):
    return '<' + ''.join(typeformatmap[col['type']] for col in columns)


def pack(data, extra_header_fields=None, columns=None, orientation='rowwise'):
    """
    Pack a dict or list of dicts into a TypedMatrix binary packed string
    If a list of columns is not given, the columns are derived from the data using get_columns()
    extra_header_fields can supply an optional dict with additional fields to be included in the packed header

    orientation can be 'rowwise' or 'columnwise'.   For row-wise orientation, the typedmatrix will stored as a list of rows.
    for column-wise oreintation it is stored as a list of columns.
    """

    # make data iterable
    if type(data) is dict:
        data = [data]

    header = dict(orientation=orientation, version=version)
    if extra_header_fields:
        header.update(extra_header_fields)

    header['length'] = len(data)
    if not columns:
        columns = get_columns(data)
    header['cols'] = columns

    if 'colsByName' in header:
        colsByName = header.pop("colsByName")
        for col in header['cols']:
            if col['name'] in colsByName:
                col.update(colsByName[col['name']])

    f = StringIO.StringIO()
    headerstr = json.dumps(header)

    # Add padding so that the header length is a muliple of 4 bytes.  This keeps all the following data
    # on 4-byte boundaries
    headerstr += ' ' * ((4 - len(headerstr) % 4) % 4)

    # write "magic" file format token at the start
    f.write(struct.pack('<%sc' % len(magic), *magic))
    # write lenght of json header string
    f.write(struct.pack("<i", len(headerstr)))
    # write the header string
    f.write(headerstr)

    colspecs = [{'name': col['name'], 'type': col['type'], 'default': typedefaultmap[col['type']]} for col in columns]

    if orientation == 'rowwise':
        for d in data:
            f.write(struct.pack(
                row_fmt(columns),
                *[conv(d[colspec['name']], colspec['type'], colspec['default'])
                  for colspec in colspecs]))
    elif orientation == 'columnwise':
        for colspec in colspecs:
            f.write(struct.pack(
                '<%s%s' % (len(data),typeformatmap[colspec['type']]),
                *[conv(d[colspec['name']], colspec['type'], colspec['default'])
                  for d in data]))
    else:
        raise ValueError ('TypedMatrix: unknown orientation %s' % orientation)

    return f.getvalue()


def _struct_read (f, t, n=1):
    fmt = '<%s%s' % (n, t)
    result = struct.unpack(fmt, f.read(struct.calcsize(fmt)))
    if n == 1:
        return result[0]
    return result


def unpack(packed_str):
    """
    Unpack a binary packed string containing a TypedMatrix.   Returns a tuple of header and data
    header is a dict and data is a list of dicts
    """
    f = StringIO.StringIO(packed_str)

    # read "magic" file format token
    token = ''.join(_struct_read(f, 'c', len(magic)))
    assert(token == magic)

    header_len = _struct_read(f,'i')
    header = json.loads(f.read(header_len))
    orientation = header.get('orientation')
    assert(header.get('version') == version)    # only supports one version right now
    if orientation == 'rowwise':
        fmt = row_fmt(header['cols'])
        data = []
        col_names = [col['name'] for col in header['cols']]
        for i in range(0, header['length']):
            data.append(dict(zip(col_names, struct.unpack(fmt, f.read(struct.calcsize(fmt))))))
    elif orientation == 'columnwise':
        col_data = []
        col_names = [col['name'] for col in header['cols']]
        length = header['length']
        for col in header['cols']:
            col_data.append(_struct_read(f, typeformatmap[col['type']], length))
        col_indexes = range(0, len(col_names))
        if length > 1:
            data = [dict(zip(col_names, [col_data[c][i] for c in col_indexes])) for i in xrange(0, length)]
        elif length == 1:
            data = [dict(zip(col_names, [col_data[c] for c in col_indexes]))]
        else:
            data = []
    else:
        raise ValueError ('TypedMatrix: unknown orientation %s' % orientation)

    return header, data


def get_packed_float_value(f):
    """
    Get a float value that has been packed using Float32.   This is useful to get the actual precision used
    in the packed array for a float column, since Float32 precision is limited to about 9 digits and
    there is no native Float32 in python.
    """
    return struct.unpack('<f', struct.pack("<f", float(f)))[0]


def get_utc_timestamp(dt=datetime.now()):
    """
    Create a timestamp in milliseconds as a Float32 from a datetime
    """
    return get_packed_float_value(_datetime2timestamp(dt))
