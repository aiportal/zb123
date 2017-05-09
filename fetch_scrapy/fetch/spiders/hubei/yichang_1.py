import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class yichang_1Spider(scrapy.Spider):
    """
    @title: 宜昌公共资源交易信息网
    @href: http://www.ycztb.com/TPFront/
    """
    name = 'hubei/yichang/1'
    alias = '湖北/宜昌'
    allowed_domains = ['ycztb.com']
    start_urls = [
        ('http://www.ycztb.com/TPFront/jyxx/003002/003002001/', '招标公告/政府采购'),
        ('http://www.ycztb.com/TPFront/jyxx/003002/003002003/', '中标公告/政府采购'),
        ('http://www.ycztb.com/TPFront/jyxx/003001/003001001/', '招标公告/建设工程'),
        ('http://www.ycztb.com/TPFront/jyxx/003001/003001004/', '中标公告/建设工程'),
        # ('http://www.ycztb.com/TPFront/jyxx/003002/003002004/', '废标公告/工程建设'),
        # ('http://www.ycztb.com/TPFront/jyxx/003001/003001005/', '废标公告/工程建设'),
    ]

    link_extractor = MetaLinkExtractor(css='div.r-item ul.list > li > a[target=_blank]',
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
        body = response.css('#mainContent')

        day = FieldExtractor.date(data.get('day'), response.css('div.detail-info'))
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
