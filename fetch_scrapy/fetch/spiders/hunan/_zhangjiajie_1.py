import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json


class zhangjiajie_1Spider(scrapy.Spider):
    """
    @title: 张家界市公共资源交易网
    @href: http://zjjsggzy.gov.cn/index.html
    """
    name = 'hunan/zhangjiajie/1'
    alias = '湖南/张家界'
    allowed_domains = ['zjjsggzy.gov.cn']
    start_urls = [
        # ('http://zjjsggzy.gov.cn/TenderProject/GetTpList?page=1&records=15&category=政府采购', '招标公告/政府采购',
        #  'http://zjjsggzy.gov.cn/招标公告/tp-3/tenderViewIndex.html?flowId=56dd3e49f8d1281798bbd318&foId={[id]}',
        #  'http://zjjsggzy.gov.cn/TenderFlow/GetTpInfo?tpId={[id]}'),
        # ('http://zjjsggzy.gov.cn/TenderProject/GetBidderList?page=1&records=15&category=政府采购', '中标公告/政府采购',
        #  ''
        #  'http://zjjsggzy.gov.cn/BidderPublic/GetInfosByTpId?tpId={[id]}',),
        # ('http://zjjsggzy.gov.cn/TenderProject/GetTpList?page=1&records=15&IsShowOld=true'
        #  '&category=房建市政,水利,交通运输,土地开发整理,其他', '招标公告/建设工程'),
        # ('http://zjjsggzy.gov.cn/TenderProject/GetBidderList?page=1&records=15&IsShowOld=true'
        #  '&category=房建市政,水利,交通运输,土地开发整理,其他', '中标公告/建设工程'),
    ]
    # detail_url = 'http://zjjsggzy.gov.cn/BidderPublic/GetInfosByTpId?tpId={}'

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        pkg = json.loads(response.text)
        for row in pkg['json']:
            url = ''
            row.meta.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('')

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
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
