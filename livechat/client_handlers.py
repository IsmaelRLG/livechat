# coding=utf8
"""
Copyright © 2018, Ismael Lugo, <ismaelrlgv@gmail.com>
Licensed under the MIT License.
"""

from __future__ import absolute_import, unicode_literals

import time
import sys
import cv2
import socket
import logging

import numpy as np
from livechat import environ as env
from livechat.conncls import command, conn, bin
from livechat.environ import ok, recv_frame_start, recv_frame_end
from livechat.environ import send_frame_start, send_frame_end
logger = logging.getLogger(env.logger_name)


@command(ok + ' {1,}(?P<message>.*)')
def ok_code(conn, data):
    logger.info(data['message'])
    return env.EXIT
conn.add_handler(0, ok_code)


@command(send_frame_start + ' FRAMES (?P<width>\d{1,5})x(?P<height>\d{1,5})')
def frames_code(conn, data):
    """
    Muestra el video recibido del servidor. Funciona más o menos así...

    [cliente -> servidor] solicita video por su ID
    [cliente <- servidor] responde con las dimensiones. cod: 101
    [cliente -> servidor] responde que está listo para recibir video. cod: 100
    [cliente <- servidor] el servidor envía el video
    """
    h = conn.stream_height = int(data['height'])
    w = conn.stream_width = int(data['width'])
    logger.info('Recv frames %sx%s' % (data['width'], data['height']))

    conn.code(recv_frame_start, "Waiting frames...")
    conn.recv_frames = True
    bin_length = 0
    partial = bytearray()
    length  = 0
    total = 0
    title = 'webcam %sx%s' % (data['width'], data['height'])
    num = lambda x, n: ("%-" + str(n) + "s  ") % x
    to_del = [0]
    cv2.namedWindow(title, cv2.WINDOW_AUTOSIZE)
    def echo(text, preserve=False):
        if to_del[0] != 0 and not preserve:
            sys.stdout.write("\b" * to_del[0])
            to_del[0] -= to_del[0]
        to_del[0] += len(text)
        sys.stdout.write(text)
        sys.stdout.flush()

    while True:
        try:
            if bin_length == -1:
                partial += conn.socket.recv(length)
                if len(partial) >= length:
                    nparr = np.fromstring(bytes(partial[:length]), np.uint8)
                    img = cv2.imdecode(nparr, cv2.CV_LOAD_IMAGE_COLOR)

                    cv2.imshow(title, img)
                    echo("|| Currently Showing", True)
                    # <reset>
                    partial     = partial[length:]
                    bin_length += 1
                    length     -= length
                    total      += 1
                    # </reset>
                    key = cv2.waitKey(1)
                    if key == 27:
                        break
                    if key == 32:
                        filename = time.strftime('%y_%m_%d...%H_%M_%S.jpg')
                        cv2.imwrite(filename, img)
                        logger.info('Frame saved as %s', filename)

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
                echo(num(total, 6)+"||  ")
                if tmp_length == "EOF" or not tmp_length.isdigit():
                    break
                length += int(str(tmp_length))
                bin_length -= bin_length + 1
                echo(num(length, 8), True)
                continue
        except Exception as e:
            logger.exception(e)
            break

    cv2.destroyAllWindows()
    conn.close()
    return env.EXIT
conn.add_handler(1, frames_code)


@command('111 (?P<message>.*)')
def quit(conn, data):
    logger.info(data['message'])
    return env.EXIT
conn.add_handler(2, quit)


@command(env.auth_ok + ' (?P<message>.*)')
def auth_ok(conn, data):
    logger.info(data['message'])
    conn.auth_ok = True
    return env.EXIT
conn.add_handler(2, auth_ok)


@command(env.sess_id + ' Session id: (?P<id>[^ ]+)')
def sess_id(conn, data):
    logger.info('Your session id: ' + data['id'])
    conn.sess_id = data['id']
    return env.EXIT
conn.add_handler(2, sess_id)


@command(send_frame_end + ' (?P<message>.*)')
def send_end_code(conn, data):
    logger.info(data['message'])
    conn.close()
    return env.EXIT
conn.add_handler(2, send_end_code)


@command(recv_frame_start + ' .*')
def recv_code(conn, data):
    """
    Esto transmite video al servidor remoto. Funciona más o menos así...
    [cliente -> servidor] Se informa que se enviará video
    [cliente <- servidor] Notifica que está listo. cod: 100
    [cliente -> servidor] Se envía el video
    """
    if not conn.video:
        return

    conn.send_frames = True
    def frame(frame):
        #frame = frame.encode('base64').replace('\n', '')
        length = len(frame)
        meta = bytearray("%s%s" % (bin(len(str(length))), length), 'utf-8')
        return meta + frame

    total = 0
    title = 'webcam stream %sx%s' % (conn.stream_width, conn.stream_height)
    skip = 0
    while True:
        try:
            img, tmp_frame = conn.get_frame()
            if env.skip:
                skip += 1
                if skip > env.skip:
                    skip -= skip
                else:
                    continue

            if env.show_stream:
                cv2.imshow(title, cv2.flip(img, 1))
                key = cv2.waitKey(1)
                if key == 27:
                    break
            if env.delay:
                time.sleep(env.delay)
            conn.socket.sendall(frame(tmp_frame))
        except Exception as e:
            logger.exception(e)
            try: conn.socket.send('00000000000011EOF')
            except socket.error: pass
            break
        else:
            total += 1

    conn.last_msg = time.time()
    conn.send_frames = False
    return env.EXIT
conn.add_handler(1, recv_code)


@command(recv_frame_end + ' (?P<message>.*)')
def recv_end_code(conn, data):
    logger.info(data['message'])
    conn.close()
    return env.EXIT
conn.add_handler(2, recv_end_code)


@command(env.id_not_found + ' (?P<message>.*)')
def id_notfound_code(conn, data):
    logger.info(data['message'])
    conn.close()
    return env.EXIT
conn.add_handler(1, id_notfound_code)
