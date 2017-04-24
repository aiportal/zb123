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
    allowed_domains = []
    start_urls = [
        ('http://www.bgpc.gov.cn/news/news/nt_id/97', '预公告/需求公告'),
        ('http://www.bgpc.gov.cn/news/news/nt_id/29', '招标公告'),
        ('http://www.bgpc.gov.cn/news/news/nt_id/32', '中标公告'),
        ('http://www.bgpc.gov.cn/news/news/nt_id/30', '更正公告'),
        ('http://www.bgpc.gov.cn/news/news/nt_id/33', '其他公告/废标公告'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='#newslist ul > li > span > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../span[last()]//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#news_xx') or response.css('#news_word')

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
