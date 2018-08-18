import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json


class pingtan_1Spider(scrapy.Spider):
    """
    @title: 平潭综合试验区招标投标信息网
    @href: http://www.ptzbtb.com/index.html
    """
    name = 'fujian/pingtan/1'
    alias = '福建/平潭'
    allowed_domains = ['ptzbtb.com']
    start_urls = [
        ('http://www.ptzbtb.com/Main/GetAllProject?pageIndex=1&pageSize=20', '招标公告',
         'http://www.ptzbtb.com/bidder_zbgg.html?tpid={0[tpid]}',
         'http://www.ptzbtb.com/Main/GetTpForRC?id={0[id]}'),
        ('http://www.ptzbtb.com/Main/BidList?pageIndex=1&pageSize=20', '中标公告',
         'http://www.ptzbtb.com/bidder_zb.html?tpid={0[tpid]}&id={0[id]}',
         'http://www.ptzbtb.com/Main/DiffBiderInfo?tpid={0[tpid]}&id={0[id]}'),
    ]

    def start_requests(self):
        for url, subject, top_url, req_url in self.start_urls:
            data = dict(subject=subject, top_url=top_url, req_url=req_url)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        """ 解析JSON包 """
        """
        {
            "result": true,
            "msg": "",
            "json": [{
                "total": 66,
                "rows": [
                    {
                        "id": "59092cfb49600111cc595519",
                        "TPName": "平潭商务运营中心配套酒店智能化系统工程施工项目",
                        "industry": "房建市政",
                        "createtime": "2017-05-03 09:50:07",
                        "tpid": "58b4334049600118b82a7820",
                        ...
                        "content": "<html>...</html>"
                    },
                    ...
                ]
            }]
        }
        """
        data = response.meta['data']
        pkg = json.loads(response.text)
        rows = pkg['json'][0]['rows']
        for row in rows:
            top_url = data['top_url'].format(row)
            req_url = data['req_url'].format(row)
            row.update(**data)
            yield scrapy.Request(req_url, meta={'data': row, 'top_url': top_url}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        """
        {
            "result": true,
            "msg": "",
            "json": {
                "id": "590967ba49600111cc7082d1",
                "createtime": "2017-05-03 13:16:42",
                "Content": "<html...>"
                "TPName": "平潭金井安置房一期Ⅱ标室外景观工程（施工）",
                "QuerstionEndTime": "2017-05-12 23:59:59",
                "QuestionBeginTime": "2017-05-05 00:00:00",
                "OpenBeginTime": "2017-05-31 09:30:00",
                "FieldUse": "开标一室",
                }
        }
        """
        pkg = json.loads(response.text)['json']
        data = response.meta['data']
        body = pkg.get('Content') or pkg['Evaluation'][0]['Content']
        try:
            attachments = [(urljoin(response.url, x['url']), x['name']) for x in json.loads(pkg.get('Attach', '[]'))]
            attach = ['<a href="{0}">{1}</a><br/>'.format(url, name) for url, name in attachments]
        except:
            attach = ''

        day = FieldExtractor.date(data.get('createtime'))
        title = data.get('TPName') or data.get('text')
        contents = [body, attach]
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
        g.set(extends=data)
        return [g]
