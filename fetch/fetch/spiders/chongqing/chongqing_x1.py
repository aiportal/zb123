import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json


class chongqing_1Spider(scrapy.Spider):
    """
    @title: 重庆市政府采购网
    @href: https://www.cqgp.gov.cn/
    """
    name = 'chongqing/x1'
    alias = '重庆'
    allowed_domains = ['cqgp.gov.cn']
    start_urls = [
        ('https://www.cqgp.gov.cn/gwebsite/api/v1/notices/stable?pi=1&ps=20&type={}'.format(k), v)
        for k, v in [
            ('301,303', '预公告/政府采购'),
            ('100,200,201,202,203,204,205,206,207,309,400,401,402,3091,4001', '招标公告/政府采购'),
            ('300,302,304,3041,305,306,307,308', '中标公告/政府采购'),
        ]
    ]
    top_url = 'https://www.cqgp.gov.cn/notices/detail/{[id]}'
    detail_url = 'https://www.cqgp.gov.cn/gwebsite/api/v1/notices/stable/{[id]}'

    link_extractor = MetaLinkExtractor(css='tr > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        """ 解析JSON包 """
        """
        {
            "zbje": 0,
            "id": "435781498793324544",
            "noticeType": 301,
            "state": 4,
            "creatorOrgName": "重庆市武隆区公共资源综合交易中心",
            "issueTime": "2017-05-03 11:43:41",
            "districtName": "武隆区",
            "title": "重庆市武隆区妇幼保健院医疗设备(17A0098)预公示",
            "projectDirectoryName": "医疗设备",
            "projectDirectoryCode": "A0320",
            "projectBudget": 707350,
            "projectPurchaseWay": 100,
            "buyerName": "重庆市武隆区妇幼保健院",
            "agentName": "重庆市武隆区公共资源综合交易中心",
            "bidBeginTime": "2017-05-03 00:00:00",
            "bidEndTime": "2017-05-03 10:00:00",
            "openBidTime": "2017-05-03 10:00:00",
            "isIssue": "1",
            "packageNum": 3,
            "lastModify": "1493783020964"
        }
        """
        pkg = json.loads(response.text)
        for row in pkg['notices']:
            url = self.detail_url.format(row)
            top_url = self.top_url.format(row)
            row.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row, 'top_url': top_url}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        """
        {
            "res": 0,
            "msg": "成功",
            "notice": {
                "html": "...",
                "zbje": "0.00",
                "noticeType": 303,
                "state": 4,
                "creatorOrgName": "重庆天廷工程咨询有限公司",
                "issueTime": "2017-05-04 14:38:42",
                "title": "重庆市检察三分院机房网络设备(17A0598)预公示",
                "projectName": "重庆市检察三分院机房网络设备",
                "projectDirectoryName": "货物类",
                "projectBudget": "473780.00",
                "projectPurchaseWay": 300,
                "buyerName": "重庆市人民检察院第三分院",
                "agentName": "重庆天廷工程咨询有限公司",
                "projectPurchaseWayName": "竞争性谈判"
            },
            "refers": [
                {
                    "id": "436188584853336064",
                    "src": "436187896123453440",
                    "target": "432570740882239488",
                    "targetName": "重庆市检察三分院机房网络设备(17A0598)采购公告"
                }
            ],
            "redcount": 3
        }
        """
        pkg = json.loads(response.text)
        notice = pkg['notice']
        data = response.meta['data']

        day = FieldExtractor.date(data.get('issueTime'), notice.get('issueTime'))
        title = notice.get('projectName') or data.get('title') or notice.get('title')
        contents = notice.get('html')
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=notice.get('projectBudget'))
        pkg.update(data=data)
        g.set(extends=pkg)
        return [g]
