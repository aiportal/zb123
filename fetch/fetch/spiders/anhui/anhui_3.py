import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class anhui_3Spider(scrapy.Spider):
    """
    @title: 安徽省招标投标信息网
    @href: http://www.ahtba.org.cn/
    """
    name = 'anhui/3'
    alias = '安徽'
    allowed_domains = ['ahtba.org.cn']
    start_urls = [
        ('http://www.ahtba.org.cn/Notice/AnhuiNoticeSearch?spid=714&scid=597', '招标公告/建设工程'),
        ('http://www.ahtba.org.cn/Notice/AnhuiNoticeSearch?spid=714&scid=600', '中标公告/建设工程'),
        ('http://www.ahtba.org.cn/Notice/AnhuiNoticeSearch?spid=739&scid=740', '招标公告/政府采购'),
        ('http://www.ahtba.org.cn/Notice/AnhuiNoticeSearch?spid=739&scid=741', '中标公告/政府采购'),
        ('http://www.ahtba.org.cn/Notice/AnhuiNoticeSearch?spid=569&scid=604', '招标公告/其他'),
    ]
    detail_url = 'http://www.ahtba.org.cn/Notice/NoticeContent'

    link_extractor = MetaLinkExtractor(css='div.newsList ul > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            pid = SpiderTool.re_text('id=(\d+)', lnk.meta['href'])
            lnk.meta.update(**response.meta['data'])
            yield scrapy.FormRequest(self.detail_url, formdata={'id': pid}, dont_filter=True,
                                     meta={'top_url': lnk.url, 'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.newsBox') or response.css('div.new_detail') or response.css('div.page_detail2')

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
