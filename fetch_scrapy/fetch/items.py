# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.org/en/latest/topics/items.html

import scrapy
from scrapy import Field
from datetime import datetime


class GatherItem(scrapy.Item):
    source = Field()        # 来源
    uuid = Field()          # UUID
    url = Field()           # 网址（详情页请求网址）
    html = Field()          # html全文
    index_url = Field(null=True)    # 索引页网址
    top_url = Field(null=True)      # 参考网址(框架顶层网址)
    real_url = Field(null=True)     # 真实网址(redirect)

    day = Field()           # 招标日期
    end = Field()           # 截止日期
    title = Field()         # 标题
    area = Field()          # 地区
    subject = Field()       # 分类
    industry = Field(null=True)     # 行业

    contents = Field()              # 正文内容
    pid = Field(null=True)           # 工程ID
    tender = Field(null=True)        # 招标单位
    budget = Field(null=True)        # 预算金额/成交金额
    tels = Field(null=True)          # 联系电话(多个电话用斜杠分隔)
    extends = Field(null=True)       # 扩展字段值(dict)
    digest = Field(null=True)        # 摘要信息

    attachments = Field(null=True)      # 附件信息[(网址,文件名),...]
    file_urls = Field(null=True)
    files = Field(null=True)

    @property
    def year(self):
        return datetime.strptime(str(self['day']), '%Y-%m-%d').year


class ItemProxy:
    def __init__(self, item: scrapy.Item):
        self._item = item
        for key in item.fields:
            super().__setattr__(key, None)

    def __setattr__(self, key, value):
        if hasattr(self, '_item') and key in self._item.fields:
            self._item[key] = value
        super().__setattr__(key, value)

    def set(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def item(self):
        return self._item.copy()
