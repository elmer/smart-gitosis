#!/usr/bin/env python

import amqplib.client_0_8 as amqp
from optparse import OptionParser

def callback(msg):
    print('MESSAGE: %s' % msg.body)
    
def main():
    parser = OptionParser()
    parser.add_option('--host', dest='host',
                        help='AMQP server to connect to (default: %default)',
                        default='localhost')
    parser.add_option('-u', '--userid', dest='userid',
                        help='userid to authenticate as (default: %default)',
                        default='guest')
    parser.add_option('-p', '--password', dest='password',
                        help='password to authenticate with (default: %default)',
                        default='guest')
    parser.add_option('--ssl', dest='ssl', action='store_true',
                        help='Enable SSL (default: not enabled)',
                        default=False)

    options, args = parser.parse_args()

    conn = amqp.Connection(options.host, userid=options.userid,
                           password=options.password, ssl=options.ssl)

    ch = conn.channel()
    ch.access_request('/data', active=True, read=True)

    ch.exchange_declare('gitosis.post_update', 'direct', auto_delete=False, durable=True)
    ch.queue_declare(queue='gitosis.post_update', durable=True, exclusive=False, auto_delete=False) 
    ch.queue_bind('gitosis.post_update', 'gitosis.post_update')
    ch.basic_consume('gitosis.post_update', callback=callback)

    while ch.callbacks:
        ch.wait()

    ch.close()
    conn.close()

if __name__ == '__main__':
    main()

