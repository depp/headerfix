# Copyright 2013 Dietrich Epp.
#
# This file is part of HeaderFix.  HeaderFix is distributed under the terms of
# the 2-clause BSD license.  See LICENSE.txt for details.

import collections
import os

Filetype = collections.namedtuple(
    'Filetype', 'name exts linecomment blockcomment')

EXTS = {}
FILETYPES = {}

def _filetype(name, exts, linecomment, blockcomment):
    exts = tuple(exts.split())
    assert exts
    if blockcomment is not None:
        blockcomment = tuple(blockcomment.split())
        assert len(blockcomment) == 2
    val = Filetype(name, exts, linecomment, blockcomment)
    for ext in exts:
        assert ext not in EXTS
        EXTS[ext] = val
    FILETYPES[name] = val

UNKNOWN = Filetype('unknown', (), None, None)

_filetype('h', '.h', '//', '/* */')
_filetype('hxx', '.hpp .hxx', '//', '/* */')
_filetype('c', '.c', '//', '/* */')
_filetype('cxx', '.cp .cpp .cxx', '//', '/* */')
_filetype('objc', '.m', '//', '/* */')
_filetype('python', '.py', '#', None)
_filetype('shell', '.sh', '#', None)
_filetype('xml', '.xml', None, '<!-- -->')
_filetype('text', '.txt', None, None)

def get_filetype(path):
    return EXTS.get(os.path.splitext(path)[1], UNKNOWN)
