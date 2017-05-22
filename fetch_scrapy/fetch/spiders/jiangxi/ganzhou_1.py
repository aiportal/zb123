import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class ganzhou_1Spider(scrapy.Spider):
    """
    @title: 赣州公共资源交易网
    @href: http://www.gzzbtbzx.com/index.asp
    """
    name = 'jiangxi/ganzhou/1'
    alias = '江西/赣州'
    allowed_domains = ['gzzbtbzx.com']
    start_urls = [
        ('http://www.gzzbtbzx.com/more.asp?id=2&city=1', '招标公告/政府采购'),
        ('http://www.gzzbtbzx.com/more.asp?id=3&city=1', '中标公告/政府采购'),
        ('http://www.gzzbtbzx.com/more.asp?id=12&city=1', '招标公告/建设工程'),
        ('http://www.gzzbtbzx.com/more.asp?id=13&city=1', '中标公告/建设工程'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 3.88}

    link_extractor = MetaLinkExtractor(css='tr[height="25"] > td > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()-1]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('td.line15')
        prefix = '^[A-Z0-9-]+'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        if title.endswith('..'):
            title1 = FieldExtractor.text(response.css('td[align="center"] > b'))
            if len(title)-2 < len(title1) < 200:
                title = title1
        title = re.sub(prefix, '', title)
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name,
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
