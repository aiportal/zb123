import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class xinyang_1Spider(scrapy.Spider):
    """
    @title: 信阳市公共资源交易网
    @href: http://ggzy.xyxzspfw.gov.cn:88/tpfront/
    """
    name = 'henan/xinyang/1'
    alias = '河南/信阳'
    allowed_domains = ['xyxzspfw.gov.cn']
    start_urls = [
        ('http://ggzy.xyxzspfw.gov.cn:88/TPFront/jyxx/003002/003002001/', '招标公告/政府采购'),
        ('http://ggzy.xyxzspfw.gov.cn:88/TPFront/jyxx/003002/003002003/', '中标公告/政府采购'),
        ('http://ggzy.xyxzspfw.gov.cn:88/TPFront/jyxx/003001/003001001/', '招标公告/建设工程'),
        ('http://ggzy.xyxzspfw.gov.cn:88/TPFront/jyxx/003001/003001003/', '中标公告/建设工程'),
        ('http://ggzy.xyxzspfw.gov.cn:88/TPFront/jyxx/003002/003002002/', '变更公告/政府采购'),
        ('http://ggzy.xyxzspfw.gov.cn:88/TPFront/jyxx/003001/003001002/', '变更公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='ul.ewb-info-items > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

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
        body = response.css('#mainContent')

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
