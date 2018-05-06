# coding=utf8
"""
Copyright © 2018, Ismael Lugo, <ismaelrlgv@gmail.com>
Licensed under the MIT License.
"""
from __future__ import absolute_import, unicode_literals

from six.moves import queue
from livechat.environ import frame_queues, queue_maxsize, queue_release


class Queue(queue.Queue):

    def add(self, item):
        if self.maxsize <= 0 and queue_release and self.full():
            self.get()  # make a free slot
        self.put(item)

    def clear(self):
        self.queue.clear()


def get(id, maxsize=0):
    if id in frame_queues:
        return frame_queues[id]
    frame_queues[id] = Queue(queue_maxsize)
    return get(id)


def remove(id):
    del frame_queues[id]
