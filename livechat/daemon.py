# coding=utf8
"""
Copyright © 2018, Ismael Lugo, <ismaelrlgv@gmail.com>
Licensed under the MIT License.
"""
from __future__ import absolute_import, unicode_literals

import os
import sys
import time
import errno
from signal import SIGTERM
from livechat import environ as env


class daemonize(object):
    def __init__(self, function, args, kwargs={}, pid_path=None, pid_file=None):
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.pid_path = pid_path if pid_path else env.pid_path
        self.pid_file = pid_file if pid_file else env.pid_file

    def daemonize(self):
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent, print eventual PID before
                print("[+] Daemon running. PID %d" % pid)
                self.write_pid(pid)
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # start the daemon main loop
        self.function(*self.args, **self.kwargs)

    @property
    def pidfile(self):
        return os.path.join(self.pid_path, self.pid_file)

    def delete_pid(self):
        if os.path.isfile(self.pidfile):
            os.remove(self.pidfile)

    def write_pid(self, pid=None):
        with open(self.pidfile, 'w') as pidf:
            pidf.write(str(pid if pid else os.getpid()))

    def read_pid(self):
        if os.path.isfile(self.pidfile):
            with open(self.pidfile, 'r') as pidf:
                try:
                    pid = int(pidf.read())
                except:
                    pid = 0
            return pid
        else:
            return 0

    def check_pid(self, pid):
        if pid > 0:
            try:
                os.kill(pid, 0)
            except OSError as err:
                return err.errno == errno.EPERM
            else:
                return True
        else:
            return False


class switch(daemonize):
    def status(self):
        pid = self.read_pid()
        if self.check_pid(pid):
            print('[+] Daemon running. PID %s' % pid)
        else:
            print('[+] Daemon stoped.')
            self.delete_pid()
        exit(0)

    def start(self):
        if self.check_pid(self.read_pid()):
            print("[+] Daemon PID %s" % os.getpid())
            exit(0)

        self.daemonize()
        exit(0)

    def stop(self, catch=False):
        pid = self.read_pid()
        if not self.check_pid(pid):
            if catch:
                return
            self.delete_pid()
            print('[-] No running process.')
            exit(1)

        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(1)
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                print('[+] Daemon stoped. PID %d' % pid)
                self.delete_pid()

    def switch(self, option):
        if option == 'start':
            self.start()
        elif option == 'stop':
            self.stop()
        elif option == 'restart':
            self.stop(catch=True)
            self.start()
        elif option == 'status':
            self.status()
