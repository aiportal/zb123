import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class chuzhou_1Spider(scrapy.Spider):
    """
    @title: 滁州市公共资源交易中心
    @href: http://www.czggzy.gov.cn/Front_jyzx/
    """
    name = 'anhui/chuzhou/1'
    alias = '安徽/滁州'
    allowed_domains = ['czggzy.gov.cn']
    start_urls = [
        ('http://www.czggzy.gov.cn/Front_jyzx/jyxx/002005/002005001/', '招标公告/建设工程'),
        ('http://www.czggzy.gov.cn/Front_jyzx/jyxx/002006/002006001/', '中标公告/建设工程'),
        ('http://www.czggzy.gov.cn/Front_jyzx/jyxx/002005/002005002/', '招标公告/政府采购'),
        ('http://www.czggzy.gov.cn/Front_jyzx/jyxx/002006/002006002/', '中标公告/政府采购'),
    ]

    link_extractor = MetaLinkExtractor(css='div.right-wrap tr > td > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()-1]//text()'})

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
        data = response.meta['data']
        body = response.css('#TD1, #tr1') or response.css('div.article-text')
        if not body:
            href = SpiderTool.re_text("window.location='(.+)'", response.text)
            if href:
                url = urljoin(response.url, href)
                body = ['<a href="{}">公告内容</a>'.format(url)]
        prefix = '^\[\w{2,8}\]'
        suffix = '【\w{1,5}】$'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
        title = re.sub(suffix, '', title)
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
