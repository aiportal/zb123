import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json
from datetime import datetime


class baoding_1Spider(scrapy.Spider):
    """
    @title: 保定市公共资源交易中心
    @href: http://www.bdggzy.com:90/
    """
    name = 'hebei/baoding/1'
    alias = '河北/保定'
    allowed_domains = ['bdggzy.com']
    start_urls = ['http://www.bdggzy.com:90/Portal/Zyjy/BulletinList']
    start_params = [
        ('招标公告/政府采购', {'category': '政府采购', 'type': '招标公告'}),
        ('中标公告/政府采购', {'category': '政府采购', 'type': '中标公告'}),
        ('招标公告/建设工程', {'category': '建设工程', 'type': '招标公告'}),
        ('中标公告/建设工程', {'category': '建设工程', 'type': '中标公告'}),
    ]
    default_param = {
        'xmmc': '',
        'container': 'divnews',
        'rows': '23',
        'page': '1',
    }
    detail_url = 'http://www.bdggzy.com:90/Portal/Zyjy/Info?sym=gg&id={0[Id]}'

    def start_requests(self):
        url = self.start_urls[0]
        for subject, param in self.start_params:
            data = dict(subject=subject)
            param.update(**self.default_param)
            yield scrapy.FormRequest(url, formdata=param, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        pkg = json.loads(response.text)
        for row in pkg['rows']:
            url = self.detail_url.format(row)
            row.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#Descr').xpath('./@value')

        tm = SpiderTool.re_nums('(\d+)', data['RecordInfo'].get('CreatedAt', '')) / 1000
        dt = datetime.fromtimestamp(tm)
        day = FieldExtractor.date(response.css('td.rq'), dt)
        title = data.get('Title') or data.get('text') or FieldExtractor.text(response.css('td.Tit'))
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
