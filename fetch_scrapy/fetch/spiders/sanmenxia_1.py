import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class sanmenxia_1Spider(scrapy.Spider):
    """
    @title: 三门峡市公共资源交易中心
    @href: http://www.smxgzjy.org/
    """
    name = 'henan/sanmenxia/1'
    alias = '河南/三门峡'
    allowed_domains = ['smxgzjy.org']
    start_urls = [
        ('http://www.smxgzjy.org/cggg/index.jhtml', '招标公告/政府采购'),
        ('http://www.smxgzjy.org/jggg/index.jhtml', '中标公告/政府采购'),
        ('http://www.smxgzjy.org/zbgg/index.jhtml', '招标公告/建设工程'),
        ('http://www.smxgzjy.org/zbgs/index.jhtml', '中标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='div.List1 ul > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span[@class="Right"]//text()'})

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
        body = response.css('div.Content')

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
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
