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
