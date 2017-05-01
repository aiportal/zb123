import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class Zhejiang2Spider(scrapy.Spider):
    """
    @title: 浙江省公共资源交易中心
    @href: http://new.zmctc.com/zjgcjy/
    """
    name = 'zhejiang/2'
    alias = '浙江'
    allowed_domains = ['zmctc.com']
    start_urls = [
        ('http://new.zmctc.com/zjgcjy/jyxx/004001/004001001/', '招标公告/工程'),
        ('http://new.zmctc.com/zjgcjy/jyxx/004001/004001002/', '招标公告/货物'),
        ('http://new.zmctc.com/zjgcjy/jyxx/004001/004001003/', '招标公告/服务'),
        ('http://new.zmctc.com/zjgcjy/jyxx/004010/004010001/', '中标公告/工程'),
        ('http://new.zmctc.com/zjgcjy/jyxx/004010/004010002/', '中标公告/货物'),
        ('http://new.zmctc.com/zjgcjy/jyxx/004010/004010003/', '中标公告/服务'),
    ]

    link_extractor = MetaLinkExtractor(css='tr > td > a.WebList_sub',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

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
        body = response.css('#TDContent, div.infodetail, #trAttach')
        tag = '\[[A-Z0-9]+\]'

        day = FieldExtractor.date(data.get('day'), response.css('#tdTitle'))
        title = data.get('title') or data.get('text')
        title = re.sub(tag, '', title)
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
