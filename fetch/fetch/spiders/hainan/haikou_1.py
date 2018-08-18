import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class haikou_1Spider(scrapy.Spider):
    """
    @title: 海口市公共资源交易网
    @href: http://www.hkcein.com/
    """
    name = 'hainan/haikou/1'
    alias = '海南/海口'
    allowed_domains = ['hkcein.com']
    start_urls = ['http://www.hkcein.com/dwr/call/plaincall/infopublishDWR.listForInte.dwr']
    start_body = r"""
callCount=1
page=
httpSessionId=
scriptSessionId=
c0-scriptName=infopublishDWR
c0-methodName=listForInte
c0-id=0
c0-e1=string:3
c0-e2=string:{0}
c0-e3=string:JYXX
c0-e4=number:1
c0-e5=string:10
c0-e6=string:true
c0-e7=string:packTable
c0-param0=Object_Object:{{flag:reference:c0-e1, type:reference:c0-e2, minflag:reference:c0-e3, currentPage:reference:c0-e4, pageSize:reference:c0-e5, isPage:reference:c0-e6, tabId:reference:c0-e7}}
batchId=1
"""

    @property
    def start_params(self):
        return [
            (self.start_body.format(k), v)
            for k, v in [
                ('zzbFlag', '招标公告/政府采购'),
                ('zjgFlag', '中标公告/政府采购'),
                ('zbFlag', '招标公告/建设工程'),
                ('jgFlag', '中标公告/建设工程'),
            ]
        ]

    detail_url = 'http://www.hkcein.com/indexmain.do?method=showMoreInfo&flag=3&minflag=JYXX&type=list' \
                 '&attachment=undefined&name={0[FLAG]}&key={0[KEYID]}'

    def start_requests(self):
        url = self.start_urls[0]
        headers = {'Content-Type': 'text/plain'}
        for body, subject in self.start_params:
            data = dict(subject=subject)
            yield scrapy.Request(url, method='POST', body=body, headers=headers, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        re_prop = 's\d+\.(\w+)="(.+)"'
        js = response.text.encode().decode('unicode-escape')
        lns = [s for s in js.split('\r\n') if SpiderTool.re_text('NAME="(.+)"', s)]
        for ln in lns:
            props = [SpiderTool.re_text(re_prop, s) for s in ln.split(';') if re.search(re_prop, s)]
            row = dict(props)
            url = self.detail_url.format(row)
            row.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.part_2, div.part_3')

        day = FieldExtractor.date(data.get('TIME'))
        title = data.get('NAME') or data.get('NAMESHOW')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
