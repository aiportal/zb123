import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class Sichuan1Spider(scrapy.Spider):
    """
    @title: 四川政府采购
    @href: http://www.sczfcg.com/view/srplatform/portal/index.html
    """
    name = 'sichuan/1'
    alias = '四川'
    allowed_domains = ['sczfcg.com']
    start_urls = [
        ('http://www.sczfcg.com/CmsNewsController.do?method=recommendBulletinList&moreType=provincebuyBulletinMore'
         '&channelCode={}&rp=25&page=1'.format(k), v)
        for k, v in [
            ('cgygg', '预公告/采购预告'),
            ('cggg', '招标公告/采购公告'),
            ('jggg', '中标公告/结果公告'),
            ('gzgg', '更正公告'),
            ('shiji_cggg1', '预公告/市县'),
            ('shiji_cggg', '招标公告/市县'),
            ('shiji_jggg', '中标公告/市县'),
            ('shiji_gzgg', '更正公告/市县'),
        ]
    ]

    link_extractor = MetaLinkExtractor(css='div.colsList > ul > li > a', url_attr='href',
                                       attrs_xpath={'text': './text()', 'start': '../span//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#myPrintArea, div.frameReport')

        day = FieldExtractor.date(data.get('day'), response.css('div.reportTitle span'))
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
