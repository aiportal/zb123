import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class shandong_1Spider(scrapy.Spider):
    """
    @title: 山东政府采购网
    @href: http://www.ccgp-shandong.gov.cn/sdgp2014/site/index.jsp
    """
    name = 'shandong/1'
    alias = '山东'
    allowed_domains = ['ccgp-shandong.gov.cn']
    start_urls = [
        ('http://www.ccgp-shandong.gov.cn/sdgp2014/site/channelall.jsp?colcode={}'.format(k), v)
        for k, v in [
            ('0301', '招标公告/政府采购/省级'),
            ('0302', '中标公告/政府采购/省级'),
            ('0303', '招标公告/政府采购/市县'),
            ('0304', '中标公告/政府采购/市县'),
            ('0305', '更正公告/政府采购'),
            ('0306', '废标公告/政府采购'),
        ]
    ]

    link_extractor = MetaLinkExtractor(css='tr > td > a.five',
                                       attrs_xpath={'text': './/text()', 'day': '../text()'})

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
        body = response.xpath('//td[@class="aa"]/../../*')

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
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
