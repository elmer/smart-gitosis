from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from twisted.python import log

from txamqp.protocol import AMQClient
from txamqp.client import TwistedDelegate

from helpers import random_queue, process_config, update_or_create_repository
from gitosis.util import read_config
from socket import gethostname

import simplejson as json
import settings

def callback_wrapper(projects_dir, git_user, git_server):
    def recv_callback(msg, chan, queue):
        log.msg("Received: %s" % msg.content.body)
        if msg.content.body == "status":
            log.msg("status: ok - %s" % gethostname())
        else:
            data = json.loads(msg.content.body)
            repository = data['repository']
            update_or_create_repository(data['repository'],
                                        projects_dir,
                                        git_user,
                                        git_server)
        return (queue.get().addCallback(recv_callback, chan, queue))
    return recv_callback

def echo_callback(msg, chan, queue):
    log.msg('Received: %s on channel: %s' % (msg.content.body, chan.id))
    return (queue.get().addCallback(echo_callback, chan, queue))

@inlineCallbacks
def gotConnection(conn, authentication):
    config = process_config(read_config(settings.gitosis_config))
    QUEUE = random_queue()

    yield conn.start(authentication)
    chan = yield conn.channel(1)
    yield chan.channel_open()

    # Initialize the MQ state
    yield chan.queue_declare(queue=QUEUE, durable=True, exclusive=False, auto_delete=False)
    yield chan.exchange_declare(exchange=config['exchange'], type="fanout",
                                durable=True, auto_delete=False)
    yield chan.queue_bind(queue=QUEUE, exchange=config['exchange'])
    yield chan.basic_consume(queue=QUEUE, no_ack=True, consumer_tag="smart")

    queue = yield conn.queue("smart")
    recv_callback = callback_wrapper(config['projects_dir'],
                                     config['git_user'],
                                     config['git_server'])
    yield (queue.get().addCallback(recv_callback, chan, queue))


    # This is all about closing the connection nicely
    yield chan.basic_cancel("smart")
    yield chan.channel_close()
    chan0 = yield conn.channel(0)
    yield chan0.connection_close()

    reactor.stop()
