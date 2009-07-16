import errno
import logging
from os import path, remove

from ConfigParser import NoSectionError, NoOptionError

log = logging.getLogger('gitosis.gitdaemon')

from gitosis import util

def export_ok_path(repopath):
    p = os.path.join(repopath, 'git-daemon-export-ok')
    return p

def allow_export(repopath):
    p = export_ok_path(repopath)
    # creates the damn file
    file(p, 'w').close()

def deny_export(repopath):
    p = export_ok_path(repopath)
    remove(p)

def reldir(topdir, dirpath):
    if topdir == dirpath:
        return '.'
    prefix = topdir + '/'
    assert dirpath.startswith(prefix)
    reldir = dirpath[len(prefix):]
    return reldir

def set_export_ok(repo_dir, repositories):
    def _error(e):
        if e.errno == errno.ENOENT:
            pass
        else:
            raise e

    for (dirpath, dirnames, filenames) in os.walk(repo_dir, onerror=_error):
        # oh how many times i have wished for os.walk to report
        # topdir and reldir separately, instead of dirpath
        relative = reldir(repo_dir, dirpath)

        log.debug('Walking %r, seeing %r', relative, dirnames)

        to_recurse = []
        repos = []

        for dirname in dirnames:
            if dirname.endswith('.git'):
                repos.append(dirname)
            else:
                to_recurse.append(dirname)

        dirnames[:] = to_recurse

        for repo in repos:
            name, ext = os.path.splitext(repo)
            if relative != '.':
                name = os.path.join(relative, name)

            try:
                enable = config.getboolean('repo %s' % name, 'daemon')
            except (NoSectionError, NoOptionError):
                enable = global_enable

            if enable:
                log.debug('Allow %r', name)
                allow_export(os.path.join(dirpath, repo))
            else:
                log.debug('Deny %r', name)
                deny_export(os.path.join(dirpath, repo))
