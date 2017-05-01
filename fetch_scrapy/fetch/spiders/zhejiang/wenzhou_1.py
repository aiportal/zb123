import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin, urlencode


class ZhejiangWenzhou1Spider(scrapy.Spider):
    """
    @title: 温州市公共资源交易网
    @href: http://www.wzzbtb.com/homepage/default.asp
    """
    name = 'zhejiang/wenzhou/1'
    alias = '浙江/温州'
    allowed_domains = ['wzzbtb.com']
    start_urls = ['http://www.wzzbtb.com/homepage/newxm.asp']
    start_params = [
        ({'lm1': '建设项目交易信息', 'lm2': '招标公告'}, '招标公告/建设工程'),
        ({'lm1': '建设项目交易信息', 'lm2': '中标结果'}, '中标公告/建设工程'),
        ({'lm1': '政府采购信息', 'lm2': '招标公告'}, '招标公告/政府采购'),
        ({'lm1': '政府采购信息', 'lm2': '中标公告'}, '中标公告/政府采购'),
    ]

    link_extractor = MetaLinkExtractor(css='tr[height="20"] > td > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../text()'})

    def start_requests(self):
        url = self.start_urls[0]
        for param, subject in self.start_params:
            body = urlencode(param, encoding='gb2312')
            data = dict(subject=subject)
            yield scrapy.Request(url, method='POST', body=body, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.xpath('//table[.//ol]') or response.css('table[width="670"]')

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
