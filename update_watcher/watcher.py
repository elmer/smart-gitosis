#!/usr/bin/env python

import sys
import amqplib.client_0_8 as amqp
import simplejson as json

from optparse import OptionParser
from gitosis.util import read_config
from os import path, mkdir, devnull
from subprocess import Popen

def call(cmd):
    p = Popen(cmd, stdout=open(devnull, 'w'))
    p.wait()
    return p.returncode

def update_or_create_repository(repository, projects_dir, git_user="git",
                                git_server="localhost"):
    project_path = path.join(projects_dir, repository)
    
    if path.exists(project_path):
        cmd = ["cd", project_path, "&&", "git", "pull"]
        print("Running %s" % cmd)
        return call(cmd)
    else:
        clone_uri = "%s@%s:%s" % (git_user, git_server, repository)
        cmd = ["git", "clone", clone_uri, project_path]
        print("Running %s" % cmd)
        return call(cmd)
        

def callback_wrapper(projects_dir, git_user, git_server):
    def callback(msg):
        print("Received: %s" % msg.body)
        data = json.loads(msg.body)
        repository = data['repository']
        update_or_create_repository(data['repository'], projects_dir, git_user, git_server)
    return callback
          
    
def main():
    parser = OptionParser()
    parser.add_option('--config', metavar='FILE', help='read config from FILE')
    options, args = parser.parse_args()

    config = read_config(options.config)

    host = config.get("amqp", "host")
    user_id = config.get("amqp", "user_id")
    password = config.get("amqp", "password")
    ssl = config.getboolean("amqp", "ssl")
    exchange = config.get("amqp", "exchange")
    projects_dir = config.get("rsp", "projects_dir")
    git_user = config.get("rsp", "git_user")
    git_server = config.get("rsp", "git_server")

    callback = callback_wrapper(projects_dir, git_user, git_server)

    conn = amqp.Connection(host, userid=user_id, password=password, ssl=ssl)
    print("Worker started")
    ch = conn.channel()
    ch.access_request('/data', active=True, read=True)
    #ch.exchange_declare('gitosis.post_update', 'fanout', auto_delete=False)
    qname, _, _ = ch.queue_declare();
    ch.queue_bind(qname, exchange)
    ch.basic_consume(qname, callback=callback)

    while ch.callbacks:
        ch.wait()

    ch.close()
    conn.close()

if __name__ == '__main__':
    main()

