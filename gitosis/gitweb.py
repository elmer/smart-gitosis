"""
Generate ``gitweb`` project list based on ``gitosis.conf``.

To plug this into ``gitweb``, you have two choices.

- The global way, edit ``/etc/gitweb.conf`` to say::

	$projects_list = "/path/to/your/projects.list";

  Note that there can be only one such use of gitweb.

- The local way, create a new config file::

	do "/etc/gitweb.conf" if -e "/etc/gitweb.conf";
	$projects_list = "/path/to/your/projects.list";
        # see ``repositories`` in the ``gitosis`` section
        # of ``~/.gitosis.conf``; usually ``~/repositories``
        # but you need to expand the tilde here
	$projectroot = "/path/to/your/repositories";

   Then in your web server, set environment variable ``GITWEB_CONFIG``
   to point to this file.

   This way allows you have multiple separate uses of ``gitweb``, and
   isolates the changes a bit more nicely. Recommended.
"""
from __future__ import with_statement 
import urllib, logging
from os import path, getpid, rename

from ConfigParser import NoSectionError, NoOptionError

from gitosis import util

class Repository(object):
    def __init__(self, name, owner=None):
        self.name = name
        self.owner = owner

    def __str__(self):
        return "%s %s" % (self.name, self.owner)
        

def _escape_filename(s):
    s = s.replace('\\', '\\\\')
    s = s.replace('$', '\\$')
    s = s.replace('"', '\\"')
    return s

def get_repositories(config):
    repositories = []

    for section in config.sections():
        header = section.split(None, 1)

        if not header or header[0] != 'repo':
            continue

        repo = Repository(" ".join(header[1:]))

        try:
            owner = config.get(section, 'owner')
        except (NoSectionError, NoOptionError):
            pass
        else:
            repo.owner = owner

        repositories.append(repo)
    return repositories
    

def filter_repositories(repo_dir, config_repos):
    """
    This function takes a repository directory and a list of repositories
    built from gitosis.conf and filters them based on the existence
    of the repository in the directory
    """
    filtered_repos = []
    for repo in config_repos:
        if path.exists(path.join(repo_dir, repo.name)) or \
           path.exists(path.join(repo_dir, "%s.git" % repo.name)):
            filtered_repos.append(repo)
        else:
            log.warning(
                'Cannot find %(name)r in %(repo_dir)r'
                % dict(name=repo.name, repo_dir=repo_dir))
    return filtered_repos

def generate_project_list(config):
    """
    Generate projects list for ``gitweb``.

    :param config: configuration to read projects from
    :type config: RawConfigParser

    :param fp: writable for ``projects.list``
    :type fp: (file-like, anything with ``.write(data)``)
    """
    log = logging.getLogger('gitosis.gitweb.generate_projects_list')

    repo_dir = util.getRepositoryDir(config)

    try:
        global_enable = config.getboolean('gitosis', 'gitweb')
    except (NoSectionError, NoOptionError):
        global_enable = False

    repositories = filter_repositories(repo_dir, get_repositories(config))

    out = []

    for repo in repositories:
        try:
            enable = config.getboolean("repo " + repo.name, 'gitweb')
        except (NoSectionError, NoOptionError):
            enable = global_enable

        try:
            enable = config.getboolean("repo " + repo.name, 'gitweb')
        except (NoSectionError, NoOptionError):
            enable = global_enable

        if not enable:
            continue

        out.append(urllib.quote_plus(str(repo)))
    return out

def write_project_list(config, path):
    """
    Generate projects list for ``gitweb``.

    :param config: configuration to read projects from
    :type config: RawConfigParser

    :param path: path to write projects list to
    :type path: str
    """
    tmp = '%s.%d.tmp' % (path, getpid())

    with open(tmp, 'w') as f:
        f.writelines(generate_project_list(config))
    rename(tmp, path)


def set_descriptions(config):
    """
    Set descriptions for gitweb use.
    """
    log = logging.getLogger('gitosis.gitweb.set_descriptions')

    repositories = util.getRepositoryDir(config)

    for section in config.sections():
        l = section.split(None, 1)
        type_ = l.pop(0)
        if type_ != 'repo':
            continue
        if not l:
            continue

        try:
            description = config.get(section, 'description')
        except (NoSectionError, NoOptionError):
            continue

        if not description:
            continue

        name, = l

        if not path.exists(path.join(repositories, name)):
            namedotgit = '%s.git' % name
            if path.exists(path.join(repositories, namedotgit)):
                name = namedotgit
            else:
                log.warning(
                    'Cannot find %(name)r in %(repositories)r'
                    % dict(name=name, repositories=repositories))
                continue

        path = path.join(
            repositories,
            name,
            'description',
            )
        tmp = '%s.%d.tmp' % (path, getpid())
        f = file(tmp, 'w')
        try:
            print >>f, description
        finally:
            f.close()
        rename(tmp, path)
