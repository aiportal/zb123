import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json
import re


class JiangsuXuzhouSpider(scrapy.Spider):
    """
    @title: 徐州市政府采购网
    @href: http://www.ccgp-xuzhou.gov.cn/Home/HomeIndex
    """
    name = 'jiangsu/xuzhou_1'
    alias = '江苏/徐州'
    allowed_domains = ['ccgp-xuzhou.gov.cn']
    start_urls = [
        ('http://www.ccgp-xuzhou.gov.cn/Home/PageListJson'
         '?sidx=createdate&category_id={}&page=1&pagesize=20'.format(k), v)
        for k, v in [
            ('331', '招标公告/政府采购/市级'),
            ('334', '招标公告/政府采购/县级'),
            ('333', '中标公告/政府采购/市级'),
            ('336', '中标公告/政府采购/县级'),
            ('332', '更正公告/政府采购/市级'),
            ('335', '更正公告/政府采购/县级'),
        ]
    ]
    custom_settings = {'DOWNLOAD_DELAY': 1.2}

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        """ 解析索引包 """
        """
            { "total":2,"page":2,"records":58,"pagerecords":30,"costtime":"11","rows": [...] }
        """
        url_detail = 'http://www.ccgp-xuzhou.gov.cn/Home/HomeDetails?type=0&articleid={0[bulletinid]}'
        pkg = json.loads(response.text)
        for row in pkg['rows']:
            url = url_detail.format(row)
            row = {k: v for k, v in row.items()}
            row.update(**response.meta['data'])
            row.update(link=url)
            yield self._parse_contents(response, data=row)

        # page, total = pkg['page'], pkg['total']
        # if page < total:
        #     url = SpiderTool.url_replace(response.url, page=page+1)
        #     yield scrapy.Request(url, meta=response.meta, dont_filter=True)

    def _parse_contents(self, response, data):
        """ 解析详情项 """
        """
        {
            "bulletinid": "20170413195251",
            "projecttype": 5,
            "bulletinidcontent": "<P>...</P>",
            "bulletintitle": "徐州市电子政务外网建设项目竞争性磋商终止公告[项目编号：徐采磋C（2017）002]",
            "projectname": "竞争性磋商",
            "createdate": "2017-04-13T19:57:54",
            "bulletinidtype": 2,
            "rownum": 3,
            "status": 1,
            "companyid": "C8153622-0237-44F4-A522-F0E0ED71AE0F"
        },
        """
        body = data.get('bulletinidcontent')
        suffix = '\[.+编号：.+\]$'

        day = FieldExtractor.date(data.get('createdate'))
        title = data.get('bulletintitle')
        title = re.sub(suffix, '', title)
        contents = [body]
        g = GatherItem.new(
            url=data['link'],
            ref=response.url,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=self.alias)
        g.set(subject=[data.get('subject'), data.get('projectname')])
        g.set(budget=FieldExtractor.money([body]))
        return g
