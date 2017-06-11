import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class SichuanMeishan2Spider(scrapy.Spider):
    """
    @title: 眉山市公共资源交易网/建设工程
    @href: http://www.msggzy.org.cn/msweb/
    """
    name = 'sichuan/meishan/2'
    alias = '四川/眉山'
    allowed_domains = ['msggzy.org.cn']
    start_urls = [
        ('http://www.msggzy.org.cn/msweb/gcjs/003002/', '招标公告/建设工程'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 5.68}

    link_extractor = MetaLinkExtractor(css='tr[height="22"] > td > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()-1]//text()',
                                                    'end': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            url = re.sub('/msweb/InfoDetail/', '/msweb/Template/GongGaoDetailWithSignature.aspx', lnk.url)
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#spnShow')

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
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
        return [g]
