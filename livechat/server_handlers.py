# coding=utf8
"""
Copyright © 2018, Ismael Lugo, <ismaelrlgv@gmail.com>
Licensed under the MIT License.
"""
from __future__ import absolute_import, unicode_literals

import re
import time
import socket
import logging
from livechat import auth
from livechat import queue
from livechat import environ as env
from livechat.conncls import command, conn, bin
from livechat.environ import ok, recv_frame_start, recv_frame_end
from livechat.environ import send_frame_start, send_frame_end

logger = logging.getLogger(env.logger_name)
auth_re = re.compile('AUTHENTICATE {1,}(?P<base64>[^ ]+)', re.I)
pong_re = re.compile('PONG', re.I)
req_re = re.compile('REQ {1,}(?P<args>.*)', re.I)
new_re = re.compile('NEW {1,}(?P<code>[^ ]+) {1,}(?P<base64>[^ ]+)', re.I)


def authenticate(conn, data):
    result = auth_re.match(data)
    if conn.session is not None:
        return

    if result is None:
        if new_re.match(data):
            return
        return conn.quit("Authentication required.")

    data = result.groupdict()
    try:
        cred = data['base64'].decode('base64')
        username, password = cred.split('\0')
    except:
        return conn.quit("Authentication failed.")

    session = auth.login(username, password, conn.address)
    if session is False:
        return conn.quit("Authentication failed.")
    conn.session = session
    conn.code(env.auth_ok, "Authenticated.")
    conn.code(env.sess_id, "Session id: " + session.token)
    env.clients[session.token] = conn
    #conn.code(req, "Connection type?")
    return env.EXIT
conn.add_handler(0, authenticate)


def register(conn, data):
    result = new_re.match(data)
    if conn.session is not None:
        return

    if result is None:
        return conn.quit("Authentication required.")

    data = result.groupdict()
    try:
        cred = data['base64'].decode('base64')
        username, password = cred.split('\0')
    except:
        return conn.quit("Authentication failed.")

    if auth.use_code(data['code'], username, password):
        return conn.quit("Registration successfully.")
    else:
        return conn.quit("Registration failed.")
conn.add_handler(0, register)


@command('PONG')
def pong(conn, data):
    conn.last_msg = time.time()
    return env.EXIT
conn.add_handler(2, pong)


@command('STREAM (?P<width>\d{1,5})x(?P<height>\d{1,5})')
def stream(conn, data):
    if not conn.queue:
        conn.queue = queue.get(conn.session.token)
        conn.height = int(data['height'])
        conn.width = int(data['width'])

    conn.code(recv_frame_start, "Waiting frames...")
    conn.recv_frames = True
    bin_length = 0
    partial = bytearray()
    length  = 0
    total = 0

    while True:
        try:
            if bin_length == -1:
                partial += conn.socket.recv(length)
                if len(partial) >= length:
                    conn.queue.add(partial[:length])
                    # <reset>
                    partial     = partial[length:]
                    bin_length += 1
                    length     -= length
                    total      += 1
                    # </reset>
            else:
                if len(partial) >= env.bin_length:
                    bin_length += int(str(partial[:env.bin_length]), 2)
                    partial     = partial[env.bin_length:]
                    if len(partial) >= bin_length:
                        tmp_length = partial[:bin_length]
                        partial    = partial[env.bin_length:]
                    else:
                        tmp_length = partial + conn.socket.recv(bin_length - len(partial))
                        partial = bytearray()
                else:
                    tmp_data = partial + conn.socket.recv(env.bin_length - len(partial))
                    bin_length += int(str(tmp_data), 2)
                    partial     = bytearray()
                    tmp_length  = conn.socket.recv(bin_length)

                if tmp_length == "EOF" or not tmp_length.isdigit():
                    break
                length += int(str(tmp_length))
                bin_length -= bin_length + 1
                continue
        except Exception as e:
            logger.error(e, exc_info=int(env.verbose))
            break

    conn.code(recv_frame_end, "%s frames received" % total)
    conn.last_msg = time.time()
    conn.recv_frames = False
    return env.EXIT
conn.add_handler(2, stream)


@command('VIDEO (?P<id>[^ ]+)')
def video(conn, data):
    if not data['id'] in env.frame_queues:
        conn.code(env.id_not_found, "User id not found: %s" % data['id'])
        return env.EXIT

    conn.send_frames = env.clients[data['id']]
    w = conn.send_frames.width
    h = conn.send_frames.height
    conn.code(send_frame_start, "FRAMES %sx%s" % (w, h))
    return env.EXIT
conn.add_handler(1, video)


@command(recv_frame_start + ' .*')  # video, segunda parte
def send_frames(conn, data):
    if not conn.send_frames:
        return

    def frame(frame):
        length = len(frame)
        meta = bytearray("%s%s" % (bin(len(str(length))), length), 'utf-8')
        return meta + frame

    total = 0
    while True:
        if not conn.send_frames.recv_frames and conn.send_frames.queue.empty():
            break

        try:
            conn.socket.sendall(frame(conn.send_frames.queue.get()))
        except:
            try: conn.socket.send('00000000000011EOF')
            except socket.error: pass
            break
        else:
            total += 1

    conn.last_msg = time.time()
    conn.send_frames = None
    return env.EXIT
conn.add_handler(2, send_frames)
