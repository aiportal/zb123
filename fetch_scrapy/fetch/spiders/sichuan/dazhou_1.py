import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class dazhou_1Spider(scrapy.Spider):
    """
    @title: 达州市公共资源交易服务网
    @href: http://www.dzggzy.cn/dzsggzy/
    """
    name = 'sichuan/dazhou/1'
    alias = '四川/达州'
    allowed_domains = ['dzggzy.cn']
    start_urls = [
        ('http://www.dzggzy.cn/dzsggzy/jyxx/025001/025001001/', '招标公告/工程建设'),
        ('http://www.dzggzy.cn/dzsggzy/jyxx/025002/025002001/', '招标公告/政府采购'),
        ('http://www.dzggzy.cn/dzsggzy/jyxx/025002/025002005/', '中标公告/政府采购'),
        ('http://www.dzggzy.cn/dzsggzy/jyxx/025002/025002003/', '更正公告/政府采购'),
        ('http://www.dzggzy.cn/dzsggzy/jyxx/025002/025002006/', '废标公告'),
    ]

    link_extractor = MetaLinkExtractor(css='div.morecontent tr > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td//text()'})

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
        body = response.css('#TDContent, .infodetail, #filedown')

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
