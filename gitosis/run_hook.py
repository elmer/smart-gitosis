"""
Perform gitosis actions for a git hook.
"""

import errno
import logging
import os
import sys
import shutil
import ConfigParser

from gitosis import repository
from gitosis import ssh
from gitosis import gitweb
from gitosis import gitdaemon
from gitosis import app
from gitosis import util

def amqp_hook(config):
    use_amqp = config.getboolean("amqp", "use_amqp")

    if use_amqp:
        host = config.get("amqp", "host")
        user_id = config.get("amqp", "user_id")
        password = config.get("amqp", "password")
        ssl = config.getboolean("amqp", "ssl")
        exchange = config.get("amqp", "exchange")

        return send_amqp_message(host, user_id=user_id, password=password,
                                 ssl=ssl, exchange=exchange)
    return False

def send_amqp_message(host, user_id="guest", password="guest", ssl=True,
                      exchange="gitosis.post_update"):
    import amqplib.client_0_8 as amqp
    import simplejson as json 

    m = "git_repository_updated"

    log = logging.getLogger('gitosis.run_hook')
    log.info('Sending "%s" to: %s' % (m, exchange))

    msg = amqp.Message(m, content_type='text/plain')

    conn = amqp.Connection(host, userid=user_id, password=password, ssl=ssl,
                           exchange=exchange)
    ch = conn.channel()
    ch.access_request('/data', active=True, write=True)
    ch.exchange_declare(exchange, 'fanout', auto_delete=False, durable=True)
    ch.basic_publish(msg, exchange)
    ch.close()
    conn.close()
    return True

def post_update(cfg, git_dir):
    export = os.path.join(git_dir, 'gitosis-export')
    try:
        shutil.rmtree(export)
    except OSError, e:
        if e.errno == errno.ENOENT:
            pass
        else:
            raise
    repository.export(git_dir=git_dir, path=export)
    os.rename(
        os.path.join(export, 'gitosis.conf'),
        os.path.join(export, '..', 'gitosis.conf'),
        )
    # re-read config to get up-to-date settings
    cfg.read(os.path.join(export, '..', 'gitosis.conf'))
    
    #send a message to the amqp server that there's been an update
    amqp_hook(config=cfg)

    gitweb.set_descriptions(
        config=cfg,
        )
    generated = util.getGeneratedFilesDir(config=cfg)
    gitweb.generate_project_list(
        config=cfg,
        path=os.path.join(generated, 'projects.list'),
        )
    gitdaemon.set_export_ok(
        config=cfg,
        )
    authorized_keys = util.getSSHAuthorizedKeysPath(config=cfg)
    ssh.writeAuthorizedKeys(
        path=authorized_keys,
        keydir=os.path.join(export, 'keydir'),
        )

class Main(app.App):
    def create_parser(self):
        parser = super(Main, self).create_parser()
        parser.set_usage('%prog [OPTS] HOOK')
        parser.set_description(
            'Perform gitosis actions for a git hook')
        return parser

    def handle_args(self, parser, cfg, options, args):
        try:
            (hook,) = args
        except ValueError:
            parser.error('Missing argument HOOK.')

        log = logging.getLogger('gitosis.run_hook')
        os.umask(0022)

        git_dir = os.environ.get('GIT_DIR')
        if git_dir is None:
            log.error('Must have GIT_DIR set in enviroment')
            sys.exit(1)

        if hook == 'post-update':
            log.info('Running hook %s', hook)
            post_update(cfg, git_dir)
            log.info('Done.')
        else:
            log.warning('Ignoring unknown hook: %r', hook)
