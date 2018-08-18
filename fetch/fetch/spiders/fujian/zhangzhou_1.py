import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class zhangzhou_1Spider(scrapy.Spider):
    """
    @title: 漳州招标采购网
    @href: http://www.zzbidding.com/
    """
    name = 'fujian/zhangzhou/1'
    alias = '福建/漳州'
    allowed_domains = ['zzbidding.com']
    start_urls = [
        ('http://www.zzbidding.com/cms/sitemanage/index.shtml?siteId=560371110512840000', '招标公告'),
        ('http://www.zzbidding.com/cms/sitemanage/index.shtml?siteId=560371110514830000', '中标公告'),
    ]

    link_extractor = MetaLinkExtractor(css='#resources tr > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert len(links) > 0
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('table.about_news')

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
