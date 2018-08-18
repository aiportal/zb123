import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class JiangsuChangzhou1Spider(scrapy.Spider):
    """
    @title: 常州市政府采购网
    @href: http://zfcg.czfb.gov.cn/
    """
    name = 'jiangsu/changzhou/1'
    alias = '江苏/常州'
    allowed_domains = ['changzhou.gov.cn']
    start_urls = [
        ('http://zfcg.changzhou.gov.cn/html/ns/dlcg_cgyg/index.html', '预公告/采购预告'),
        ('http://zfcg.changzhou.gov.cn/html/ns/dlcg_cggg/index.html', '招标公告/采购公告'),
        ('http://zfcg.changzhou.gov.cn/html/ns/dlcg_cjgg/index.html', '中标公告/成交公告'),
        ('http://zfcg.changzhou.gov.cn/html/ns/dlcg_gzgg/index.html', '更正公告'),
        # ('http://zfcg.changzhou.gov.cn/html/ns/dlcg_fsgs/index.html', '其他公告/方式公示'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(xpath='//a[strong]/../a[@target="_blank"]',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()',
                                                    'subject': '../a[strong]//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('.NewsContent') or response.css('#czfxfontzoom')

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
