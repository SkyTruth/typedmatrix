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

typemap = {
    int: 'Int32',
    float: 'Float32',
    datetime: 'Float32',
}
typeformatmap = {
    'Int32': 'i',
    'Float32': 'f',
}
typedefaultmap = {
    'Int32': 0,
    'Float32': 0.0,
}


def get_columns(data):
    """
    Gets the column definitions implicit in a dict or list of dicts.
    If any field which has a datatype that is not in typemap, thows ???
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
    if 'Int32' == t:
        assert type(data) is not datetime, 'Cannot convert datetime to int32.'
        fn = int
    elif 'Float32' == t:
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


def pack(data, extra_header_fields=None, columns=None):
    """
    Pack a dict or list of dicts into a TypedMatrix binary packed string
    If a list of columns is not given, the columns are derived from the data using get_columns()
    extra_header_fields can supply an optional dict with additional fields to be included in the packed header
    """

    # make data iterable
    if type(data) is dict:
        data = [data]

    if extra_header_fields:
        header = dict(extra_header_fields)
    else:
        header = dict()

    header['length'] = len(data)
    if not columns:
        columns = get_columns(data)
    header['cols'] = columns

    f = StringIO.StringIO()
    headerstr = json.dumps(header)

    #TODO: #100 write "magic" file format token at the start
    # f.write("tmtx")

    f.write(struct.pack("<i", len(headerstr)))
    f.write(headerstr)

    formatmap = row_fmt(columns)
    #    inverse_typemap = {v: k for k, v in typemap.iteritems()}
    colspecs = [{'name': col['name'], 'type': col['type'], 'default': typedefaultmap[col['type']]} for col in columns]

    for d in data:
        f.write(struct.pack(
            formatmap,
            *[conv(d[colspec['name']], colspec['type'], colspec['default'])
              for colspec in colspecs]))

    return f.getvalue()


def unpack(packed_str):
    """
    Unpack a binary packed string containing a TypedMatrix.   Returns a tuple of header and data
    header is a dict and data is a list of dicts
    """
    f = StringIO.StringIO(packed_str)

    #TODO: #100 read "magic" file format token
    # token = f.read(4)
    # assert(token == 'tmtx')

    header_len = struct.unpack('<i', f.read(struct.calcsize('<i')))[0]
    header = json.loads(f.read(header_len))

    fmt = row_fmt(header['cols'])
    data = []
    col_names = [col['name'] for col in header['cols']]
    for i in range(0, header['length']):
        data.append(dict(zip(col_names, struct.unpack(fmt, f.read(struct.calcsize(fmt))))))

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
