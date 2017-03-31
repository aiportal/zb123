import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import json
from lxml import etree
import re


class ChengDuSpider(scrapy.Spider):
    """
    @title: 成都市公共资源交易服务中心
    @href: http://www.cdggzy.com/
    """
    name = 'sichuan/chengdu'
    alias = '四川/成都'
    start_urls = [
        ('http://www.cdggzy.com:8081/newsite/Notice/ListHandler.ashx?form=CgList&action=GetGG&{}'.format(k), v)
        for k, v in [
            ('classid=2&typeid=1', '招标公告/政府采购/成都'),
            ('classid=4&typeid=1', '中标公告/政府采购/成都'),
            ('classid=5&typeid=1', '更正公告/政府采购/成都'),
        ]
    ] + [
        ('http://www.cdggzy.com:8081/newsite/QXNotice/ListHandler.ashx?form=CgList&action=GetGG&{}'.format(k), v)
        for k, v in [
            ('classid=2&typeid=2', '招标公告/政府采购/成都'),
            ('classid=3&typeid=2', '中标公告/政府采购/成都'),
            ('classid=4&typeid=2', '更正公告/政府采购/成都'),
        ]
    ]
    start_params = {
        'pageindex': '1',
        'pagesize': '10',
    }

    def start_requests(self):
        for url, subject in self.start_urls:
            form = self.start_params
            data = dict(subject=subject)
            yield scrapy.FormRequest(url, formdata=form, meta={'data': data, 'form': form})

    def parse(self, response):
        pkg = json.loads(response.text)
        dom = etree.HTML(pkg['showinfo'])
        for elem in dom.xpath('.//a'):
            url = elem.get('href')
            data = {
                'text': (elem.xpath('.//text()') + [''])[0],
                'day': elem.findtext('../span[1]'),
            }
            yield scrapy.Request(url, meta={'data': data}, callback=self.parse_item)

        page, count = pkg['pageindex'] + 1, pkg['pagesum']
        if page < count:
            form = response.meta['form']
            form.update(pageindex=str(page))
            yield scrapy.FormRequest(response.url, formdata=form, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#ctl00_ContentPlaceHolder1_table') or response.css('div.content')

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub('^\[(.+)\]\s*', '', title)
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
