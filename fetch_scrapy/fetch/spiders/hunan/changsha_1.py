import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class changsha_1Spider(scrapy.Spider):
    """
    @title: 长沙公共资源交易监管网
    @href: http://csggzy.gov.cn/front.aspx/Index
    """
    name = 'hunan/changsha/1'
    alias = '湖南/长沙'
    allowed_domains = ['csggzy.gov.cn']
    start_urls = [
        ('https://csggzy.gov.cn/NoticeFile/Index?type=101&Sm=房建市政&Ptype=工程建设&Sm2=招标公告', '招标公告/工程建设'),
        ('https://csggzy.gov.cn/NoticeFile/Index?type=101&Sm=房建市政&Ptype=工程建设&Sm2=中标候选人公示', '中标公告/工程建设'),
        ('https://csggzy.gov.cn/NoticeFile/Index?type=102&Sm=政府采购&Ptype=政府采购&Sm2=招标公告', '招标公告/政府采购'),
        ('https://csggzy.gov.cn/NoticeFile/Index?type=102&Sm=政府采购&Ptype=政府采购&Sm2=结果公告', '中标公告/政府采购'),
        ('https://csggzy.gov.cn/NoticeFile/Index?type=104&Sm=医药采购&Ptype=医药采购&Sm2=招标公告', '招标公告/医药采购'),
        ('https://csggzy.gov.cn/NoticeFile/Index?type=104&Sm=医药采购&Ptype=医药采购&Sm2=结果公告', '中标公告/医药采购'),
    ]

    link_extractor = MetaLinkExtractor(css='#formSearch + div tr > td > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

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
        body = response.css('#cont')

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
