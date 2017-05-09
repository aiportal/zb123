import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import re
from datetime import date


class Hebei2Spider(scrapy.Spider):
    """
    @title: 河北省公共资源交易服务平台
    @href: http://www.hebpr.cn/
    """
    name = 'hebei/2'
    alias = '河北'
    allowed_domains = ['hebpr.cn']
    start_urls = [
        ('http://www.hebpr.cn/002/002009/002009001/002009001001/1.html', '招标公告/政府采购'),
        # ('http://www.hebpr.cn/002/002009/002009001/002009001006/moreinfo.html', '中标公告/政府采购'),
        # ('http://www.hebpr.cn/002/002009/002009001/002009001002/moreinfo.html', '更正公告/政府采购'),
        ('http://www.hebpr.cn/002/002009/002009002/002009002001/moreinfo.html', '招标公告/工程建设'),
        ('http://www.hebpr.cn/002/002009/002009002/002009002005/moreinfo.html', '中标公告/工程建设'),
        # ('http://www.hebpr.cn/002/002009/002009002/002009002002/moreinfo.html', '更正公告/工程建设'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data})

    link_extractor = MetaLinkExtractor(css=('#categorypagingcontent > ul > li > a',),
                                       attrs_xpath={'text': './p[1]//text()',
                                                    'day': './p[2]/span//text()'})
    # page_extractor = MetaLinkExtractor(css=('div.pagemargin a:contains(下页)',))

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        # pager = self.page_extractor.links(response)
        # if pager:
        #     yield scrapy.Request(pager[0].url, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        prefix = '^【(.+)】\s*([A-Za-z0-9-]*)'

        day = FieldExtractor.date(data.get('day'), response.css('div.sub-title'), response.css('div.show-con'),
                                  str(date.today()))
        title = data.get('title') or data.get('text') or FieldExtractor.text(response.css('div.show-title'))
        title = re.sub(prefix, '', title or '')
        contents = response.css('div.show-con > *').extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        area, pid = SpiderTool.re_text(prefix, data.get('text', ''))
        g.set(area=[self.alias, area], pid=pid)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(response.css('div.show-con')))
        return [g]
