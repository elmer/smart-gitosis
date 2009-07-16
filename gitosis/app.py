from config import Config
from os import path
from optparse import OptionParser

import logging

class NotImplemented(Exception):
    pass

class App(object):
    name = None

    def __init__(self):
        self.parser = self.create_parser()
        self.config = Config(options.config)
        self.setup_logging()

    def run(self):
        (options, args) = parser.parse_args()
        self.handle_args(parser, options, args)

    def create_parser(self):
        parser = OptionParser()
        parser.set_defaults(
            config=path.expanduser('~/.gitosis.conf'),
            )
        parser.add_option('--config',
                          metavar='FILE',
                          help='read config from FILE',
                          )

        return parser

    def setup_logging(self):
        logging.basicConfig()
        log_level = self.config.log_level()
        symbolic = logging._levelNames[log_level]
        logging.root.setLevel(symbolic)

    def handle_args(self, parser, options, args):
        raise NotImplemented()
