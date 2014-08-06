TypedMatrix
===========

Typedmatrix is a binary coded format optimized for delivering large amounts of tabular data from a web server to a javascript client without the need to parse on the client

TypedMatrix Module
==================

Read and write typed-matrix formatted strings


Install
=======

TODO: Make this pip-installable

Test
====

Tests are built using unittest2 and can be executed using nose

    cd typedmatrix
    nosetests

TypedMatrix Format
==================

A TypedMatrix is a packed 2 dimensional array of typed values suitable for typecasting to a set of javascript arrays.

Currently two fundamental data types are supported
    Int32
    Float32

Special handling is provided for convertiong datetime values to Float32

The format includes a header containing a json object, which can contain arbitrary content.

The header must contain at least:

- length: indicated the number of rows in the data section
- cols: an array of column definitions.  The length of this array indicates the number of columns in each row

For example, a TypedMatrix with 2 rows and 3 columns:

    {'length': 2,
     'cols': [
        {'type': 'Float32', 'name': 'float'},
        {'type': 'Int32', 'name': 'int'},
        {'type': 'Float32', 'name': 'timestamp'}]
    }


Usage Examples
==============

    >>> from typedmatrix import TypedMatrix
    >>> from datetime import datetime
    >>> from pprint import pprint

    # create two rows of 3 columns each: int, float and datetime
    >>> data = [{'int':1, 'float':1.0, 'timestamp': datetime(2014,1,1)}]
    >>> data.append ({'int':2, 'float':2.0, 'timestamp':datetime(2014,1,2)})
    >>> t_str = TypedMatrix.pack(data)

    # Typedmatrix is now coded as a binary string
    >>> t_str
    'tmtx\x89\x00\x00\x00{"length": 2, "cols": [{"type": "Float32", "name": "float"}, {"type": "Int32", "name": "int"},
    {"type": "Float32", "name": "timestamp"}]}\x00\x00\x80?\x01\x00\x00\x00\x8d\xa5\xa1S\x00\x00\x00@\x02\x00\x00\x00
    \xa8\xa1S'
    >>> header, data = TypedMatrix.unpack(t)
    >>> pprint(header)
    {u'cols': [{u'name': u'float', u'type': u'Float32'},
               {u'name': u'int', u'type': u'Int32'},
               {u'name': u'timestamp', u'type': u'Float32'}],
     u'length': 2}
    >>> pprint(data)
    [{u'float': 1.0, u'int': 1, u'timestamp': 1388534431744.0},
     {u'float': 2.0, u'int': 2, u'timestamp': 1388620808192.0}]


Javascript example
------------------
see data-visualization-tools/js/app/Data/TypedMatrixParser.js
