import os
import stat
from . import rule

def scan_dir(rules, path):
    try:
        fp = open(os.path.join(path, '.header'))
    except IOError:
        pass
    else:
        with fp:
            nrules = rule.Rules.read(fp)
        rules = rules.union(nrules)

    fnames = os.listdir(path)
    files = []
    dirs = []
    for fname in fnames:
        st = os.lstat(os.path.join(path, fname))
        if stat.S_ISREG(st.st_mode):
            files.append(fname)
        elif stat.S_ISDIR(st.st_mode):
            dirs.append(fname)

    for fname in files:
        env = rules.file_env(fname)
        if env is None:
            continue
        print os.path.join(path, fname)

    for fname in dirs:
        drules = rules.dir_rules(fname)
        if drules is None:
            continue
        fpath = os.path.join(path, fname)
        if os.path.exists(os.path.join(fpath, '.git')):
            continue
        scan_dir(drules, fpath)
