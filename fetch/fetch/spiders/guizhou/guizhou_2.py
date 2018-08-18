import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json
import re


class guizhou_2Spider(scrapy.Spider):
    """
    @title: 贵州省公共资源交易中心
    @href: http://www.gzsggzyjyzx.cn/
    """
    name = 'guizhou/2'
    alias = '贵州'
    allowed_domains = ['gzsggzyjyzx.cn']
    start_urls = ['http://www.gzsggzyjyzx.cn/ajax_trace']
    start_params = [
        ('招标公告/政府采购', {'cls': '4B', 'type': '4B1', 'classif_no': 'All', 'rownum': '20'}),
        ('中标公告/政府采购', {'cls': '4B', 'type': '4B2', 'classif_no': 'All', 'rownum': '20'}),
        ('招标公告/建设工程', {'cls': '4A', 'type': '4A1', 'classif_no': 'All', 'rownum': '20'}),
        ('中标公告/建设工程', {'cls': '4A', 'type': '4A2', 'classif_no': 'All', 'rownum': '20'}),
    ]

    def start_requests(self):
        url = self.start_urls[0]
        for subject, form in self.start_params:
            data = dict(subject=subject)
            yield scrapy.FormRequest(url, formdata=form, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        """ JSON """
        """
        {
            "dataList": [
                {
                    "list_id": "INF217000004745",
                    "title": "盘县2017年翰林片区城市棚户区改造项目施工二标段招标公告<font style=\"color:#f00;\">[报名中]</font>",
                    "inf_type": "4A1",
                    "page_url": "/content?cls=4A&id=INF217000004745",
                    "date": "2017-05-05",
                    "is_new": "1"
                },
            ]
        }
        """
        pkg = json.loads(response.text)
        for row in pkg['dataList']:
            url = urljoin(response.url, row['page_url'])
            row.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.detail_box')
        tail = '<font (.+)</font>$'
        symbol = '&[a-z]+;'

        day = FieldExtractor.date(data.get('date'), response.css('div.article_subtitle'))
        title = data.get('title') or data.get('text')
        title = re.sub(tail, '', title)
        title = re.sub(symbol, '', title)
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
