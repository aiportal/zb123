import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class deyang_1Spider(scrapy.Spider):
    """
    @title: 德阳市公共资源交易信息网
    @href: http://ggzyxx.deyang.gov.cn/index.html
    """
    name = 'sichuan/deyang/1'
    alias = '四川/德阳'
    allowed_domains = ['deyang.gov.cn']
    start_urls = [
        ('http://ggzyxx.deyang.gov.cn/tradingClass_bfbfc9ef3ed74c36b1748b5d7adbe94a.html', '招标公告/建设工程'),
        ('http://ggzyxx.deyang.gov.cn/tradingClass_6f285df4d2934bc68fe1c940c613e788.html', '招标公告/政府采购'),
    ]
    start_params = {
        'category_id': 'bfbfc9ef3ed74c36b1748b5d7adbe94a',
        'area': '0',
        'currentPage': '1',
    }

    link_extractor = MetaLinkExtractor(css='div.news-list ul > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

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
        body = response.css('.table_detail, .content_box') or response.css('.text-wrap') or response.css('.detail-box')

        day = FieldExtractor.date(data.get('day'), response.css('div.big-tit-wrap'))
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
