import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class bijie_1Spider(scrapy.Spider):
    """
    @title: 毕节公共资源交易中心
    @href: http://www.bjggzy.cn/
    """
    name = 'guizhou/bijie/1'
    alias = '贵州/毕节'
    allowed_domains = ['bjggzy.cn']
    start_urls = [
        # ('http://www.bjggzy.cn/gzfcg/index.jhtml',[
        #     ('div.TabbedPanelsContent:nth-child(1) ul > li > a', '招标公告/政府采购'),
        #     ('div.TabbedPanelsContent:nth-child(4) ul > li > a', '中标公告/政府采购'),
        # ]),
        # ('http://www.bjggzy.cn/gjsgc/index.jhtml', [
        #     ('div.TabbedPanelsContent:nth-child(1) ul > li > a', '招标公告/建设工程'),
        #     ('div.TabbedPanelsContent:nth-child(4) ul > li > a', '中标公告/建设工程'),
        # ]),
    ]

    custom_settings = {'COOKIES_ENABLED': True}

    def start_requests(self):
        for url, subjects in self.start_urls:
            data = dict(subjects=subjects)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        data = response.meta['data']
        for css, subject in data['subjects']:
            extractor = MetaLinkExtractor(css=css, attrs_xpath={'text': './/text()', 'day': '../span//text()'})
            links = extractor.links(response)
            assert links
            for lnk in links:
                lnk.meta.update(subject=subject)
                yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.Content > *:not(.TxtCenter)')

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
