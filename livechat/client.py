
# coding=utf8
"""
Copyright © 2018, Ismael Lugo, <ismaelrlgv@gmail.com>
Licensed under the MIT License.
"""
from __future__ import absolute_import, unicode_literals

import cv2
import ssl
import time
import socket
import logging
import getpass
from livechat import environ as env
from livechat import conncls

logger = logging.getLogger(env.logger_name)


class client(conncls.conn):
    handlers = env.handlers
    handlers_index = []

    def __init__(self, host, port, user, password=None, timeout=None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password if password else getpass.getpass()
        self._socket = None
        self.address = host
        self.stop = False

        # meta
        self.__connected = False
        self.__timeout = timeout if timeout else env.recv_timeout
        self.last_msg = time.time()
        self.recv_frames = False
        self.send_frames = False
        self.stream_height = None
        self.stream_width = None
        self.video = None
        self.auth_ok = False
        self.sess_id = None

    def wait_auth(self):
        while not self.stop and not self.auth_ok:
            time.sleep(0.1)

    def getcred(self):
        cred = '%s\0%s' % (self.user, self.password)
        cred = cred.encode('base64').replace('\n', '')
        return cred

    def build_socket(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(env.recv_timeout)
        self.socket = ssl.wrap_socket(self._socket)

    def connect(self):
        if self.__connected:
            return
        self.socket.connect((self.host, self.port))
        self.socket.__connected = True

    def input_loop(self):
        for data in self.recv_loop():
            self.process(data)
        self.release_webcam()

    def auth(self):
        self.send('AUTHENTICATE %s' % self.getcred())

    def register(self, code):
        self.send('NEW %s %s' % (code, self.getcred()))

    def stream_video(self, opt):
        self.wait_auth()
        self.build_video(opt)
        self.send('STREAM %sx%s' % (self.stream_width, self.stream_height))

    def request_video(self, user_id):
        self.wait_auth()
        self.send('VIDEO %s' % user_id)

    def build_video(self, opt):
        if self.video:
            return
        self.video = cv2.VideoCapture(opt)

        if self.video.isOpened():
            #self.video.set(cv2.cv.CV_CAP_PROP_FRAME_COUNT, env.frame_max)
            self.stream_width = int(self.video.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH))
            self.stream_height = int(self.video.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT))
            (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.', 2)
            self.video.set(cv2.cv.CV_CAP_PROP_FPS, env.fps)
        else:
            logger.error("Can't open webcam or file '%s'" % opt)
            exit(0)

    def get_frame(self):
        return self.process_frame(self.video.read()[1])

    def process_frame(self, frame):
        if env.mirror:
            frame = cv2.flip(frame, 1)
        return cv2.imencode('.jpg', frame, 
        [int(cv2.IMWRITE_JPEG_QUALITY), env.jpeg_quality])[1]

    def release_webcam(self):
        if self.video:
            self.video.release()
