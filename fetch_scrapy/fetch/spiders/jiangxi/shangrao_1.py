import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class shangrao_1Spider(scrapy.Spider):
    """
    @title: 上饶市建设工程交易中心
    @href: http://www.srjsgc.cn/
    """
    name = 'jiangxi/shangrao/1'
    alias = '江西/上饶'
    allowed_domains = ['srjsgc.cn']
    start_urls = [
        ('http://www.srjsgc.cn/news/list.php?catid=4', '招标公告/建设工程'),
        ('http://www.srjsgc.cn/news/list.php?catid=5', '中标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='tr[height="27"] > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

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
        body = response.css('td[style*="width:900px;"]')
        prefix = '^【.{2,18}】\s*'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
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
