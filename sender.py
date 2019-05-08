#!/usr/bin/env python3
import kombu
import threading
import time
from kombu import Exchange, Queue

import logging


media_exchange = Exchange('media', 'direct', durable=True)
video_queue = Queue('video', exchange=media_exchange, routing_key='video')


LOG = logging.getLogger(__name__)


def _produce(producer):
    producer.publish({'name': '/tmp/lolcat1.avi', 'size': 1301013},
                     exchange=media_exchange, routing_key='video',
                     declare=[video_queue])


def _drain_errback(exc, interval):
    LOG.exception('Draining error: %s', exc)
    LOG.info('Retry triggering in %s seconds', interval)


class Producer(object):

    def __init__(self):
        transport = 'amqp'
        transport_options = dict()
        url = 'amqp://devtools:devtools@localhost:5672/'
        self._exchange_name = 'media'
        self._topic = 'media'
        self._running = threading.Event()
        self._conn = kombu.Connection(url, transport=transport,
                                      transport_options=transport_options)
        self._exchange = kombu.Exchange(name=self._exchange_name)

    def _make_queue(self, routing_key, exchange, channel=None):
        queue_name = "%s_%s" % (self._exchange_name, routing_key)
        return kombu.Queue(name=queue_name,
                           routing_key=routing_key, durable=False,
                           exchange=exchange, auto_delete=True,
                           channel=channel)

    def start(self):
        with kombu.connections[self._conn].acquire(block=True) as conn:
            with conn.Producer(serializer='json') as producer:
                ensure_kwargs = dict()
                ensure_kwargs['errback'] = _drain_errback
                safe_produce = conn.ensure(producer, _produce, **ensure_kwargs)
                self._running.set()
                try:
                    while self._running.is_set():
                        safe_produce(producer)
                        time.sleep(2)
                finally:
                    self._running.clear()


def main():
    producer = Producer()
    producer.start()


if __name__ == '__main__':
    main()
