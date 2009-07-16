import logging

from re import match
from sys import stderr
from os import path, environ 
from subprocess import call, Popen, PIPE

from gitosis.util import mkdir

log = logging.getLogger('gitosis.repository')


class GitError(Exception):
    """git failed"""

    def __str__(self):
        return '%s: %s' % (self.__doc__, ': '.join(self.args))

class GitInitError(Exception):
    """git init failed"""

class GitHasInitialCommitError(GitError):
    """Check for initial commit failed"""

class GitRevParseError(GitError):
    """rev-parse failed"""

class GitFastImportError(GitError):
    """git fast-import failed"""

class GitExportError(GitError):
    """Export failed"""

class GitReadTreeError(GitExportError):
    """git read-tree failed"""

class GitCheckoutIndexError(GitExportError):
    """git checkout-index failed"""


def init(path, template=None, _git=None):
    """
    Create a git repository at C{path} (if missing).

    Leading directories of C{path} must exist.

    @param path: Path of repository create.

    @type path: str

    @param template: Template directory, to pass to C{git init}.

    @type template: str
    """
    if _git is None:
        _git = 'git'

    mkdir(path, 0750)

    args = [ _git, '--git-dir=.', 'init', ]

    if template is not None:
        args.append('--template=%s' % template)

    returncode = call(
        args = args,
        cwd = path,
        stdout = stderr,
        close_fds = True,
        )

    if returncode != 0:
        raise GitInitError('exit status %d' % returncode)



def fast_import(git_dir, commit_msg, committer, files, parent=None):
    """
    Create an initial commit.
    """
    child = Popen(
        args=[
            'git',
            '--git-dir=.',
            'fast-import',
            '--quiet',
            '--date-format=now',
            ],
        cwd=git_dir,
        stdin=PIPE,
        close_fds=True,
        )
    files = list(files)

    for index, (path, content) in enumerate(files):
        child.stdin.write("""\
blob
mark :%(mark)d
data %(len)d
%(content)s
""" % { "mark": index+1,
        "len": len(content),
        "content": content }

    child.stdin.write("""\
commit refs/heads/master
committer %(committer)s now
data %(msg_len)d
%(msg)s
""" % { "committer": = committer,
        "msg_len": = len(commit_msg),
        "msg": = commit_msg }

    if parent is not None:
        assert not parent.startswith(':')
        child.stdin.write("from %ss" % parent)

    for index, (path, content) in enumerate(files):
        child.stdin.write('M 100644 :%d %s\n' % (index+1, path))

    child.stdin.close()

    returncode = child.wait()

    if returncode != 0:
        raise GitFastImportError(
            'git fast-import failed', 'exit status %d' % returncode)


def export(git_dir, path):
    mkdir(path)

    returncode = call(
        args=[
            'git',
            '--git-dir=%s' % git_dir,
            'read-tree',
            'HEAD',
            ],
        close_fds=True,
        )

    if returncode != 0:
        raise GitReadTreeError('exit status %d' % returncode)
    # jumping through hoops to be compatible with git versions
    # that don't have --work-tree=
    env = environ.copy() 
    env['GIT_WORK_TREE'] = '.'
    returncode = call(
        args=[
            'git',
            '--git-dir=%s' % path.abspath(git_dir),
            'checkout-index',
            '-a',
            '-f',
            ],
        cwd=path,
        close_fds=True,
        env=env,
        )

    if returncode != 0:
        raise GitCheckoutIndexError('exit status %d' % returncode)

def has_initial_commit(git_dir):
    child = Popen(
        args=[
            'git',
            '--git-dir=.',
            'rev-parse',
            'HEAD',
            ],
        cwd=git_dir,
        stdout=PIPE,
        close_fds=True,
        )

    got = child.stdout.read()
    log.debug("Has Initial Commit GOT: %s" % got)

    returncode = child.wait()
    if returncode != 0:
        raise GitRevParseError('exit status %d' % returncode)

    if got == 'HEAD\n':
        return False
    elif match('^[0-9a-f]{40}\n$', got):
        return True
    else:
        raise GitHasInitialCommitError('Unknown git HEAD: %r' % got)
