import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
from datetime import date
import re


class guangyuan_1Spider(scrapy.Spider):
    """
    @title: 广元市公共资源交易网
    @href: http://www.gyggzy.gov.cn/ceinwz/indexgy.htm
    """
    name = 'sichuan/guangyuan/1'
    alias = '四川/广元'
    allowed_domains = ['gyggzy.gov.cn']
    start_urls = [
        ('http://www.gyggzy.gov.cn/ceinwz/WebInfo_List.aspx?jsgc=0100000&newsid=100&FromUrl=jsgc', '招标公告/建设工程'),
        ('http://www.gyggzy.gov.cn/ceinwz/WebInfo_List.aspx?jsgc=0000010&newsid=102&FromUrl=jsgc', '中标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='table.myGVClass tr > td > a[id$=HLinkGcmc]',
                                       attrs_xpath={'text': './/text()', 'pid': '../../td[1]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('table.yygl')
        prefix = '^\[\w{1,5}\]'

        day = FieldExtractor.date(data.get('day'), response.css('table.yygl'), str(date.today()))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        g.set(pid=data.get('pid'))
        return [g]
