import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json


class ningde_1Spider(scrapy.Spider):
    """
    @title: 宁德市公共资源交易网
    @href: http://ggzyw.ningde.gov.cn:9120/
    """
    name = 'fujian/ningde/1'
    alias = '福建/宁德'
    allowed_domains = ['ningde.gov.cn']
    start_urls = [
        ('http://ggzyw.ningde.gov.cn:9120/tenderproject/GetTpAllInfo?page=3&records=15', '招标公告',
         'http://ggzyw.ningde.gov.cn:9120/fjebid/jypt.html?type=招标公告&tpid={[id]}',
         'http://ggzyw.ningde.gov.cn:9120/Audit/GetRecord?id={[id]}'),
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
            "json": {
                "total": 1259,
                "page": 3,
                "records": 15,
                "rows": [...]
            }
        }
        """
        data = response.meta['data']
        pkg = json.loads(response.text)
        for row in pkg['json']['rows']:
            top_url = data['top_url'].format(row)
            req_url = data['req_url'].format(row)
            row.update(**data)
            yield scrapy.Request(req_url, meta={'top_url': top_url, 'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        """
        {
            "result": true,
            "msg": "",
            "json": [{
                "Data": {
                    "招标标题": "中国历史文化名镇（霍童）保护与旅游开发项目—古镇民居立面改造工程设计",
                    "开标时间": "2017-05-23 09:00:00",
                    ...
                    "所属地区": "蕉城区",
                    "行业类型": "工程建设",
                    "category": "房屋市政",
                    "Type": "施工",
                    "Category": "直接发布",
                    "Eval": "直接发布"

                    "招标内容": " ... "     # HTML
                },
                ...
                "RecordTime": "2017-04-28 16:58:29"
                }
            ]
        }
        """
        """
        {
                "id": "5901a1405f3bccdea44c6c19",
                "招标标题": "射箭竞赛专用器械采购项目",
                "region": "",
                "time": "2017-04-27 15:44:00",
                "type": "施工",
                "状态": "",
                "答疑": false,
                "补充通知": false,
                "中标公示": false,
                "保证金退还": false
        }
        """
        pkg = json.loads(response.text)
        pkg_data = pkg['json'][0]['Data']
        data = response.meta['data']
        body = pkg_data.get('招标内容')

        day = FieldExtractor.date(data.get('time'))
        title = data.get('招标标题') or data.get('标题')
        contents = [body]
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias, pkg_data.get('所属地区')])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        g.set(extends=data)
        return [g]
