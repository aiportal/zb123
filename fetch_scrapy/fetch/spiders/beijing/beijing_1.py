import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class Beijing1Spider(scrapy.Spider):
    """
    @title: 北京市政府采购中心
    @href: http://www.bgpc.gov.cn/
    """
    name = 'beijing/1'
    alias = '北京'
    allowed_domains = ['bgpc.gov.cn']
    start_urls = [
        ('http://www.bgpc.gov.cn/defaults/news/news/tid/1', '预公告/需求公告'),
        ('http://www.bgpc.gov.cn/defaults/news/news/tid/2', '招标公告'),
        ('http://www.bgpc.gov.cn/defaults/news/news/tid/5', '中标公告'),
        ('http://www.bgpc.gov.cn/defaults/news/news/tid/4', '更正公告'),
        ('http://www.bgpc.gov.cn/defaults/news/news/tid/6', '废标公告'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='div.content-right-content-center li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.content-right-details-content') or response.css('div.content-right-content')

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
