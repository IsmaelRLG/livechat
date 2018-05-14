# coding=utf8
"""
Copyright © 2018, Ismael Lugo, <ismaelrlgv@gmail.com>
Licensed under the MIT License.
"""
from __future__ import absolute_import, unicode_literals

import uuid
import logging
import datetime

from peewee import SqliteDatabase
from peewee import Model, CharField, DateTimeField, UUIDField
from peewee import BooleanField, ForeignKeyField, IntegerField
from livechat import environ as env

logger = logging.getLogger(env.logger_name)
peewee_logger = logging.getLogger('peewee')
peewee_logger.setLevel(logging.ERROR)


class database(object):
    database = SqliteDatabase(env.database_path)
    connected = False
    builded = False
    tables = {}

    @classmethod
    def connect(cls):
        if cls.connected:
            return
        logger.debug("Open database connection...")
        cls.database.connect()

    @classmethod
    def create_tables(cls, models, safe=False):
        cls.database.create_tables(models, safe)
        for model in models:
            cls.tables[model.__name__] = model

    @classmethod
    def create_table(cls, model_class, safe=False):
        cls.database.create_tables(model_class, safe=safe)
        cls.tables[model_class.__name__] = model_class

    @classmethod
    def getTable(cls, table_name):
        if table_name in cls.tables:
            return cls.tables[table_name]
        else:
            raise ValueError("Unknown table name: %s", table_name)

    @classmethod
    def build(cls):
        models = []

        class BaseModel(Model):
            class Meta:
                database = cls.database

        class User(BaseModel):
            uuid = UUIDField(primary_key=True, default=uuid.uuid4)
            username = CharField()
            password = CharField()
            active = BooleanField(default=True)
            date = DateTimeField(default=datetime.datetime.now)
        models.append(User)

        class Session(BaseModel):
            user = ForeignKeyField(User, related_name='logins')
            token = CharField()
            action = IntegerField()  # 0: login, 1: logout
            address = CharField()
            login_date = DateTimeField(default=datetime.datetime.now)
            logout_date = DateTimeField(null=True)
        models.append(Session)

        class Codes(BaseModel):
            token = UUIDField(default=uuid.uuid4)
            user = ForeignKeyField(User, related_name='code', null=True)
            exp_date = DateTimeField(default=datetime.datetime.now)
            use_date = DateTimeField(null=True)
        models.append(Codes)
        cls.create_tables(models, safe=True)
