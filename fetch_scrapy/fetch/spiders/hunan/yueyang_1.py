import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class yueyang_1Spider(scrapy.Spider):
    """
    @title: 岳阳市公共资源交易中心
    @href: http://ggzy.yueyang.gov.cn/
    """
    name = 'hunan/yueyang/1'
    alias = '湖南/岳阳'
    allowed_domains = ['yueyang.gov.cn']
    start_urls = [
        ('http://ggzy.yueyang.gov.cn/004/004002/004002001/about-zfcg.html', '招标公告/政府采购'),
        ('http://ggzy.yueyang.gov.cn/004/004002/004002003/about-zfcg.html', '中标公告/政府采购'),
        ('http://ggzy.yueyang.gov.cn/004/004002/004002002/about-zfcg.html', '更正公告/政府采购'),
        ('http://ggzy.yueyang.gov.cn/004/004001/004001001/about-gcjs.html', '招标公告/建设工程'),
        ('http://ggzy.yueyang.gov.cn/004/004001/004001003/about-gcjs.html', '中标公告/建设工程'),
        ('http://ggzy.yueyang.gov.cn/004/004001/004001002/about-gcjs.html', '更正公告/建设工程'),
        ('http://ggzy.yueyang.gov.cn/004/004005/004005001/about03.html', '招标公告/医疗采购'),
        ('http://ggzy.yueyang.gov.cn/004/004005/004005003/about03.html', '中标公告/医疗采购'),
    ]

    link_extractor = MetaLinkExtractor(css='div.erjitongzhilist ul > li > a',
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
        body = response.css('div.xiangxiyekuang')

        day = FieldExtractor.date(data.get('day') or response.css('div.xiangxidate'))
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
