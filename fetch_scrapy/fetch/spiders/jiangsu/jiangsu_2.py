import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json


class Jaingsu2Spider(scrapy.Spider):
    """
    @title: 江苏省公共资源交易电子服务平台
    @href: http://www.jsggzy.com.cn/
    """
    name = 'jiangsu/2'
    alias = '江苏'
    allowed_domains = ['jsggzy.com.cn']
    start_urls = [
        ('http://www.jsggzy.com.cn/services/JsggWebservice/getList'
         '?response=application/json&pageIndex=1&pageSize=15&categorynum={}&city=省级'.format(k), v)
        for k, v in [
            ('003001001', '招标公告/建设工程'),
            ('003001008', '中标公告/建设工程'),
            ('003002001', '招标公告/交通工程'),
            ('003002004', '中标公告/交通工程'),
            ('003003001', '招标公告/水利工程'),
            ('003003004', '中标公告/水利工程'),
            ('003004002', '招标公告/政府采购'),
            ('003004006', '中标公告/政府采购'),
            ('003004003', '更正公告/政府采购'),
        ]
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject, page=1, size=15)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        ret = json.loads(response.text)
        pkg = json.loads(ret['return'])
        for row in pkg['Table']:
            url = urljoin(response.url, row['href'])
            row.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

        data = response.meta['data']
        if pkg['RowCount'] == data['size']:
            data['page'] += 1
            url = SpiderTool.url_replace(response.url, pageIndex=data['page'])
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse_item(self, response):
        """ 解析详情页 """
        """
            city:"南京市"
            href:"/jyxx/003001/003001008/20170417/982.html"
            index:"1"
            infoid:"982"
            jyfl:"货物"
            number:"M3201000099000418001001"
            postdate:"2017-04-17"
            title:"南京禄口国际机场有限公司污水处理药剂采购采购结果公告"
        """
        data = response.meta['data']
        body = response.css('div.con')

        day = FieldExtractor.date(data.get('postdate'), response.css('p.info-sources'))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias, data.get('city')])
        g.set(subject=[data.get('subject'), data.get('jyfl')])
        g.set(budget=FieldExtractor.money(body))
        g.set(extends=data)
        return [g]
