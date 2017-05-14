import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class liaoning_2Spider(scrapy.Spider):
    """
    @title: 辽宁省政府集中采购网
    @href: http://www.lnzc.gov.cn/SitePages/default.aspx
    """
    name = 'liaoning/2'
    alias = '辽宁'
    allowed_domains = ['lnzc.gov.cn']
    start_urls = [
        ('http://www.lnzc.gov.cn/SitePages/AfficheListAll1.aspx', '招标公告/政府采购'),
        ('http://www.lnzc.gov.cn/SitePages/AfficheListAll2.aspx', '中标公告/政府采购'),
        ('http://www.lnzc.gov.cn/SitePages/AfficheListAll3.aspx', '更正公告/政府采购'),
    ]

    link_extractor = MetaLinkExtractor(css='div.infoArea ul > li span.listDate ~ span > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../span[1]//text()'})

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
        body = response.css('div.article')
        pid = '\([A-Z0-9-]{10,18}\)'
        suffix = '\([A-Z0-9-]+\)$'

        day = FieldExtractor.date(data.get('day'), response.css('div.subinfo'))
        title = data.get('title') or data.get('text')
        title = re.sub(suffix, '', title)
        title = re.sub(pid, '', title)
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
