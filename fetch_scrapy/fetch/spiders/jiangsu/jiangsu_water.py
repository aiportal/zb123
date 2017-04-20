import scrapy
from fetch.extractors import NodesExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json


class JiangsuWaterSpider(scrapy.Spider):
    """
    @title: 江苏省水利工程建设招标投标公共服务平台
    @href: http://221.226.253.14:84/Home/Index.aspx
    """
    name = 'jiangsu/water'
    alias = '江苏/水利'
    # allowed_domains = ['221.226.253.14']
    start_urls = [
        ('http://221.226.253.14:84/Home/List.aspx?type=3', '招标公告'),
        ('http://221.226.253.14:84/Home/List.aspx?type=2', '中标公告'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = NodesExtractor(css='#div dl > dd > a',
                                    attrs_xpath={'text': './/text()', 'day': '../span//text()'})
    page_extractor = NodeValueExtractor(css='#InfoPager a:contains(下一页)', value_xpath='./@href')

    def parse(self, response):
        links = self.link_extractor.extract_nodes(response)
        for lnk in links:
            target, argument = SpiderTool.re_text("__doPostBack\('(.+)','(.*)'\)", lnk['href'])
            form = {
                '__EVENTTARGET': target,
                '__EVENTARGUMENT': argument
            }
            lnk.update(**response.meta['data'])
            yield scrapy.FormRequest.from_response(response, formdata=form, meta={'data': lnk},
                                                   callback=self.parse_item, dont_filter=True)

        pager = self.page_extractor.extract_value(response) or ''
        target, argument = SpiderTool.re_text("__doPostBack\('(.+)','(\d+)'\)", pager)
        if target and argument:
            form = {
                '__EVENTTARGET': target,
                '__EVENTARGUMENT': argument
            }
            yield scrapy.FormRequest.from_response(response, formdata=form, meta=response.meta, dont_filter=True)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#lblHtml') or response.css('#tab')
        url = response.url
        ref = response.request.headers.get('Referer', b'').decode()

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.new(
            url=url,
            ref=ref,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
