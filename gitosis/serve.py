#!/usr/bin/env python
"""
Enforce git-shell to only serve allowed by access control policy.
directory. The client should refer to them without any extra directory
prefix. Repository names are forced to match ALLOW_RE.
"""

import logging

from os import path, umask, fork, environ, sep, execvp, wait
from sys import exit
from re import compile

from gitosis import access
from gitosis import git
from gitosis import gitweb
from gitosis import gitdaemon
from gitosis import util

from gitosis.app import App

import simplejson as json 

log = logging.getLogger('gitosis.serve')

ALLOW_RE = compile("^'/*(?P<path>[a-zA-Z0-9][a-zA-Z0-9@._-]*(/[a-zA-Z0-9][a-zA-Z0-9@._-]*)*)'$")

COMMANDS_READONLY = [
    'git-upload-pack',
    'git upload-pack',
    ]

COMMANDS_WRITE = [
    'git-receive-pack',
    'git receive-pack',
    ]

class ServingError(Exception):
    """Serving error"""

    def __str__(self):
        return '%s' % self.__doc__

class CommandMayNotContainNewlineError(ServingError):
    """Command may not contain newline"""

class UnknownCommandError(ServingError):
    """Unknown command denied"""

class UnsafeArgumentsError(ServingError):
    """Arguments to command look dangerous"""

class AccessDenied(ServingError):
    """Access denied to repository"""

class WriteAccessDenied(AccessDenied):
    """Repository write access denied"""

class ReadAccessDenied(AccessDenied):
    """Repository read access denied"""



def repository_path( cfg, user, command ):
    try:
        verb, args = command.split(None, 1)
    except ValueError:
        # all known "git-foo" commands take one argument; improve
        # if/when needed
        raise UnknownCommandError()
    if verb == 'git':
        try:
            subverb, args = args.split(None, 1)
        except ValueError:
            # all known "git foo" commands take one argument; improve
            # if/when needed
            raise UnknownCommandError()
        verb = '%s %s' % (verb, subverb)

    match = ALLOW_RE.match(args)

    if match is None:
        raise UnsafeArgumentsError()

    path = match.group('path')
    return path

## determines if we should send a message or not
def should_send_message( cfg, user, command ):
    if '\n' in command:
        raise CommandMayNotContainNewlineError()
    try:
        verb, args = command.split(None, 1)
    except ValueError:
        # all known "git-foo" commands take one argument; improve
        # if/when needed
        raise UnknownCommandError()

    ## only send the message if we have use_amqp set in the config file...
    if not cfg.getboolean("amqp", "use_amqp"):
        return False

    if verb == 'git':
        try:
            subverb, args = args.split(None, 1)
        except ValueError:
            # all known "git foo" commands take one argument; improve
            # if/when needed
            raise UnknownCommandError()
        verb = '%s %s' % (verb, subverb)

    match = ALLOW_RE.match(args)
    if match is None:
        raise UnsafeArgumentsError()
    path = match.group('path')

    if ( verb in COMMANDS_WRITE ):
        return True
    else:
        return False


def serve(cfg, user, command):
    if '\n' in command:
        raise CommandMayNotContainNewlineError()

    try:
        verb, args = command.split(None, 1)
    except ValueError:
        # all known "git-foo" commands take one argument; improve
        # if/when needed
        raise UnknownCommandError()

    if verb == 'git':
        try:
            subverb, args = args.split(None, 1)
        except ValueError:
            # all known "git foo" commands take one argument; improve
            # if/when needed
            raise UnknownCommandError()
        verb = '%s %s' % (verb, subverb)

    if (verb not in COMMANDS_WRITE
        and verb not in COMMANDS_READONLY):
        raise UnknownCommandError()

    match = ALLOW_RE.match(args)
    if match is None:
        raise UnsafeArgumentsError()

    path = match.group('path')

    # write access is always sufficient
    newpath = access.haveAccess(
        config=cfg,
        user=user,
        mode='writable',
        path=path)

    if newpath is None:
        # didn't have write access; try once more with the popular
        # misspelling
        newpath = access.haveAccess(
            config=cfg,
            user=user,
            mode='writeable',
            path=path)
        if newpath is not None:
            log.warning(
                'Repository %r config has typo "writeable", '
                +'should be "writable"',
                path,
                )

    if newpath is None:
        # didn't have write access

        newpath = access.haveAccess(
            config=cfg,
            user=user,
            mode='readonly',
            path=path)

        if newpath is None:
            raise ReadAccessDenied()

        if verb in COMMANDS_WRITE:
            # didn't have write access and tried to write
            raise WriteAccessDenied()

    (topdir, relpath) = newpath
    assert not relpath.endswith('.git'), \
           'git extension should have been stripped: %r' % relpath
    repopath = '%s.git' % relpath
    fullpath = path.join(topdir, repopath)
    if (not path.exists(fullpath)
        and verb in COMMANDS_WRITE):
        # it doesn't exist on the filesystem, but the configuration
        # refers to it, we're serving a write request, and the user is
        # authorized to do that: create the repository on the fly

        # create leading directories
        p = topdir
        for segment in repopath.split(sep)[:-1]:
            p = path.join(p, segment)
            util.mkdir(p, 0750)

        git.init(path=fullpath)
        gitweb.set_descriptions(config=cfg)
        generated = util.getGeneratedFilesDir(config=cfg)
        gitweb.write_project_list(cfg,
            path.join(generated, 'projects.list')
            )
        gitdaemon.set_export_ok(cfg)

    # put the verb back together with the new path
    newcmd = "%(verb)s '%(path)s'" % dict(
        verb=verb,
        path=fullpath,
        )
    return newcmd


class Serve(App):
    def create_parser(self):
        parser = super(Serve, self).create_parser()
        parser.set_usage('%prog [OPTS] USER')
        parser.set_description(
            'Allow restricted git operations under DIR')
        return parser

    def handle_args(self, parser, cfg, options, args):
        try:
            (user,) = args
        except ValueError:
            parser.error('Missing argument USER.')

        main_log = logging.getLogger('gitosis.serve.main')
        umask(0022)

        cmd = environ.get('SSH_ORIGINAL_COMMAND', None)

        if cmd is None:
            main_log.error('Need SSH_ORIGINAL_COMMAND in environment.')
            exit(1)

        main_log.debug('Got command %r' % cmd)

        chdir(path.expanduser('~'))

        try:
            newcmd = serve(
                cfg=cfg,
                user=user,
                command=cmd,
                )
        except ServingError, e:
            main_log.error('%s', e)
            exit(1)

        ## if we are writing then we need to 

        main_log.debug('Serving %s', newcmd)
        pid = fork()
        if not pid:
            execvp('git', ['git', 'shell', '-c', newcmd])
            main_log.error('Cannot execute git-shell.')
            exit(1)
        else:
            wait()
            try:
                if (should_send_message( cfg=cfg, user=user, command=cmd )):
                    send_amqp_message(data={'repository': repository_path(cfg=cfg, user=user, command=cmd)}, **amqp_config(cfg))
            except ServingError, e:
                main_log.error('%s', e)
                exit(1)

if __name__ == "__main__":
    
