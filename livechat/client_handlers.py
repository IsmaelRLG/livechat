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
    total_bytes = 0
    title = 'webcam %sx%s' % (data['width'], data['height'])
    txt = "[N#: %-6s] [TOTAL BYTES: %-9s] [SIZE: %-6s]"
    class n:
        to_del = 0
    cv2.namedWindow(title, cv2.WINDOW_AUTOSIZE)
    def echo(text):
        if n.to_del != 0:
            sys.stdout.write("\b" * n.to_del)
            n.to_del -= n.to_del
        n.to_del += len(text)
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

                if tmp_length == "EOF" or not tmp_length.isdigit():
                    break

                length += int(str(tmp_length))
                total_bytes += length + env.bin_length
                bin_length -= bin_length + 1
                if env.verbose:
                    echo(txt % (total, total_bytes, length))
                continue
        except Exception as e:
            logger.error(e, exc_info=int(env.verbose))
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

    class n:
        to_del = 0
        total_bytes = 0
    total = 0
    skip = 0
    txt = "[N#: %-6s] [TOTAL BYTES: %-9s] [SIZE: %-6s]"
    title = 'webcam stream %sx%s' % (conn.stream_width, conn.stream_height)

    def echo(text):
        if n.to_del != 0:
            sys.stdout.write("\b" * n.to_del)
            n.to_del -= n.to_del
        n.to_del += len(text)
        sys.stdout.write(text)
        sys.stdout.flush()

    def frame(frame):
        length = len(frame)
        if env.verbose:
            n.total_bytes += env.bin_length + length
            echo(txt % (total, n.total_bytes, length))
        meta = bytearray("%s%s" % (bin(len(str(length))), length), 'utf-8')
        return meta + bytearray(frame)

    while True:
        try:
            video_frame = conn.get_frame()
            if env.skip:
                skip += 1
                if skip > env.skip:
                    skip -= skip
                else:
                    continue

            if env.show_stream:
                cv2.imshow(title, cv2.imdecode(video_frame, 1))
                key = cv2.waitKey(1)
                if key == 27:
                    break
            conn.socket.sendall(frame(video_frame.tostring()))
            if env.delay:
                time.sleep(env.delay)
        except Exception as e:
            logger.error(e, exc_info=int(env.verbose))
            try: conn.socket.send('00000000000011EOF')
            except socket.error: pass
            break
        else:
            total+= 1

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
