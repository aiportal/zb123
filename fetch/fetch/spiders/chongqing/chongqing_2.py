import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json


class chongqing_2Spider(scrapy.Spider):
    """
    @title: 重庆市公共资源交易网
    @href: http://www.cqggzy.com/
    """
    name = 'chongqing/2'
    alias = '重庆'
    allowed_domains = ['cqggzy.com']
    start_urls = [
        ('http://www.cqggzy.com/services/PortalsWebservice/getInfoList?response=application/json'
         '&pageIndex=1&pageSize=18&siteguid=d7878853-1c74-4913-ab15-1d72b70ff5e7&categorynum={}'
         '&title=&infoC='.format(k), v)
        for k, v in [
            ('014001001', '招标公告/建设工程'),
            ('014001004', '中标公告/建设工程'),
            ('014005001', '招标公告/政府采购'),
            ('014005004', '中标公告/政府采购'),
        ]
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        """ 解析数据包 """
        """
        {"return":"[{
            "infourl": "/xxhz/014001/014001001/014001001003/20170503/6112b84f-fa15-4b35-b1e3-f263964f6edc.html",
            "title": "云阳县蔈草镇蔈草社区撤并村（龙山、谭家村）通畅工程（水泥厂-雷家沟）招标公告",
            "index": "1",
            "infodate": "2017-05-03",
            "infoC": "云阳县"
        }]"}
        """
        res = json.loads(response.text)
        rows = json.loads(res['return'])
        for row in rows:
            url = urljoin(response.url, row['infourl'])
            row.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#mainContent, #yewuxitong')

        day = FieldExtractor.date(data.get('infodate'))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias, data.get('infoC')])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
