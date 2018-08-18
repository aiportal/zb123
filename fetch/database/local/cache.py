"""
Store items to local SQLite db.
"""

import peewee
import uuid
from datetime import datetime, date, timedelta
from ..common import JSONObjectField, JSONArrayField
import os


# if not os.path.exists('../data'):
#     os.mkdir('../data')
# db_uuid = '{0:%Y%m%d-%H%M}'.format(datetime.now())
# db_store = peewee.SqliteDatabase('../data/{}.db'.format(db_uuid))
db_store = peewee.SqliteDatabase('../cache.db')


class CacheModel(peewee.Model):
    class Meta:
        database = db_store


class CacheItem(CacheModel):
    class Meta:
        db_table = 'item_temp'
        indexes = (
            (('source', 'title', 'subject'), False),
        )

    uuid = peewee.UUIDField(primary_key=True, help_text='url的hash值')
    day = peewee.DateField(help_text='招标日期')
    source = peewee.CharField(max_length=50, help_text='招标来源')
    title = peewee.CharField(help_text='标题')
    subject = peewee.CharField(help_text='分类')
    completed = peewee.BooleanField(default=False, help_text='是否已上传成功')

    data = peewee.BlobField(help_text='Item对象压缩存储')


class _GatherTemp(CacheModel):
    class Meta:
        db_table = 'gather_temp'
        indexes = (
            (('day', 'source', 'title'), False),
        )
    uuid = peewee.UUIDField(primary_key=True, help_text='url的hash值')
    day = peewee.DateField(help_text='招标日期')
    source = peewee.CharField(max_length=50, help_text='招标来源')
    title = peewee.CharField(help_text='标题')

    subject = peewee.CharField(help_text='信息分类(招标、中标等)')
    area = peewee.CharField(max_length=50, help_text='地区(省、市等)')
    url = peewee.CharField(help_text='详情页请求网址')

    end = peewee.DateField(null=True, help_text='截止日期')
    industry = peewee.CharField(null=True, help_text='行业分类(机械、软件等)')
    pid = peewee.CharField(null=True)
    tender = peewee.CharField(null=True)
    budget = peewee.CharField(null=True, help_text='预算金额/中标金额')
    tels = peewee.CharField(null=True, help_text='联系电话')

    extends = JSONObjectField(null=True, sort_keys=True, help_text='扩展信息(json格式)')
    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')


class _ContentTemp(CacheModel):
    class Meta:
        db_table = 'content_temp'
    uuid = peewee.UUIDField(primary_key=True, help_text='url的hash值')
    day = peewee.DateField(help_text='招标日期')
    source = peewee.CharField(max_length=50, help_text='招标来源')
    title = peewee.CharField(help_text='标题')

    index_url = peewee.CharField(null=True, help_text='索引页网址')
    top_url = peewee.CharField(null=True, help_text='框架详情页的顶层网址')
    real_url = peewee.CharField(null=True, help_text='详情页转向之后的真实网址(redirect)')

    html = peewee.BlobField(null=True, help_text='HTML内容(压缩)')
    contents = JSONArrayField(null=True, help_text='招标详情(正文)')

    digest = JSONObjectField(null=True, sort_keys=True, help_text='关键字段摘要')
    attachments = JSONObjectField(null=True, help_text='附件信息')
    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')


class EventLog(CacheModel):
    class Meta:
        db_table = 'log_temp'
    ID = peewee.PrimaryKeyField()
    source = peewee.CharField(max_length=50, help_text='信息来源')
    level = peewee.CharField(max_length=50, help_text='信息类型')
    url = peewee.CharField(null=True, help_text='简单描述')
    info = JSONObjectField(null=True, sort_keys=True, indent=2, help_text='信息描述')
    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')

    @staticmethod
    def log_exception(source: str, level: str, url: str, exception: Exception=None, addition: dict=None):
        info = addition or {}
        info['exception'] = str(exception)
        EventLog.create(source=source, level=level, url=url, info=info)


db_store.create_tables([CacheItem, EventLog], True)
