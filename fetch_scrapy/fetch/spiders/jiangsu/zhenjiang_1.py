import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json


class JiangsuZhenjiang1Spider(scrapy.Spider):
    """
    @title: 镇江市公共资源交易中心
    @href: http://www.zjggzy.gov.cn/
    """
    name = 'jiangsu/zhenjiang/1'
    alias = '江苏/镇江'
    allowed_domains = ['zjggzy.gov.cn']
    start_urls = [
        ('http://www.zjggzy.gov.cn/services/ZjWebService/getGovInfoPubMoreInfo'
         '?response=application/json&pageIndex=1&pageSize=20&categorynum={}&title='.format(k), v)
        for k, v in [
            ('001001002001', '招标公告/工程建设'),
            ('001001005001', '中标公告/工程建设'),
            ('001002002', '招标公告/政府采购'),
            ('001002004', '中标公告/政府采购'),
            ('001002003', '变更公告/政府采购'),
            ('001006', '招标公告/水利工程'),
            ('001006002001', '中标公告/水利工程'),
            ('001007001001', '招标公告/交通工程'),
            ('001007004001', '中标公告/交通工程'),
        ]
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        """ 解析索引内容 """
        """
        {
            "infodate": "2017-04-26",
            "infoUrl": "/jyxx/001002/001002002/001002002001/20170426/48ad3099-c876-456b-9dbc-be7809e2959c.html",
            "title": "丹阳投资集团有限公司办公用房电梯采购及安装项目公开招标二次公告"
        },
        """
        res = json.loads(response.text)
        pkg = json.loads(res['return'])
        for row in pkg['Table']:
            url = urljoin(response.url, row['infoUrl'])
            row.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.article-content, #attach') or response.css('div.article-block')

        day = FieldExtractor.date(data.get('infodate'), response.css('div.info-sources'))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
