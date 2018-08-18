import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class xining_1Spider(scrapy.Spider):
    """
    @title: 西宁市公共资源交易中心
    @href: http://www.xnggzy.gov.cn/xnweb/
    """
    name = 'qinghai/xining/1'
    alias = '青海/西宁'
    allowed_domains = ['xnggzy.gov.cn']
    start_urls = [
        ('http://www.xnggzy.gov.cn/xnweb/zfcg/013001/', '招标公告/政府采购'),
        # ('http://www.xnggzy.gov.cn/xnweb/zfcg/013003/', '中标公告/政府采购'),
        # ('http://www.xnggzy.gov.cn/xnweb/zfcg/013002/', '招标公告/政府采购/更正公告'),
        # ('http://www.xnggzy.gov.cn/xnweb/zfcg/013004/', '中标公告/政府采购/废标公告'),
        #
        # ('http://www.xnggzy.gov.cn/xnweb/jsgc/012001/', '招标公告/建设工程'),
        # ('http://www.xnggzy.gov.cn/xnweb/jsgc/012003/', '中标公告/建设工程'),
        # ('http://www.xnggzy.gov.cn/xnweb/jsgc/012002/', '招标公告/建设工程/更正公告'),
        # ('http://www.xnggzy.gov.cn/xnweb/jsgc/012004/', '中标公告/建设工程/废标公告'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 3.80}

    link_extractor = MetaLinkExtractor(css='div.right-span-content tr > td > a[target=_blank]',
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
        body = response.css('#TDContent, #trAttach')
        prefix = '^\[\w{2,8}\]'
        suffix = '<font.+</font>$'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
        title = re.sub(suffix, '', title)
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
