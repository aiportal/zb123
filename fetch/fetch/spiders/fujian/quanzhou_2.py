import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json


class quanzhou_2Spider(scrapy.Spider):
    """
    @title: 泉州市公共资源交易信息网
    @href: http://www.qzzb.gov.cn/default/homePage.do
    """
    name = 'fujian/quanzhou/2'
    alias = '福建/泉州'
    allowed_domains = ['qzzb.gov.cn']
    start_urls = [
        # ('http://www.qzzb.gov.cn/default/getTradeInfoList.do', '招标公告/建设工程', '{projType:1,centerId:0,rcdSize:50}',
        #  'http://www.qzzb.gov.cn/project/projectInfo.do?projId={[bltId]}'),
        #
        # ('http://www.qzzb.gov.cn/default/getTradeResult.do', '中标公告/建设工程', '{projType:1,centerId:0,rcdSize:50}',
        #  'http://www.qzzb.gov.cn/project/projectInfo.do?projId={[bltId]}&leftIndex=3'),

        ('http://www.qzzb.gov.cn/default/getTradeInfoList.do', '招标公告/政府采购', '{projType:2,centerId:0,rcdSize:50}',
         'http://www.qzzb.gov.cn/govProcurement/govProcurementDetail.do?bltId={[bltId]}'),

        ('http://www.qzzb.gov.cn/default/getTradeResult.do', '中标公告/政府采购', '{projType:2,centerId:0,rcdSize:50}',
         'http://www.qzzb.gov.cn/govProcurement/govProcurementDetail.do?bltId={[bltId]}'),
    ]

    def start_requests(self):
        headers = {'Content-Type': 'application/json;charset=UTF-8'}
        for url, subject, body, detail in self.start_urls:
            data = dict(subject=subject, detail=detail)
            yield scrapy.Request(url, method='POST', body=body, headers=headers, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        """ 解析JSON包 """
        """
        {
            "result": true,
            "data": [
                {
                    "bltTitle": "泉州台商投资区近期（2015-2017年度）污水管网连通收集工程",
                    "pubDate": "2017-05-05",
                    "bltId": 21179,
                    "projType": 1,
                },
                ...
            ]
        }
        """
        data = response.meta['data']
        pkg = json.loads(response.text)
        for row in pkg['data']:
            url = data['detail'].format(row)
            row.update(**data)
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.xpath('//div[@id="gpContent"]')

        day = FieldExtractor.date(data.get('pubDate'), response.xpath('//div[@id="gpPubDate"]'))
        title = data.get('bltTitle') or FieldExtractor.text(response.xpath('//div[@id="gpTitle"]'))
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
