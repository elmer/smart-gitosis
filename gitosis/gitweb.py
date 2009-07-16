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
    def __init__(self, name="", section="", owner=None, directory=""):
        self.name = name
        self.owner = owner
        self.section = section
        self.directory = directory

    def details(self):
        if self.owner:
            return [self.name, self.owner]
        else:
            return [self.name]

    def path(self):
        path.join(self.directory, self.name)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return " ".join(self.details())
        

def _escape_filename(s):
    s = s.replace('\\', '\\\\')
    s = s.replace('$', '\\$')
    s = s.replace('"', '\\"')
    return s

# This function needs a data structure such that
# we have a list of "sections" and each section
# has in it the section's owner
def get_repositories(config):
    repo_dir = util.getRepositoryDir(config)
    repositories = []

    for section in config.sections():
        header = section.split(None, 1)

        if not header or header[0] != 'repo':
            continue

        name = " ".join(header[1:])
        repo = Repository(name=name, section=section, directory=repo_dir)

        try:
            owner = config.get(section, 'owner')
        except (NoSectionError, NoOptionError):
            pass
        else:
            repo.owner = owner

        repositories.append(repo)
    return repositories

#def repository_exits(repo):
#    return path.exists(repo.path())
#
#def filter_repositories(repos):
#    [r for r in repos if repository_exits(r)]
    
def filter_repositories(repo_dir, config_repos):
    """
    This function takes a repository directory and a list of repositories
    built from gitosis.conf and filters them based on the existence
    of the repository in the directory
    """
    log = logging.getLogger('gitosis.gitweb.filter_repositories')
    filtered_repos = []
    for repo in config_repos:
        if repository_exits(repo):
            filtered_repos.append(repo)
        elif path.exists(path.join(repo_dir, "%s.git" % repo.name)):
            repo.name = "%s.git" % repo.name
            filtered_repos.append(repo)
        else:
            log.warning(
                'Cannot find %(name)r in %(repo_dir)r'
                % dict(name=repo.name, repo_dir=repo_dir))

    return filtered_repos

def generate_project_list(repo_dir):
    """
    Generate projects list for ``gitweb``.

    :param config: configuration to read projects from
    :type config: RawConfigParser
    """

    ##try:
    ##    global_enable = config.getboolean('gitosis', 'gitweb')
    ##except (NoSectionError, NoOptionError):
    ##    global_enable = False

    repositories = filter_repositories(repo_dir, get_repositories(config))

    return [r.quoted_details() for r in repositories if repo.gitweb)]

def write_project_list(repo_dir, to):
    """
    Generate projects list for ``gitweb``.

    :param repo_dir: the path to look for repositories
    :param to: path to write projects list to
    """
    with open(to, 'w') as f:
        f.write("\n".join(generate_project_list(repo_dir)))


def set_descriptions(repositories):
    """
    Set descriptions for gitweb use.
    """
    log = logging.getLogger('gitosis.gitweb.set_descriptions')

    for repo in repositories:
        if repo.description:
            p = path.join(repo.path(), "description")

            with open(p, 'w') as f:
                f.write(description)
