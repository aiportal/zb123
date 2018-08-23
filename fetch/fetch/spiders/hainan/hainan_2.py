import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class hainan_2Spider(scrapy.Spider):
    """
    @title: 中国海南政府采购网
    @href: http://www.ccgp-hainan.gov.cn/
    """
    name = 'hainan/2'
    alias = '海南'
    allowed_domains = ['www.ccgp-hainan.gov.cn']
    start_urls = [
        ('http://www.ccgp-hainan.gov.cn/cgw/cgw_list.jsp?bid_type=102', '预公告/政府采购'),
        ('http://www.ccgp-hainan.gov.cn/cgw/cgw_list.jsp?bid_type=101', '招标公告/政府采购'),
        ('http://www.ccgp-hainan.gov.cn/cgw/cgw_list.jsp?bid_type=113', '废标公告/政府采购'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='div.nei02_right ul > li > em > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../i//text()',
                                       'area': '../../span/b//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.content01')
        suffix = '（\w{2,5}）$'

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
        g.set(area=[self.alias, data.get('area')])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
