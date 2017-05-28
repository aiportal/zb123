import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class pingdingshan_1Spider(scrapy.Spider):
    """
    @title: 平顶山市公共资源交易网
    @href: http://www.pdsggzy.com/
    """
    name = 'henan/pingdingshan/1'
    alias = '河南/平顶山'
    allowed_domains = ['pdsggzy.com']
    start_urls = [
        ('http://www.pdsggzy.com/zzbgg/index.jhtml', '招标公告/政府采购'),
        ('http://www.pdsggzy.com/zzbgs/index.jhtml', '中标公告/政府采购'),
        ('http://www.pdsggzy.com/gzbgg/index.jhtml', '招标公告/建设工程'),
        ('http://www.pdsggzy.com/gzbgs/index.jhtml', '中标公告/建设工程'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 5.28}

    link_extractor = MetaLinkExtractor(css='div.infolist-main ul > li > a',
                                       attrs_xpath={'text': './span//text()', 'day': './em//text()'})

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
        body = response.css('div.s_content')

        day = FieldExtractor.date(data.get('day'), response.css('div.s_date'))
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
