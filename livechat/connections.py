# coding=utf8
"""
Copyright © 2018, Ismael Lugo, <ismaelrlgv@gmail.com>
Licensed under the MIT License.
"""
from __future__ import absolute_import, unicode_literals

import time
import logging
import datetime
from six.moves import _thread
from livechat import environ as env
from livechat import conncls

logger = logging.getLogger(env.logger_name)


class conn(conncls.conn):
    handlers = env.handlers
    handlers_index = []

    def __init__(self, sock, address):
        self.socket = sock
        self.socket.settimeout(env.recv_timeout)
        self.address = address
        self.host = address
        self.stop = False
        self.session = None
        self.queue = None
        self.height = None
        self.width = None
        self.last_msg = time.time()
        self.recv_frames = False
        self.send_frames = False
        self.send_done = False
        self.recv_done = False

    def quit(self, msg):
        self.code('111', msg)
        self.close()
        return env.EXIT

    def input_loop(self):
        logger.debug('[%s] input loop started' % self.address)
        for data in self.recv_loop():
            #logger.debug('[%s] data: %s' % (self.address, data))
            self.process(data)

        if self.session:
            self.session.action = 1
            self.session.logout_date = datetime.datetime.now()
            self.session.save()
            if self.queue:
                self.queue.clear()
                del env.frame_queues[self.session.token]
        logger.debug('[%s] input loop stoped' % self.address)


def new(sock, address):
    logger.info("Connection received: %s", address[0])
    client = conn(sock, address[0])
    _thread.start_new(client.check_conn, ())
    _thread.start_new(client.input_loop, ())
