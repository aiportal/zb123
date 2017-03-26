import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem


class Tianjin2Spider(scrapy.Spider):
    name = 'tianjin/2'
    alias = '天津'
    allowed_domains = ['tjgp.gov.cn']
    start_urls = ['http://www.tjgp.gov.cn/portal/topicView.do']
    start_params = {
        'method': 'view',
        'view': 'Infor',
        'id': {
            '1662': '预公告/征求意见/市级', '1994': '预公告/征求意见/区县',
            '1665': '招标公告/市级', '1664': '招标公告/区县',
            '2014': '中标公告/市级', '2013': '中标公告/区县',
            '1663': '更正公告/市级', '1666': '更正公告/区县',
        },
        'page': '1',
        'step': '1',
    }

    def start_requests(self):
        url = self.start_urls[0]
        for form, data in SpiderTool.iter_params(self.start_params):
            yield scrapy.FormRequest(url, formdata=form, meta={'data': data, 'form': form})

    link_extractor = MetaLinkExtractor(css=('ul.dataList > li > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})
    page_extractor = NodeValueExtractor(css=('span.selectPage > a:contains(">")',), value_xpath='./@onclick')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        pager = self.page_extractor.extract_value(response) or ''
        page = SpiderTool.re_nums('findGoodsAndRef\((\d+),\d+\);', pager)
        if page:
            form = response.meta['form']
            form.update(page=str(page))
            yield scrapy.FormRequest(response.url, formdata=form, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('body > table') or response.css('body')

        day = FieldExtractor.date(data.get('day'), body)
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

