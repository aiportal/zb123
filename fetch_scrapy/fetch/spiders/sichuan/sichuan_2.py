import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json


class Sichuan2Spider(scrapy.Spider):
    name = 'sichuan/2'
    alias = '四川'
    allowed_domains = ['scztb.gov.cn']
    start_urls = [
        ('http://www.scztb.gov.cn/Home/GetTradeList?tradeName=Project&tradeType=TenderAnnQuaInqueryAnn', '招标公告/工程建设'),
        ('http://www.scztb.gov.cn/Home/GetTradeList?tradeName=Project&tradeType=WinResultAnno', '中标公告/工程建设'),
        ('http://www.scztb.gov.cn/Home/GetTradeList?tradeName=Purchase&tradeType=PurchaseBulletin', '招标公告/政府采购'),
        ('http://www.scztb.gov.cn/Home/GetTradeList?tradeName=Purchase&tradeType=PurchaseTermination', '更正公告/政府采购'),
        ('http://www.scztb.gov.cn/Home/GetTradeList?tradeName=Purchase&tradeType=PurchaseBid', '更正公告/政府采购'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = {'subject': subject, 'page': '1'}
            yield scrapy.Request(url, meta={'data': data})

    def parse(self, response):
        data = response.meta['data']
        pkg = json.loads(response.text)
        rows = json.loads(pkg['data'])
        for row in rows:          # type: dict
            url = urljoin('http://www.scztb.gov.cn', row['Link'])
            row.update(**data)
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

        # count = pkg['pageCount']
        # page = int(response.meta['data']['page']) + 1
        # if page < count:
        #     url = SpiderTool.url_replace(response.url, page=page)
        #     response.meta['data']['page'] = page
        #     yield scrapy.Request(url, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        day = FieldExtractor.date(data.get('CreateDateStr'), data.get('CreateDate'), )
        contents = response.css('div.projectcontent').extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=data.get('Title') or data.get('text'),
            contents=contents
        )

        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(response.css('div.projectcontent')))
        g.set(pid=data.get('ProjectCode'))
        g.set(extends=data)
        return [g]
