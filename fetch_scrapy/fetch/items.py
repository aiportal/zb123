# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.org/en/latest/topics/items.html

import scrapy
from scrapy import Field
from database import JobIndex
from datetime import datetime, date
import sys
from typing import List, Union


class GatherItem(scrapy.Item):
    source = Field()        # 来源
    uuid = Field()          # UUID
    url = Field()           # 网址（详情页请求网址）
    html = Field()          # html全文
    index_url = Field(null=True)    # 索引页网址
    top_url = Field(null=True)      # 参考网址(框架顶层网址)
    real_url = Field(null=True)     # 真实网址(redirect)

    day = Field()               # 招标日期
    end = Field()               # 截止日期
    title = Field()             # 标题
    area = Field()              # 地区
    subject = Field()           # 分类
    industry = Field(null=True)     # 行业

    contents = Field()              # 正文内容
    pid = Field(null=True)           # 工程ID
    tender = Field(null=True)        # 招标单位
    budget = Field(null=True)        # 预算金额/成交金额
    tels = Field(null=True)          # 联系电话(多个电话用斜杠分隔)
    extends = Field(null=True)       # 扩展字段值(dict)
    digest = Field(null=True)        # 摘要信息

    # attachments = Field(null=True)      # 附件信息[(网址,文件名),...]
    # file_urls = Field(null=True)
    # files = Field(null=True)

    @property
    def year(self):
        return datetime.strptime(str(self['day']), '%Y-%m-%d').year

    @staticmethod
    def create(response, source: str, day: date, title: str, contents: List[str], **kwargs):
        if (not source) or (day == date.min) or (not title) or (not contents):
            raise ValueError('GatherItem')

        assert not isinstance(response.request, scrapy.FormRequest)     # Post网址的hash要加上参数
        redirects = response.request.meta.get('redirect_urls', [])
        req_url = redirects and redirects[0] or response.url            # 原始请求网址
        url_hash = JobIndex.url_hash(req_url)                           # 防止重入的网址hash

        url = response.meta.get('top_url') or req_url                  # 用户跳转的原文页面
        html = '-full' in sys.argv and response.text or None            # -full模式下保存html
        real_url = (response.url != req_url) and response.url or None   # 有redirect时记录最终请求网址
        top_url = response.meta.get('top_url')                          # 有框架时记录顶层网址

        kwargs.update(source=source, day=day, title=title, contents=contents)
        kwargs.update(uuid=url_hash, url=url, html=html, index_url=None, top_url=top_url, real_url=real_url)
        return GatherItem(kwargs)

    def set(self,
            end: date=None,
            area: Union[str, list]=None,
            subject: Union[str, list]=None,
            industry: Union[str, list]=None,
            pid: str=None,
            tender: str=None,
            budget: str=None,
            tels: str=None,
            extends: dict=None,
            digest: dict=None):
        params = dict(end=end, area=area, subject=subject, industry=industry, pid=pid, tender=tender, budget=budget,
                      tels=tels, extends=extends, digest=digest)
        for k, v in params.items():
            if not v:
                continue
            if isinstance(v, list):
                self[k] = self._words(v)
            self[k] = v

    @staticmethod
    def _words(value: Union[str, list]):
        if isinstance(value, str):
            return value
        values = [str(v).strip() for v in value if v and str(v).strip()]
        return any(values) and '/'.join(values) or None
