#!/usr/bin/env python

import sys
import time
from optparse import OptionParser
from gitosis.util import read_config


import amqplib.client_0_8 as amqp

def main():
    parser = OptionParser()
    parser.add_option('--config', metavar='FILE', help='read config from FILE')
    options, args = parser.parse_args()

    if not args:
        parser.print_help()
        sys.exit(1)

    config = read_config(options.config)
    host = config.get("amqp", "host")
    user_id = config.get("amqp", "user_id")
    password = config.get("amqp", "password")
    ssl = config.getboolean("amqp", "ssl")


    msg_body = ' '.join(args)
    msg = amqp.Message(msg_body, content_type='text/plain')

    conn = amqp.Connection(host, userid=user_id, password=password, ssl=ssl)

    ch = conn.channel()
    ch.access_request('/data', active=True, write=True)
    ch.exchange_declare('gitosis.post_update', 'fanout', auto_delete=False)
    ch.basic_publish(msg, exchange='gitosis.post_update')
    ch.close()
    conn.close()

if __name__ == '__main__':
    main()
