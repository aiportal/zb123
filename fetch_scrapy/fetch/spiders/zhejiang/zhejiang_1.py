import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class Zhejiang1Spider(scrapy.Spider):
    """
    @title: 浙江政府采购
    @href: http://www.zjzfcg.gov.cn/new/
    """
    name = 'zhejiang/1'
    alias = '浙江'
    allowed_domains = ['zjzfcg.gov.cn']
    start_urls = [
        ('http://www.zjzfcg.gov.cn/new/articleSearch/search_search.do?count=30&chnlIds={}'.format(k), v)
        for k, v in [
            ('206,210', '预公告/采购预告'),
            ('207,211', '招标公告/采购公告'),
            # ('208,212', '中标公告/中标成交公示'),
            ('209,213', '中标公告'),
            # ('401,411', '其他公告/采购合同公告'),
            # ('402,412', '其他公告/竞争性磋商公告'),
            # '245': '其他公告/单一来源公示',
            # '445,400,410': '其他公告/进口产品公示',
            # '246,405,415': '其他公告/采购文件或需求公示'
        ]
    ]

    link_extractor = MetaLinkExtractor(css='.artcon_new > li > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'end': '../span//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#news_content')
        pid = '（[A-Z0-9-]+\）'

        day = FieldExtractor.date(data.get('day'), response.css('#news_msg'), data.get('end'))
        title = data.get('title') or data.get('text')
        title = re.sub(pid, '', title)
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
