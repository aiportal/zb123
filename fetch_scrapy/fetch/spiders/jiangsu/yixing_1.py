import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class yixing_1Spider(scrapy.Spider):
    """
    @title: 宜兴市招投标网
    @href: http://www.yxztb.net/yxweb/
    """
    name = 'jiangsu/yixing/1'
    alias = '江苏/宜兴'
    allowed_domains = ['yxztb.net']
    start_urls = [
        ('http://www.yxztb.net/yxweb/zypd/012001/012001007/', '预公告/工程建设'),
        ('http://www.yxztb.net/yxweb/zypd/012001/012001001/', '招标公告/工程建设'),
        ('http://www.yxztb.net/yxweb/zypd/012001/012001006/', '中标公告/工程建设'),
        ('http://www.yxztb.net/yxweb/zypd/012001/012001008/', '其他公告/废标公告'),
        ('http://www.yxztb.net/yxweb/zypd/012002/012002001/', '招标公告/政府采购'),
        ('http://www.yxztb.net/yxweb/zypd/012002/012002004/', '中标公告/政府采购'),
        ('http://www.yxztb.net/yxweb/zypd/012002/012002002/', '更正公告/政府采购'),
    ]

    link_extractor = MetaLinkExtractor(css='#moreinfopage tr > td.tdmoreinfosub > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

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
        body = response.css('#TDContent, .infodetail, #trAttach') or response.css('#tblInfo')

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
