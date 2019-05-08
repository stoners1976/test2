#!/usr/bin/env python3
import kombu
import threading
from kombu import Exchange, Queue
from kombu import exceptions as kombu_exceptions

import logging


media_exchange = Exchange('media', 'direct', durable=True)
video_queue = Queue('video', exchange=media_exchange, routing_key='video')


LOG = logging.getLogger(__name__)


def process_media(body, message):
    print(body)
    message.ack()


def _drain(conn, timeout):
    try:
        conn.drain_events(timeout=timeout)
    except kombu_exceptions.TimeoutError:
        pass


def _drain_errback(exc, interval):
    LOG.exception('Draining error: %s', exc)
    LOG.info('Retry triggering in %s seconds', interval)


class Consumer(object):

    def __init__(self):
        transport = 'amqp'
        transport_options = dict()
        url = 'amqp://devtools:devtools@localhost:5672/'
        self._exchange_name = 'media'
        self._topic = 'media'
        self._running = threading.Event()
        self._drain_events_timeout = 1
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
            with conn.Consumer(video_queue, callbacks=[process_media]) as consumer:
                ensure_kwargs = dict()
                ensure_kwargs['errback'] = _drain_errback
                safe_drain = conn.ensure(consumer, _drain, **ensure_kwargs)
                self._running.set()
                try:
                    while self._running.is_set():
                        # uncomment the below line to make things recover...
                        # consumer.consume()
                        safe_drain(conn, self._drain_events_timeout)
                finally:
                    self._running.clear()


def main():
    consumer = Consumer()
    consumer.start()


if __name__ == '__main__':
    main()
