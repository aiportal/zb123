import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import json
# import re
# from urllib.parse import urljoin


class Hefei2Spider(scrapy.Spider):
    """
    @title: 安徽合肥公共资源交易中心
    @href: http://www.hfggzy.com/hfzbtb/
    """
    name = 'anhui/hefei_2'
    alias = '合肥'
    allow_domains = ['hfggzy.com']
    start_urls = [
        ('http://www.hfggzy.com:7090/fulltextsearch/rest/getfulltextdata?format=json&rmk3={}&pn=1&rn=20'.format(k), v)
        for k, v in [
            ('029002001001', '招标公告/工程建设'),
            ('029002002001', '招标公告/政府采购'),
        ]
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject, page='1', size='20')
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        """ 解析索引包 """
        """
            "result": {
                "totalcount": "29732",
                "executetime": "0.172",
                "records": [...]
        """
        pkg = json.loads(response.text)
        records = pkg['result']['records']
        for r in records:
            # r['link'] = re.sub('Jump\?', 'Jump/?', r['link'])
            r.update(**response.meta['data'])
            yield self._parse_item(response, r)
            # yield scrapy.Request(r['link'], meta={'data': r}, callback=self.jump_detail)

        page = int(response.meta['data']['page']) + 1
        size = int(response.meta['data']['size'])
        count = int(pkg['result']['totalcount'])
        if page * size < count:
            url = SpiderTool.url_replace(response.url, pn=page)
            response.meta['data']['page'] = str(page)
            yield scrapy.Request(url, meta=response.meta)

    def _parse_item(self, response, data):
        """ 解析详情项 """
        """
        {
            "title": "高速·滨湖时代广场C1#楼酒店厨房设备采购及安装",
            "content": "高速·滨湖时代广场C1#楼酒店厨房 ...",
            "link": "http://www.hfggzy.com/hfzbtb/Jump?InfoID=557382&CategoryNum=029002001001",
            "date": "2017-04-19 09:00:00",
            "folder": "Web",
            "categoryname": "网站",
            "guid": "557382",
            "remark1": "公开招标",
            "remark3": "029002001001",
            "remark2": "代理"
        },
        """
        day = FieldExtractor.date(data.get('date'))
        title = data.get('title')
        contents = [data.get('content')]
        g = GatherItem.new(
            url=data['link'],
            ref=response.url,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money([data.get('content')]))
        g.set(pid=data.get('guid'))
        return g

    # def jump_detail(self, response):
    #     script = FieldExtractor.text(response.css('script'))
    #     href = SpiderTool.re_text("location\.href='(.+)'", script)
    #     url = urljoin(response.url, href)
    #     yield scrapy.Request(url, meta=response.meta, callback=self.parse_item)
    #
    # def parse_item(self, response):
    #     """ 解析详情页 """
    #     """
    #     {
    #         "title": "高速·滨湖时代广场C1#楼酒店厨房设备采购及安装",
    #         "content": "高速·滨湖时代广场C1#楼酒店厨房 ...",
    #         "link": "http://www.hfggzy.com/hfzbtb/Jump?InfoID=557382&CategoryNum=029002001001",
    #         "date": "2017-04-19 09:00:00",
    #         "folder": "Web",
    #         "categoryname": "网站",
    #         "guid": "557382",
    #         "remark1": "公开招标",
    #         "remark3": "029002001001",
    #         "remark2": "代理"
    #     },
    #     """
    #     data = response.meta['data']
    #     body = response.css('#TDContent, #trAttach')
    #
    #     day = FieldExtractor.date(data.get('date'), response.css('#tdTitle'))
    #     title = data.get('title') or data.get('text')
    #     contents = body.extract()
    #     g = GatherItem.create(
    #         response,
    #         source=self.name.split('/')[0],
    #         day=day,
    #         title=title,
    #         contents=contents
    #     )
    #     g.set(area=self.alias)
    #     g.set(subject=data.get('subject'))
    #     g.set(budget=FieldExtractor.money(body))
    #     g.set(pid=data.get('guid'))
    #     return [g]
