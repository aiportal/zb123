import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class jinhua_1Spider(scrapy.Spider):
    """
    @title: 金华市公共资源交易网
    @href: http://www.jhztb.gov.cn/jhztb/
    """
    name = 'zhejiang/jinhua/1'
    alias = '浙江/金华'
    allowed_domains = ['jhztb.gov.cn']
    start_urls = [
        ('http://www.jhztb.gov.cn/jhztb/gcjyysgs/index.htm', '招标公告/建设工程'),
        ('http://www.jhztb.gov.cn/jhztb/gcjyzbzy/index.htm', '中标公告/建设工程'),
        ('http://www.jhztb.gov.cn/jhztb/jsgcgcjszbgg/index.htm', '招标公告/建设工程'),
        ('http://www.jhztb.gov.cn/jhztb/jsgcgcjszbjg/index.htm', '中标公告/建设工程'),
        ('http://www.jhztb.gov.cn/jhztb/jsgcjhszbgg/index.htm', '招标公告/建设工程'),
        ('http://www.jhztb.gov.cn/jhztb/jsgcjhszbjg/index.htm', '中标公告/建设工程'),
        ('http://www.jhztb.gov.cn/jhztb/zfcgggyg/index.htm', '预公告/政府采购'),
        ('http://www.jhztb.gov.cn/jhztb/zfcgcggg/index.htm', '招标公告/政府采购'),
        ('http://www.jhztb.gov.cn/jhztb/zfcgzbhxgs/index.htm', '中标公告/政府采购'),

    ]

    link_extractor = MetaLinkExtractor(css='div.Right-list dl > dt > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

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
        body = response.css('div.Main-p img') or response.css('div.content-Border img')

        day = FieldExtractor.date(data.get('day'))
        title = FieldExtractor.text(response.css('div.content-Border > font.Font-weight')) \
            or data.get('title') or data.get('text')
        contents = body.extract()
        contents = [re.sub('&amp;', '&', s) for s in contents]
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
        return [g]
