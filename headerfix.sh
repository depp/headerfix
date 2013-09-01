#!/bin/sh
# Copyright 2013 Dietrich Epp.
#
# This file is part of HeaderFix.  HeaderFix is distributed under the terms of
# the 2-clause BSD license.  See LICENSE.txt for details.

dir=`dirname "$0"`
PYTHONPATH="$dir/lib:$PYTHONPATH" exec python -m header.tool "$@"
