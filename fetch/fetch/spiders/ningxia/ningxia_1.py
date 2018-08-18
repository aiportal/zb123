import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json
import re


class ningxia_1Spider(scrapy.Spider):
    """
    @title: 宁夏回族自治区公共资源交易网
    @href: http://www.nxggzyjy.org/ningxiaweb/
    @href: http://www.nxzfcg.gov.cn/ningxiaweb/
    """
    name = 'ningxia/1'
    alias = '宁夏'
    allowed_domains = ['nxggzyjy.org']
    start_urls = [
        ('http://www.nxggzyjy.org/ningxia/services/BulletinWebServer/getInfoListInAbout'
         '?response=application/json&pageIndex=1&pageSize=18&categorynum={}&cityname=&title='.format(k), v)
        for k, v in [
            ('002002001', '招标公告/政府采购'),
            ('002002002', '更正公告/政府采购'),
            ('002002003', '中标公告/政府采购'),
            ('002001001', '招标公告/建设工程'),
            ('002001002', '更正公告/建设工程'),
            ('002001003', '中标公告/建设工程'),
        ]
    ]
    top_url = 'http://www.nxggzyjy.org/ningxia/WebbuilderMIS/RedirectPage/RedirectPage.jspx' \
                 '?infoid={0[infoid]}&categorynum={0[categorynum]}&locationurl=http://www.nxggzyjy.org/ningxiaweb'
    req_url = 'http://www.nxggzyjy.org/ningxia/services/BulletinWebServer/getRelateInDetail' \
              '?response=application/json&infoid={0[infoid]}'

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        res = json.loads(response.text)['return']
        pkg = json.loads(res)
        for row in pkg['Table']:
            top_url = self.top_url.format(row)
            req_url = self.req_url.format(row)
            row.update(**response.meta['data'])
            yield scrapy.Request(req_url, meta={'data': row, 'top_url': top_url}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        """
        """
        pkg = json.loads(json.loads(response.text)['return'])
        info = [x.get('info') for x in reversed(pkg['result']) if x.get('info')][0][0]
        data = response.meta['data']
        body = info.get('infocontent')
        prefix = '^\[\w{2,8}\]+'
        if re.match('^\s*<script .+</script>\s*$', body, re.DOTALL):
            return []

        day = FieldExtractor.date(data.get('infodate'), info.get('infodate'))
        title = info.get('title') or pkg.get('title') or data.get('title')
        title = re.sub(prefix, '', title)
        contents = [body]
        g = GatherItem.create(
            response,
            source=self.name,
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money([body]))
        return [g]
