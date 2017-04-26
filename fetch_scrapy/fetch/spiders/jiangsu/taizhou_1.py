import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class JiangsuTaizhouSpider(scrapy.Spider):
    """
    @title: 泰州市公共资源交易网
    @href: http://www.tzzbtb.com/ggzy/
    """
    name = 'jiangsu/taizhou/1'
    alias = '江苏/泰州'
    allowed_domains = ['tzzbtb.com']
    start_urls = [
        ('http://www.tzzbtb.com/ggzy/jyxx/004001/004001001/', '招标公告/工程设计'),
        ('http://www.tzzbtb.com/ggzy/jyxx/004001/004001005/', '中标公告/工程设计'),
        ('http://www.tzzbtb.com/ggzy/jyxx/004002/004002001/', '招标公告/交通工程'),
        ('http://www.tzzbtb.com/ggzy/jyxx/004002/004002004/', '中标公告/交通工程'),
        ('http://www.tzzbtb.com/ggzy/jyxx/004003/004003001/', '预公告/政府采购'),
        ('http://www.tzzbtb.com/ggzy/jyxx/004003/004003002/', '招标公告/政府采购'),
        ('http://www.tzzbtb.com/ggzy/jyxx/004003/004003004/', '中标公告/政府采购'),
        ('http://www.tzzbtb.com/ggzy/jyxx/004007/004007001/', '招标公告/水利工程'),
        ('http://www.tzzbtb.com/ggzy/jyxx/004007/004007005/', '中标公告/水利工程'),
    ]

    link_extractor = MetaLinkExtractor(css='td.TDStyle > a',
                                       attrs_xpath={'text': '..//text()', 'day': '../../td[last()]//text()',
                                                    'area': '../font[1]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subjet=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#TDContent') or response.css('.infodetail') or response.css('#tblInfo')

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
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
