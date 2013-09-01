# Copyright 2013 Dietrich Epp.
#
# This file is part of HeaderFix.  HeaderFix is distributed under the terms of
# the 2-clause BSD license.  See LICENSE.txt for details.

import subprocess
from . import util
import sys

COLORDIFF = None

def show_diff(diff):
    global COLORDIFF
    if COLORDIFF is None:
        colordiff = util.find_executable('colordiff')
        if colordiff is None:
            COLORDIFF = False
        else:
            COLORDIFF = colordiff
    if COLORDIFF:
        proc = subprocess.Popen(
            [COLORDIFF],
            stdin=subprocess.PIPE)
        proc.communicate(diff)
    else:
        sys.stdout.write(diff)
