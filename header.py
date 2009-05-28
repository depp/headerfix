#! /usr/bin/env python3.0
# Header Fixer - header.py
# Copyright 2007 - 2009 Dietrich Epp <depp@zdome.net>
# This source code is licensed under the GNU General Public License,
# Version 3. See gpl-3.0.txt for details.
import fixheader

LICENSE = [
    'This source code is licensed under the GNU General Public License,',
    'Version 3. See gpl-3.0.txt for details.'
]

EXCLUDE = set(['build', 'setup.py'])

class MyHeaderFixer(fixheader.HeaderFixer):
    def filter_path(self, path, isdir):
        if path in EXCLUDE:
            return False
        return super(MyHeaderFixer, self).filter_path(path, isdir)
    def project_name(self, path):
        return "Header Fixer"
    def project_author(self, path):
        return "Dietrich Epp <depp@zdome.net>"
    def header_suffix(self, path):
        return LICENSE

MyHeaderFixer().run()
