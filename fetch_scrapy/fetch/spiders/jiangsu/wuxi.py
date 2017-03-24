import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import json


class WuxiSpider(scrapy.Spider):
    name = 'jiangsu/wuxi'
    alias = '江苏/无锡'
    allowed_domains = ['wuxi.gov.cn']
    start_urls = ['http://cz.wuxi.gov.cn/intertidwebapp/docquery/queryDocments']
    start_params = {
        'currentPage': '1',
        'chanId': {
            '2098': '招标公告/采购公告',
            '2099': '更正公告',
            '2100': '中标公告/成交公告',
        }
    }

    def start_requests(self):
        url = self.start_urls[0]
        for form, data in SpiderTool.iter_params(self.start_params):
            yield scrapy.FormRequest(url, formdata=form, meta={'form': form, 'data': data}, dont_filter=True)

    def parse(self, response):
        pkg = json.loads(response.text)
        for row in pkg['list']:
            url = 'http://cz.wuxi.gov.cn/' + row['url']
            row['subject'] = response.meta['data']['chanId']
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

        count = int(pkg['pageCount'])
        page = int(pkg['pageIndex']) + 1
        if page < count:
            form = response.meta['form']
            form['currentPage'] = str(page)
            yield scrapy.FormRequest(response.url, formdata=form, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """

        data = response.meta['data']
        day = FieldExtractor.date(data.get('writeTime'), response.css('#sch_box > p.explain'))
        title = data.get('title') or data.get('text') or FieldExtractor.text(response.css('#sch_box > h1'))
        contents = response.css('#sch_box > div.Zoom').extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(response.css('#sch_box > div.Zoom')))
        return [g]
