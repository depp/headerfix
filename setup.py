#! /usr/bin/env python3.0
bytes # There is a better way to do this, but this breaks pre-3.0 Python
from distutils.core import setup
setup(name='Fixheader',
      version='1.0',
      description='Source code header fixer',
      author='Dietrich Epp',
      author_email='depp@zdome.net',
      py_modules=['fixheader'])
