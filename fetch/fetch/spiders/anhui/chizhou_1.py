import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class haozhou_1Spider(scrapy.Spider):
    """
    @title: 池州市公共资源交易网
    @href: http://www.czztbj.cn/chiztpfront/
    """
    name = 'anhui/chizhou/1'
    alias = ''
    allowed_domains = ['czztbj.cn']
    start_urls = [
        ('http://www.czztbj.cn/chiztpfront/jyxx/002001/002001001/', '招标公告/建设工程'),
        ('http://www.czztbj.cn/chiztpfront/jyxx/002001/002001003/', '中标公告/建设工程'),
        ('http://www.czztbj.cn/chiztpfront/jyxx/002002/002002001/', '招标公告/政府采购'),
        ('http://www.czztbj.cn/chiztpfront/jyxx/002002/002002003/', '中标公告/政府采购'),

        ('http://www.czztbj.cn/chiztpfront/jyxx/002001/002001007/', '预公告/建设工程'),
        ('http://www.czztbj.cn/chiztpfront/jyxx/002002/002002005/', '预公告/政府采购'),
    ]

    link_extractor = MetaLinkExtractor(css='tr > td > a.WebList_sub',
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
        body = response.css('#TDContent, #trAttach')

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
