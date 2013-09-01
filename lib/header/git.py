# Copyright 2013 Dietrich Epp.
#
# This file is part of HeaderFix.  HeaderFix is distributed under the terms of
# the 2-clause BSD license.  See LICENSE.txt for details.

import subprocess

def get_gitconfig(key, subkey, is_global=False):
    cmd = ['git', 'config', '--null']
    if is_global:
        cmd.append('--global')
    cmd.extend(['--get', '{}.{}'.format(key, subkey)])
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    out, err = proc.communicate()
    if proc.returncode:
        return None
    z = out.index('\0')
    return out[:z]
