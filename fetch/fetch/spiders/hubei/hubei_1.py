import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class hubei_1Spider(scrapy.Spider):
    """
    @title: 湖北省政府采购网
    @href: http://www.ccgp-hubei.gov.cn/
    """
    name = 'hubei/1'
    alias = '湖北'
    allowed_domains = ['ccgp-hubei.gov.cn']
    start_urls = [
        ('http://www.ccgp-hubei.gov.cn/notice/cggg/pzbgg/index_1.html', '招标公告/政府采购/省级'),
        ('http://www.ccgp-hubei.gov.cn/notice/cggg/pzhbgg/index_1.html', '中标公告/政府采购/省级'),
        ('http://www.ccgp-hubei.gov.cn/notice/cggg/pfbgg/index_1.html', '废标公告/政府采购/省级'),
        ('http://www.ccgp-hubei.gov.cn/notice/cggg/pgzgg/index_1.html', '更正公告/政府采购/省级'),
        ('http://www.ccgp-hubei.gov.cn/notice/cggg/czbgg/index_1.html', '招标公告/政府采购/市级'),
        ('http://www.ccgp-hubei.gov.cn/notice/cggg/czhbgg/index_1.html', '中标公告/政府采购/市级'),
        ('http://www.ccgp-hubei.gov.cn/notice/cggg/cfbgg/index_1.html', '废标公告/政府采购/市级'),
        ('http://www.ccgp-hubei.gov.cn/notice/cggg/cgzgg/index_1.html', '更正公告/政府采购/市级'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='ul.news-list-content > li > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        # if response.css('#mainFrame'):
        #     src = response.css('#mainFrame').xpath('./@src').extract_first()
        #     url = urljoin(response.url, src)
        #     return [scrapy.Request(url, meta=response.meta, callback=self.parse_item)]
        data = response.meta['data']
        body = response.css('div.art_con')

        prefix = '^\[.+]([\w{2,8}]){0,1}'
        suffix = '（[\w-]+）$'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
        title = re.sub(suffix, '', title)
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
