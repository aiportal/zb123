import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import json
import re
import re


class SuzhouSpider(scrapy.Spider):
    """
    @title: 苏州市政府采购网
    @href: http://www.zfcg.suzhou.gov.cn/html/main/index.shtml
    """
    name = 'jiangsu/suzhou/1'
    alias = '江苏/苏州'
    allowed_domains = ['suzhou.gov.cn']
    start_urls = [
        ('http://www.zfcg.suzhou.gov.cn/content/searchContents.action',
         'http://www.zfcg.suzhou.gov.cn/html/project/{[PROJECTID]}.shtml')
    ]
    start_params = {
        'type': {'0': '招标公告', '2': '中标公告'},
        'zbCode': '',
        'page': '1',
        'rows': '30',
    }
    custom_settings = {'DOWNLOAD_DELAY': 3.81}
    custom_headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}

    def start_requests(self):
        url, detail = self.start_urls[0]
        for form, data in SpiderTool.iter_params(self.start_params):
            data.update(detail=detail)
            yield scrapy.FormRequest(url, formdata=form, meta={'data': data},
                                     headers=self.custom_headers, dont_filter=True)

    def parse(self, response):
        data = response.meta['data']
        pkg = json.loads(response.text)

        for row in pkg['rows']:
            url = data['detail'].format(row)
            row.update(**data)
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.Article')
        suffix = '\([A-Z0-9-]+\)$'

        day = FieldExtractor.date(data.get('RELEASE_TIME'), response.css('div.date'))
        title = data.get('TITLE') or ''
        title = re.sub(suffix, '', title)
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
