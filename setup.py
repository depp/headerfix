#! /usr/bin/env python3.0
import platform
import sys
if platform.python_version_tuple()[0] != '3':
    sys.stderr.write("Needs version 3 of Python.\n")
    sys.exit(1)
from distutils.core import setup
setup(name='Fixheader',
      version='1.0',
      description='Source code header fixer',
      author='Dietrich Epp',
      author_email='depp@zdome.net',
      py_modules=['fixheader'])
