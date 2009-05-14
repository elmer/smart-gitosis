#!/usr/bin/env python

import sys
import amqplib.client_0_8 as amqp
from optparse import OptionParser
from gitosis.util import read_config

#import simplejson as json

def callback(msg):
    # try:
    #   data = json.loads(msg.body)
    #   # this will return a python dictionary from the message
    #   # data['key'] to retreive value
    #   repository = data['repository']
    #   git.pull(repository)
    # except: # I can't remember what the exception is named
    #   # some failure
    #   
    print('MESSAGE: %s' % msg.body)
    
def main():
    parser = OptionParser()
    parser.add_option('--config', metavar='FILE', help='read config from FILE')
    options, args = parser.parse_args()

    config = read_config(options.config)
    host = config.get("amqp", "host")
    user_id = config.get("amqp", "user_id")
    password = config.get("amqp", "password")
    ssl = config.getboolean("amqp", "ssl")

    conn = amqp.Connection(host, userid=user_id, password="password", ssl=ssl)
    ch = conn.channel()
    ch.access_request('/data', active=True, read=True)

    #ch.exchange_declare('gitosis.post_update', 'fanout', auto_delete=False)
    qname, _, _ = ch.queue_declare();
    ch.queue_bind(qname, 'gitosis.post_update')
    ch.basic_consume(qname, callback=callback)

    while ch.callbacks:
        ch.wait()

    ch.close()
    conn.close()

if __name__ == '__main__':
    main()

