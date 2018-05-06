# coding=utf8
"""
Copyright © 2018, Ismael Lugo, <ismaelrlgv@gmail.com>
Licensed under the MIT License.
"""
from __future__ import absolute_import, unicode_literals

import socket
import argparse
import logging

from livechat import environ as env
from six.moves import _thread

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose',
    action='store_true',
    help='Show verbose messages')

parser.add_argument('-s', '--show',
    action='store_true',
    help='Show video stream')

parser.add_argument('-d', '--delay',
    type=int, metavar='<ms>', default=env.delay,
    help='Show video stream')

parser.add_argument('-f', '--fps',
    type=int, metavar='<num>', default=env.fps,
    help='set fps stream')

parser.add_argument('-ss', '--skip',
    type=int, metavar='<num>', default=env.skip,
    help='set fps stream')

conn = parser.add_argument_group('Connection')
conn.add_argument('-H', '--host',
    type=str, metavar='<ip/host>', required=True,
    help='Address of the remote host for the connection')

conn.add_argument('-P', '--port',
    type=int, metavar='<port>', default=env.default_port,  required=False,
    help='Connect to another port instead of the default port (%(default)s)')

conn = parser.add_argument_group('Authentication')
conn.add_argument('-U', '--user',
    type=str, metavar='<username>', required=True,
    help='Username for authentication')

conn.add_argument('-W', '--password',
    type=str, metavar='<password>',
    help='Password to use for the connection. Not recommended, insecure.')

actions = parser.add_mutually_exclusive_group(required=True)
actions.add_argument('-R', '--register',
    type=str, metavar='<code>',
    help='Register a new user with the given code')

actions.add_argument('-S', '--stream',
    type=str, metavar='<device>',
    help='Stream video to the remote host')

actions.add_argument('-V', '--video',
    type=str, metavar='<id>',
    help='Gets video of the remote stream')


def main():
    args = parser.parse_args()

    logger = logging.getLogger(env.logger_name)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(env.log_form, "%H:%M:%S"))
    logger.addHandler(handler)
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    if not args.register and not args.stream and not args.video:
        return parser.print_usage()

    import livechat.client
    import livechat.client_handlers

    client = livechat.client.client(args.host, args.port, args.user, args.password)
    client.build_socket()
    try:
        client.connect()
    except socket.error as e:
        return logger.error('Connection error: %s', e)

    if args.video:
        client.auth()
        _thread.start_new(client.request_video, (args.video,))
    elif args.stream:
        client.auth()
        if args.show:
            env.show_stream = True
        if args.fps:
            env.fps = args.fps
            logger.info('Video fps: %s', env.fps)
        if args.skip:
            env.skip = args.skip
            logger.info('Video skip frames: %s', env.skip)
        if args.delay:
            env.delay = args.delay / 1000.
            logger.info('Video delay: %s', env.delay)
        args = (int(args.stream) if args.stream.isdigit() else args.stream,)
        _thread.start_new(client.stream_video, args)
    elif args.register:
        client.register(args.register)

    try:
        client.input_loop()
    except KeyboardInterrupt:
        pass
