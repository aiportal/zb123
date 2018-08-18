import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class manzhouli_1Spider(scrapy.Spider):
    """
    @title: 满洲里公共资源交易中心
    @href: http://www.mzlggzy.org.cn/
    """
    name = 'neimenggu/manzhouli/1'
    alias = '内蒙古/满洲里'
    allowed_domains = ['mzlggzy.org.cn']
    start_urls = [
        ('http://www.mzlggzy.org.cn/page/index.jspx?type=notice&code=biddingNotice_purchase', '招标公告/政府采购'),
        ('http://www.mzlggzy.org.cn/page/index.jspx?type=notice&code=getBidding_purchase', '中标公告/政府采购'),
        ('http://www.mzlggzy.org.cn/page/index.jspx?type=notice&code=biddingNotice_dyproject', '招标公告/建设工程'),
        ('http://www.mzlggzy.org.cn/page/index.jspx?type=notice&code=getBidding_dyproject', '中标公告/建设工程'),
        ('http://www.mzlggzy.org.cn/page/index.jspx?type=notice&code=change_dyproject', '更正公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='div.c1-bline a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../../div[last()-1]//text()'})

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
        body = response.css('div.content-page > section')
        prefix = '^\s*\[\w{2,8}\]\s*'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
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
