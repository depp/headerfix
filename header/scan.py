import os
import stat
from . import rule

def scan_dir(rules, path, includes, excludes):
    try:
        fp = open(os.path.join(path, '.gitignore'))
    except IOError:
        pass
    else:
        with fp:
            nrules = rule.Rules.read_gitignore(fp)
        rules = rules.union(nrules)

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
        if includes is not None and not includes.match_file(fname):
            continue
        if excludes is not None and excludes.match_file(fname):
            continue
        env = rules.file_env(fname)
        if env is None:
            continue
        yield os.path.join(path, fname), env

    for fname in dirs:
        if includes is not None:
            match, dir_includes = includes.match_dir(fname)
            if match:
                dir_includes = None
            elif not dir_includes:
                continue
        else:
            dir_includes = None
        if excludes is not None:
            match, dir_excludes = excludes.match_dir(fname)
            if match:
                continue
            elif not dir_excludes:
                dir_excludes = None
        else:
            dir_excludes = None
        drules = rules.dir_rules(fname)
        if drules is None:
            continue
        fpath = os.path.join(path, fname)
        if os.path.exists(os.path.join(fpath, '.git')):
            continue
        for result in scan_dir(drules, fpath, dir_includes, dir_excludes):
            yield result
