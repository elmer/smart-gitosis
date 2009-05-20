from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from txamqp.protocol import AMQClient
from txamqp.client import TwistedDelegate
from txamqp.content import Content
import txamqp.spec
import settings

from gitosis.util import read_config

from helpers import process_config

@inlineCallbacks
def gotConnection(conn, authentication, body):
    config = process_config(read_config(settings.gitosis_config))

    yield conn.start(authentication)
    chan = yield conn.channel(1)
    yield chan.channel_open()

    msg = Content(body)
    msg["delivery mode"] = 2
    chan.basic_publish(exchange=config['exchange'], content=msg)
    
    yield chan.channel_close()

    chan0 = yield conn.channel(0)
    yield chan0.connection_close()
    
    reactor.stop()
    
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print "%s path_to_spec content" % sys.argv[0]
        sys.exit(1)

    config = process_config(read_config(settings.gitosis_config))
    spec = txamqp.spec.load(sys.argv[1])
    authentication = {"LOGIN": config['user_id'], "PASSWORD": config['password']}

    delegate = TwistedDelegate()
    d = ClientCreator(reactor, AMQClient, delegate=delegate, vhost="/",
        spec=spec).connectTCP(config['host'], config['port'])

    d.addCallback(gotConnection, authentication, sys.argv[2])

    reactor.run()
