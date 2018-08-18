import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class xuancheng_1Spider(scrapy.Spider):
    """
    @title: 宣城市公共资源交易服务网
    @href: http://www.xcsztb.com/XCTPFront/
    """
    name = 'anhui/xuancheng/1'
    alias = '安徽/宣城'
    allowed_domains = ['xcsztb.com']
    start_urls = [
        ('http://www.xcsztb.com/XCTPFront/jsgc/', '建设工程'),
        ('http://www.xcsztb.com/XCTPFront/zfcg/', '政府采购'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 3.88}

    link_extractor = MetaLinkExtractor(css='div.s-block ul > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

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
        location = FieldExtractor.text(response.css('div.ewb-location')) or ''
        tail = [s.strip() for s in location.split('>>')][-1:][0]
        subject = {
            '招标公告': '招标公告',
            '中标公告': '中标公告',
            '采购公告': '招标公告',
            '结果公告': '中标公告',
        }.get(tail)
        if not subject:
            return []

        data = response.meta['data']
        body = response.css('#mainContent')

        day = FieldExtractor.date(data.get('day'), response.css('div.info-sources'))
        title = FieldExtractor.text(response.css('.article-title')) or data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias])
        g.set(subject=[subject, data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
