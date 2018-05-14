# coding=utf8
"""
Copyright © 2018, Ismael Lugo, <ismaelrlgv@gmail.com>
Licensed under the MIT License.
"""
from __future__ import absolute_import, unicode_literals

import uuid
import hashlib
import datetime
from livechat import environ as env
from livechat.database import database


database.connect()
database.build()

user_tb = database.getTable('User')
session_tb = database.getTable('Session')
codes_tb = database.getTable('Codes')


def get_id(n=2, div='-'):
    return div.join(str(uuid.uuid4()).split(div, n)[:n])


def text2hash(text):
    return hashlib.new(env.hash_algorithm, text).hexdigest()


def getuser(username):
    try:
        return user_tb.get(user_tb.username == username.upper())
    except user_tb.DoesNotExist:
        return


def adduser(username, password):
    return user_tb.create(username=username.upper(), password=text2hash(password))


def new_code():
    return codes_tb.create()


def use_code(token, username, password):
    if getuser(username):
        return False
    try:
        code = codes_tb.get(codes_tb.token == token)
    except codes_tb.DoesNotExist:
        return False
    if code.user is not None:
        return False
    user = adduser(username, password)
    code.user = user
    code.use_date = datetime.datetime.now()
    code.save()
    return True


def revoke(user):
    user.active = False
    user.save()


def grant(user):
    user.active = True
    user.save()


def login(username, password, address):
    user = getuser(username)
    if user is None or not user.active:
        return False
    if user.password != text2hash(password):
        return False

    token = get_id()
    #logout(user)

    return session_tb.create(user=user, token=token, action=0, address=address)


def logout(user):
    (session_tb.update({
        session_tb.action: 1,
        session_tb.logout_date: datetime.datetime.now()})
    .where(
        (session_tb.user == user) and \
        (session_tb.action == 0))
    .execute())
