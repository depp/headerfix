#!/usr/bin/env python
# Header Fixer - header.py
# Copyright 2007 - 2009 Dietrich Epp <depp@zdome.net>
# This source code is licensed under the GNU General Public License,
# Version 3. See gpl-3.0.txt for details.
import fixheader

class MyHeaderFixer(fixheader.HeaderFixer):
    PROJECT_NAME = "Header Fixer"
    AUTHOR = "Dietrich Epp <depp@zdome.net>"
    EXCLUDE = set(['build', 'setup.py'])
    HEADER_SUFFIX = [
        'This source code is licensed under the GNU General Public License,',
        'Version 3. See gpl-3.0.txt for details.'
        ]

MyHeaderFixer().run()
