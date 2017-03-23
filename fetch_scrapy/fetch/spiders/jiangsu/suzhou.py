import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import json
import re


class SuzhouSpider(scrapy.Spider):
    name = 'jiangsu/suzhou'
    alias = '江苏/苏州'
    allowed_domains = ['zfcg.suzhou.gov.cn']
    start_url = 'http://www.zfcg.suzhou.gov.cn/content/cpContents.action'
    start_form = {
        'type': '',
        'title': '',
        'choose': '',
        'projectType': '0',
        'zbCode': '',
        'appcode': '',
        'page': '1',
        'rows': '30',
    }

    def start_requests(self):
        form = self.start_form
        yield scrapy.FormRequest(self.start_url, formdata=form, meta={'data': form})

    def parse(self, response):
        pkg = json.loads(response.text)

        links = [x for x in pkg['rows']]
        for link in links:      # type: dict
            link['url'] = 'http://www.zfcg.suzhou.gov.cn/html/project/{}.shtml'.format(link['ID'])
        links = SpiderTool.url_filter(links, lambda x: x['url'])
        for link in links:
            link['subject'] = '招标公告'
            yield scrapy.Request(link['url'], meta={'data': link}, callback=self.parse_item)

        data = response.meta['data']
        page = int(data['page'])
        rows = int(data['rows'])
        total = pkg['total']
        if (page * rows) <= total:
            data.update(page=str(page + 1))
            yield scrapy.FormRequest(response.url, formdata=data, meta={'data': data})

    def parse_item(self, response):
        """ 解析详情页 """

        data = response.meta['data']
        day = FieldExtractor.date(data.get('RELEASETIME'), data.get('#tab1 > date'), )
        title = re.sub('\(.+\)$', '', data.get('TITLE', ''))
        contents = response.css('#tab1 > div.Article').extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )

        g.set(area=self.alias)
        g.set(subject=[data.get('subject'), data.get('CATEGORY_TEXT')])
        g.set(budget=FieldExtractor.money(response.css('#tab1 > div.Article')))
        g.set(extends=data)
        return [g]

