class Repository(ConfigSection):
    section_prefix = "repo "
    def __init__(self, name="", owner=None, gitweb=False, description="",
                       directory=""):
        self.name = name
        self.owner = owner
        self.gitweb = gitweb
        self.description = description
        self.directory = directory

    def from_config(self, config, section, directory=""):
        self.name = cls.exists(s[(Repository.section_prefix):], directory)

        if name:
            self.owner = config.get(s, "owner")
            self.description = config.get(s, "description")
            self.gitweb = config.getboolean(s, "gitweb")
            self.daemon = config.getboolean(s, "daemon")
            self.directory = directory
            return self
        return False

    def details(self):
        if self.owner:
            return [self.name, self.owner]
        else:
            return [self.name]

    def quoted_details(self):
        return " ".join([urllib.quote_plus(x) for x in self.details()])

    def path(self):
        path.join(self.directory, self.name)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return " ".join(self.details())

    @classmethod
    def exists(cls, name, dir=""):

        if path.exists(path.join(dir, name)):
            return name
        elif path.exists(path.join(dir, name+".git")):
            return name+".git"
        else
            return False
