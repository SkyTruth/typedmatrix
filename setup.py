#!/usr/bin/env python

from glob import glob
from os.path import sep
from distutils.core import setup

import typedmatrix

setup(name='typedmatrix',
      version=typedmatrix.__version__,
      author=typedmatrix.__author__,
      author_email='paul@skytruth.org',
      description=typedmatrix.__doc__,
      long_description=typedmatrix.__doc__,
      url=typedmatrix.__source__,
      license=typedmatrix.__license__,
      packages=['typedmatrix', 'typedmatrix.tests'])