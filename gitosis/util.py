from __future__ import with_statement
import errno
import os
import ConfigParser

class CannotReadConfigError(Exception):
    """Unable to read config file"""

    def __str__(self):
        return '%s: %s' % (self.__doc__, ': '.join(self.args))

class ConfigFileDoesNotExistError(CannotReadConfigError):
    """Configuration does not exist"""

def mkdir(*a, **kw):
    try:
        os.mkdir(*a, **kw)
    except OSError, e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise

def getRepositoryDir(config):
    repositories = os.path.expanduser('~')
    try:
        path = config.get('gitosis', 'repositories')
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        repositories = os.path.join(repositories, 'repositories')
    else:
        repositories = os.path.join(repositories, path)
    return repositories

def getGeneratedFilesDir(config):
    try:
        generated = config.get('gitosis', 'generate-files-in')
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        generated = os.path.expanduser('~/gitosis')
    return generated

def getSSHAuthorizedKeysPath(config):
    try:
        path = config.get('gitosis', 'ssh-authorized-keys-path')
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        path = os.path.expanduser('~/.ssh/authorized_keys')
    return path

def read_config(file_name):
    cfg = ConfigParser.RawConfigParser()

    try:
        with open(os.path.expanduser(file_name)) as f:
            cfg.readfp(f)
    except (IOError, OSError), e:
        if e.errno == errno.ENOENT:
            raise ConfigFileDoesNotExistError(str(e))
        else:
            raise CannotReadConfigError(str(e))
    return cfg
