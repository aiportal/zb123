import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class chongqing_3Spider(scrapy.Spider):
    """
    @title: 重庆市招标投标综合网
    @href: http://www.cqzb.gov.cn/
    """
    name = 'chongqing/3'
    alias = '重庆'
    allowed_domains = ['cqzb.gov.cn']
    start_urls = [
        ('http://www.cqzb.gov.cn/class-5-1.aspx', '招标公告'),
        ('http://www.cqzb.gov.cn/class-5-45.aspx', '中标公告'),
    ]

    link_extractor = MetaLinkExtractor(css='div.ztb_list_right ul > li > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

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
        body = response.css('#ztb_zbxx1')

        day = FieldExtractor.date(data.get('day'), response.css('#con_formz1'))
        title = data.get('title') or data.get('text') or FieldExtractor.text(response.css('#tith1'))
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
