# coding=utf8
"""
Copyright © 2018, Ismael Lugo, <ismaelrlgv@gmail.com>
Licensed under the MIT License.
"""
from __future__ import absolute_import, unicode_literals

import argparse
import logging

from logging.handlers import RotatingFileHandler as rfh
from livechat import environ as env

parser = argparse.ArgumentParser()
parser.add_argument('--verbose',
    action='store_true',
    help='Show verbose messages')

parser.add_argument('--code',
    action='store_true',
    help='Generate a registration code')

parser.add_argument('--host',
    type=str, metavar='<ip address>', default="0.0.0.0",
    help='Listen on the given IP address')

parser.add_argument('--port',
    type=int, metavar='<port>', default=env.default_port,
    help='Listen on <port> instead of the default port (%(default)s)')

parser.add_argument('--cert',
    type=str, metavar='<file>',
    help='Local certificate')

parser.add_argument('--key',
    type=str, metavar='<file>',
    help='Local private key')

parser.add_argument('--lim',
    type=int, metavar='<number>', default=env.maxconn,
    help='Listen more than (%(default)s) clients')

parser.add_argument('--queue',
    type=int, metavar='<number>', default=env.queue_maxsize,
    help='Change queue max')

parser.add_argument('--no-daemon',
    action='store_true',
    help="Don't fork to the background, don't write a pid file")

parser.add_argument('action', metavar="action",
    type=str, nargs="?", choices=['start', 'stop', 'restart', 'status'],
    help="Controls the execution of the service (start|stop|restart|status)")


def main():
    args = parser.parse_args()

    logger = logging.getLogger(env.logger_name)

    if args.no_daemon:
        formatter = logging.Formatter(env.log_form, "%H:%M:%S")
        handler = logging.StreamHandler()
    else:
        formatter = logging.Formatter(env.log_form)
        handler = rfh(env.log_file, maxBytes=env.maxBytes, backupCount=env.backupCount)

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if args.code:
        from livechat import auth
        print('Code: %s' % auth.new_code().token)
        exit(0)

    if args.queue:
        env.queue_maxsize = args.queue

    if args.action:
        if args.action in ('start', 'restart'):
            if not args.key:
                print('[-] Local private key needed.')
                exit(1)
            elif not args.cert:
                print('[-] Local certificate needed.')
                exit(1)
        from livechat import server
        from livechat import server_handlers
        from livechat import daemon

        chat = server.server(args.host,
            args.port, args.key,
            args.cert, args.lim)

        if args.no_daemon and args.action == 'start':
            try:
                chat.start()
            except KeyboardInterrupt:
                pass
        else:
            switch = daemon.switch(chat.start, ())
            switch.switch(args.action)
        exit(0)

    parser.print_usage()
    exit(0)
