import peewee
from .db import *
from typing import Union, Iterable
from urllib.parse import urlsplit
from datetime import datetime
import socket


class SiteInfo(LinkModel):
    class Meta:
        db_table = 'sites'

    id = peewee.PrimaryKeyField()
    parents = JSONArrayField(null=True, help_text='父节点列表')
    name = peewee.CharField(null=True, help_text='spider name')
    title = peewee.CharField(null=True, help_text='网站标题')
    host = peewee.CharField(help_text='网站')
    url = peewee.CharField(unique=True, help_text='网址')

    valid = peewee.BooleanField(default=True, help_text='是否可访问')
    enabled = peewee.BooleanField(default=True, help_text='是否启用')
    ttl = peewee.IntegerField(null=True, help_text='访问延时(秒)')
    comment = peewee.CharField(null=True, help_text='备注')
    time = peewee.DateTimeField(default=datetime.now, help_text='最后更新时间')

    @staticmethod
    def append(url: str, title: str, ttl: int, parent: int) -> int:
        """ append new site """
        exists = SiteInfo.select(SiteInfo.id).where(SiteInfo.url == url).exists()
        if not exists:
            hostname = urlsplit(url).hostname
            parents = parent and [parent] or None
            row = SiteInfo(title=title, host=hostname, url=url, ttl=ttl, parents=parents)
            if not row.title or len(str(row.title)) < 1 or len(str(row.title)) > 30:
                row.enabled = False
            row.save()
            return row.id
        else:
            row = SiteInfo.get(url=url)
            if parent:
                parents = (row.parents or []) + [parent]
                row.parents = list(set(parents))
            row.title = title
            row.ttl = ttl
            row.time = datetime.now()
            row.save()
            return row.id


if socket.gethostname() == 'ubuntu':
    if not SiteInfo.table_exists():
        SiteInfo.create_table(fail_silently=True)
