import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class puyang_1Spider(scrapy.Spider):
    """
    @title: 濮阳市公共资源交易网
    @href: http://www.pyggzy.com/
    """
    name = 'henan/puyang/1'
    alias = '河南/濮阳'
    allowed_domains = ['pyggzy.com']
    start_urls = [
        ('http://www.pyggzy.com/list.asp?class=34', '招标公告/政府采购'),
        ('http://www.pyggzy.com/list.asp?class=35', '中标公告/政府采购'),
        ('http://www.pyggzy.com/list.asp?class=25', '招标公告/建设工程'),
        ('http://www.pyggzy.com/list.asp?class=26', '中标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='div.lm_c tr > td > a[target=_blank]',
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
        body = response.css('.ShowText') or response.css('div.lm_c')

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
