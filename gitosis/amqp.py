import amqplib.client_0_8 as amqp

def send(host="localhost", user_id="guest", password="guest", ssl=True,
         exchange="gitosis.post_update", data={}, vhost="/data"):
    m = json.dumps(data)

    log.info('Sending "%s" to: %s' % (m, exchange))

    msg = amqp.Message(m, content_type='text/plain')

    conn = amqp.Connection(host, userid=user_id, password=password, ssl=ssl)

    ch = conn.channel()
    ch.access_request(vhost, active=True, write=True)
    ch.exchange_declare(exchange, 'fanout', auto_delete=False)
    ch.basic_publish(msg, exchange)
    ch.close()
    conn.close()

    return True
