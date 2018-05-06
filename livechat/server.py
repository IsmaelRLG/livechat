
import ssl
import socket
import logging
from livechat import connections
from livechat import environ as env
from socket import AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET


logger = logging.getLogger(env.logger_name)


class server(object):
    __status = True
    def __init__(self, host, port, key, crt, maxconn):
        self.sock = None
        self.host = host
        self.port = port
        self.key = key
        self.crt = crt
        self.max = maxconn
        self.__running = False
        self.__builded = False

    @classmethod
    def disable(cls):
        cls.__status = False

    @classmethod
    def enable(cls):
        cls.__status = True

    def build_socket(self):
        if self.__builded:
            return
        self._sock = socket.socket(AF_INET, SOCK_STREAM)
        self._sock.bind((self.host, self.port))
        self._sock.listen(self.max)
        self._sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        logger.debug('Private key: %s', self.key)
        logger.debug('Certificate: %s', self.crt)
        self.sock = ssl.wrap_socket(self._sock,
            keyfile=self.key,
            certfile=self.crt,
            server_side=True)
        logger.info('Listen on %s:%d' % (self.host, self.port))

    def server_loop(self):
        self.__running = True
        try:
            logger.debug('Starting server loop, waiting connections...')
            while self.__status:
                try:
                    conn, address = self.sock.accept()
                    connections.new(conn, address)
                except socket.error as e:
                    logging.error(str(e))
        except Exception:
            pass

        self.__running = False

    def start(self):
        self.build_socket()
        if self.__running:
            return
        self.server_loop()
