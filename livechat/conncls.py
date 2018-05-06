# coding=utf8
"""
Copyright © 2018, Ismael Lugo, <ismaelrlgv@gmail.com>
Licensed under the MIT License.
"""
from __future__ import absolute_import, unicode_literals

import re
import time
import logging
import socket
from livechat import environ as env

logger = logging.getLogger(env.logger_name)

class conn(object):
    handlers = env.handlers

    @classmethod
    def add_handler(cls, runlevel, handler):
        if runlevel not in cls.handlers:
            cls.handlers[runlevel] = []
        logger.debug("New handler: %s(%s)" % (handler.__name__, runlevel))
        cls.handlers[runlevel].append(handler)

    def check_conn(self):
        while not self.stop:
            time.sleep(2.5)
            if self.recv_frames or self.send_frames:
                continue
            elif (time.time() - self.last_msg) > env.recv_timeout:
                self.close()

    def close(self):
        self.socket.close()
        self.stop = True

    def process(self, data):
        break_all = 0
        index = list(self.handlers.keys())
        index.sort()
        for runlevel in index:
            for handler in self.handlers[runlevel]:
                logger.debug('[%s] Running handler %s(%s)',
                self.address, handler.__name__, runlevel)
                if handler(self, data) is True:
                    break_all += 1
                    break
            if break_all != 0:
                break

    def recv_loop(self):
        while not self.stop:
            try:
                data = self.socket.recv(env.buffer_size)
            except socket.timeout:
                break
            except socket.error:
                break

            if data == "":
                break

            for line in data.splitlines():
                if line == "":
                    continue
                logger.debug("%s |--> %s" % (self.address, line))
                yield line
        logger.error('[%s] Connection closed', self.address)
        self.stop = True

    def send(self, text):
        if self.stop:
            logger.warning("%s <--X %s" % (self.address, text))
            return
        logger.debug("%s <--| %s" % (self.address, text))
        self.socket.send(text + "\n\r")

    def code(self, code, msg):
        self.send('%s %s' % (code, msg))

def command(regex):
    regex = re.compile(regex, re.IGNORECASE)

    def func_wrapper(func):
        def arg_wrapper(conn, data):
            result = regex.match(data)
            if result is None:
                return
            data = result.groupdict()
            result = func(conn, data)
            return env.EXIT if result is None else result
        arg_wrapper.__name__ = func.__name__
        return arg_wrapper
    return func_wrapper


def bin(num):
    return format(num, '0'+str(env.bin_length)+'b')
