import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class changde_1Spider(scrapy.Spider):
    """
    @title: 常德市公共资源交易网
    @href: http://www.cdggzy.net/cdweb/
    """
    name = 'hunan/changde/1'
    alias = '湖南/常德'
    allowed_domains = ['cdggzy.net']
    start_urls = [
        ('http://www.cdggzy.net/cdweb/jyxx/004002/004002001/', '招标公告/政府采购'),
        ('http://www.cdggzy.net/cdweb/jyxx/004002/004002002/', '中标公告/政府采购'),
        ('http://www.cdggzy.net/cdweb/jyxx/004002/004002003/', '更正公告/政府采购'),
        ('http://www.cdggzy.net/cdweb/jyxx/004001/004001001/', '招标公告/建设工程'),
        ('http://www.cdggzy.net/cdweb/jyxx/004001/004001002/', '中标公告/建设工程'),
        ('http://www.cdggzy.net/cdweb/jyxx/004001/004001003/', '更正公告/建设工程'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 3.88}

    link_extractor = MetaLinkExtractor(css='tr[height="22"] > td > a[target=_blank]',
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
        body = response.css('#InfoDetail_spnContent')

        day = FieldExtractor.date(data.get('day') or response.css('#InfoDetail_lblDate'))
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
