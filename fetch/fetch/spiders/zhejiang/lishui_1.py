import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class lishui_1Spider(scrapy.Spider):
    """
    @title: 丽水市公共资源交易网
    @href: http://www.lssggzy.com/lsweb/
    """
    name = 'zhejiang/lishui/1'
    alias = '浙江/丽水'
    # allowed_domains = ['lssggzy.com']     # 部分中标公告会转向县级网站
    start_urls = [
        ('http://www.lssggzy.com/lsweb/jyxx/071001/071001001/', '招标公告/建设工程'),
        ('http://www.lssggzy.com/lsweb/jyxx/071001/071001005/', '中标公告/建设工程'),
        ('http://www.lssggzy.com/lsweb/jyxx/071001/071001006/071001006001/', '招标公告/建设工程/小额'),
        ('http://www.lssggzy.com/lsweb/jyxx/071002/071002002/', '招标公告/政府采购'),
        ('http://www.lssggzy.com/lsweb/jyxx/071002/071002005/', '中标公告/政府采购'),
        ('http://www.lssggzy.com/lsweb/jyxx/071002/071002003/', '更正公告/政府采购'),
    ]

    link_extractor = MetaLinkExtractor(css='a[target=_blank][href^="/lsweb/infodetail"]',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()-1]//text()'})

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
        body = response.css('#TDContent, .infodetail') or response.css('#zoom') or response.css('.bt_content')
        if not body:
            href = SpiderTool.re_text("location='([^']+)'", response.css('script').extract_first())
            if href:
                url = urljoin(response.url, href)
                return [scrapy.Request(url, meta=response.meta, callback=self.parse_item)]

        day = FieldExtractor.date(data.get('day'), response.css('p.s-mid-content-date'))
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
