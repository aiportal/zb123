import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class AnhuiBengbu1Spider(scrapy.Spider):
    """
    @title: 安徽蚌埠公共资源交易服务网
    @href: http://www.bbztb.cn/bbfwweb/
    """
    name = 'anhui/bengbu/1'
    alias = '安徽/蚌埠'
    allowed_domains = ['bbztb.cn']
    start_urls = [
        ('http://www.bbztb.cn/bbfwweb/jyxx/003001/', '招标公告/建设工程'),
        ('http://www.bbztb.cn/bbfwweb/zbgs/004001/', '中标公告/建设工程'),
        ('http://www.bbztb.cn/bbfwweb/jyxx/003002/', '招标公告/政府采购'),
        ('http://www.bbztb.cn/bbfwweb/zbgs/004002/', '中标公告/政府采购'),
    ]

    link_extractor = MetaLinkExtractor(css='tr[height="18"] > td > a[target=_blank]',
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
        body = response.css('#TDContent, .infodetail, #trAttach')
        suffix = '皖[A-Z0-9-]+$'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(suffix, '', title)
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
