from __future__ import with_statement

from ConfigParser import RawConfigParser, SafeConfigParser, NoSectionError, NoOptionError

from os import path

import logging

class ConfigSection(object):
    section_prefix = ""

    def section_name(self):
        return section_prefix + self.name

    @classmethod
    def _filter(cls, section):
        return section.startswith(cls.section_prefix)


class Group(ConfigSection):
    section_prefix = "group "

    def __init__(self, name, members=[]):
        self.name = name
        self.members = members

        if "@all" in members:
            self.all = True
        else:
            self.all = False

    @classmethod
    def member_of(cls, user, groups):
        [g for g in groups if group.is_member(user)]

    def is_member(self, user):
        return user in members or self.all
        

class Config(object):
    """
    captures the state and checks necessary to present a unified config object
    this prevents constant exception handling for missing sections or options
    and allows us more easily to remove dependencies on the config object
    itself.
    """
    defaults = {
                'repositories': "~/repositories",
                'ssh-authorized-keys-path': "~/.ssh/authorized_keys",
                'generated-files-in': "~/gitosis",
                'members': "",
                'logLevel': "debug",
                'gitweb': False,
                'daemon': False,
                'writable': "",
                'readonly': "",
               }

    def __init__(self, file_path=None):
        self.file_path = path.expanduser(file_path)
        self.config = None

        if self.file_path:
            self.read_config([self.file_path])

    def read_config(self, file_paths=[]):
        config = SafeConfigParser(self.defaults)
        if config.read(file_paths):
            self.config = config
            return self
        return False

    def get(self, section, option):
        return self.config.get(section, option)

    def set(self, section, option, value):
        return self.config.set(section, option, value)

    def repositories_dir(self):
        return path.expanduser(self.config.get("gitosis", "repositories"))

    def generated_files_dir(self):
        return path.expanduser(self.config.get("gitosis", "generated-file-in"))

    def ssh_authorized_keys_path(self):
        return path.expanduser(self.config.get("gitosis", "ssh-authorized-keys-path"))

    def amqp_config(self):
        return {
            'host': self.get("amqp", "host"),
            'user_id': self.get("amqp", "user_id"),
            'password': self.get("amqp", "password"),
            'ssl': self.config.getboolean("amqp", "ssl"),
            'exchange': self.get("amqp", "exchange"),
            }

    def filter_sections(self, f):
        return [s for s in self.config.sections() if f(s)]


    def groups(self):
        def build_group(s):
            name = s[len(Group.section_prefix):]
            members = self.config.get(s, 'members').split()
            modes = {'writable': self.config.get(s, 'writable').split(),
                     'readonly': self.config.get(s, 'readonly').split()}
            return Group(name, members, modes)

        return [build_group(s) for s in filter_sections(Group._filter)]

    def repositories(self):
        # insert check if the repository exists on disk here
        repo_dir = self.repositories_dir()

        def build_repos(s):
            name = Repository.exists(s[(Repository.section_prefix):], repo_dir)

            if name:
                owner = self.get(s, "owner")
                description = self.get(s, "description")
                gitweb = self.config.getboolean(s, "gitweb")
                daemon = self.config.getboolean(s, "daemon")
                return Repository(name, owner, gitweb, daemon, description)

         return [build_repos(s) for s in filter_sections(Repository._filter)]

    def log_level(self):
        level = self.get('gitosis', 'logLevel')
        if not logging._levelNames.has_key(level):
            raise InvalidConfig("logLevel %s does not exist" % level)
