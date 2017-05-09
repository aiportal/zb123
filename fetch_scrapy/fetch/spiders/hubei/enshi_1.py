import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class enshi_1Spider(scrapy.Spider):
    """
    @title: 恩施州公共资源交易中心
    @href: http://www.eszggzy.cn/TPFront/
    """
    name = 'hubei/enshi/1'
    alias = '湖北/恩施'
    allowed_domains = ['eszggzy.cn']
    start_urls = [
        ('http://www.eszggzy.cn/TPFront/jyxx/070002/070002001/', '招标公告/政府采购'),
        ('http://www.eszggzy.cn/TPFront/jyxx/070002/070002003/', '中标公告/政府采购'),
        ('http://www.eszggzy.cn/TPFront/jyxx/070001/070001001/', '招标公告/建设工程'),
        ('http://www.eszggzy.cn/TPFront/jyxx/070001/070001003/', '中标公告/建设工程'),
        ('http://www.eszggzy.cn/TPFront/jyxx/070002/070002002/', '更正公告/政府采购'),
        ('http://www.eszggzy.cn/TPFront/jyxx/070001/070001002/', '更正公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='div.morelist tr > td > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()-1]//text()'})

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
        body = response.css('#TDContent, #filedown')

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
