#!/usr/bin/env python
"""
Perform gitosis actions for a git hook.
"""

import errno
import logging
import sys
import shutil

from os import rename, path, umask, environ

from gitosis import git
from gitosis import ssh
from gitosis import gitweb
from gitosis import gitdaemon
from gitosis import app
from gitosis import util

log = logging.getLogger('gitosis.run_hook')

def post_update(git_dir, generated_files, authorized_keys):
    export = path.join(git_dir, 'gitosis-export')

    try:
        shutil.rmtree(export)
    except OSError, e:
        if e.errno == errno.ENOENT:
            pass
        else:
            raise

    git.export(git_dir=git_dir, path=export)

    rename(
        path.join(export, 'gitosis.conf'),
        path.join(export, '..', 'gitosis.conf'),
        )

    repo_dir = config.repositories_dir()
    repositories = config.get_repositories()
    gitweb_enabled = config.getweb_enabled()
    daemon_enabled = config.daemon_enabled()

    gitweb.set_descriptions(repositories)
    if gitweb_enabled:
        gitweb.write_project_list(path.join(generated_files, 'projects.list'))

    if daemon_enabled:
        gitdaemon.set_export_ok(repo_dir)

    ssh.writeAuthorizedKeys(authorized_keys, path.join(export, 'keydir'))

class RunHook(app.App):
    def create_parser(self):
        parser = super(RunHook, self).create_parser()
        parser.set_usage('%prog [OPTS] HOOK')
        parser.set_description('Perform gitosis actions for a git hook')
        return parser

    def handle_args(self, parser, cfg, options, args):
        try:
            (hook,) = args
        except ValueError:
            parser.error('Missing argument HOOK.')

        umask(0022)

        git_dir = environ.get('GIT_DIR')

        if git_dir is None:
            log.error('Must have GIT_DIR set in enviroment')
            sys.exit(1)

        if hook == 'post-update':
            log.info('Running hook %s', hook)
            post_update(cfg, git_dir)
            log.info('Done.')
        else:
            log.warning('Ignoring unknown hook: %r', hook)

if __name__ == "__main__":
    RunHook().run()
