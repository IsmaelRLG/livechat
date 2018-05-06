# coding=utf8
"""
Copyright © 2018, Ismael Lugo, <ismaelrlgv@gmail.com>
Licensed under the MIT License.
"""
from __future__ import absolute_import, unicode_literals

import os

logger_name = 'livechat'
base_path = os.path.join(os.environ['HOME'], ".livechat")
database_path = os.path.join(base_path, 'livechat.db')
pid_file = '.livechat.pid'
pid_path = base_path
log_path = os.path.join(base_path, 'log')
log_file = os.path.join(log_path, 'livechat.log')
log_form = '%(asctime)s | %(levelname)-8s | %(message)s'
if not os.path.exists(base_path):
    os.mkdir(base_path)
if not os.path.exists(log_path):
    os.mkdir(log_path)

frame_queues = {}
EXIT = True
default_port = 5789
show_stream = False
queue_release = False
queue_maxsize = 50
hash_algorithm = 'sha512'
buffer_size = 2**16
recv_timeout = 4 * 60
bin_length = 14
backupCount = 7
maxBytes = 2**10 * 256  # 256 Kb
maxconn = 12
frame_max = 10
fps = 15
skip = 1
delay = 0
clients = {}
handlers = {}
error = '000'
ok =    '001'
req =   '010'
auth_ok = '011'
sess_id = '012'
recv_frame_start = "100"
recv_frame_end   = "110"
send_frame_start = "101"
send_frame_end   = "200"
id_not_found     = "404"
