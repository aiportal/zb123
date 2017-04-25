import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class ${NAME}Spider(scrapy.Spider):
    """
    @title: 
    @href: 
    """
    name = '${Package_name}'
    alias = ''
    allowed_domains = []
    start_urls = [
    ]

    def start_requests(self):
        pass

    def parse(self, response):
        pass

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('')

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
