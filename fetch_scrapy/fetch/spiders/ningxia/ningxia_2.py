import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem


class Ningxia2Spider(scrapy.Spider):
    name = 'ningxia/2'
    alias = '宁夏'
    allowed_domains = ['nxgp.gov.cn']
    start_urls = ['http://www.nxgp.gov.cn/public/NXGPP/dynamic/contents/CGGG/index.jsp?cid=312&sid=1']
    start_params = {
        'type': {'101': '招标公告/公开招标', '108': '中标公告', '110': '更正公告'},
        'date': '0',
        'page': '0',
    }

    def start_requests(self):
        url = self.start_urls[0]
        for form, data in SpiderTool.iter_params(self.start_params):
            yield scrapy.FormRequest(url, formdata=form, meta={'data': data, 'form': form})

    link_extractor = MetaLinkExtractor(css=('table.list_table tr > td > a', ),
                                       attrs_xpath={'text': './/text()', 'title': '../@title',
                                                    'day': '../../td[last()]//text()'})
    page_extractor = NodeValueExtractor(css=('div.page-html > a:contains(下一页)',), value_xpath='./@onclick')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.url = 'http://www.nxgp.gov.cn/public/NXGPP/dynamic/' + lnk.meta['href']
            lnk.meta.update(subject=response.meta['data']['type'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        pager = self.page_extractor.extract_value(response) or ''
        page = SpiderTool.re_nums('doQuery\((\d+)\)', pager)
        if page:
            form = response.meta['form']
            form.update(page=str(page))
            yield scrapy.FormRequest(response.url, formdata=form,  meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        day = FieldExtractor.date(data.get('day'), response.css('#pubTime'))
        title = data.get('title') or data.get('text') or FieldExtractor.text(response.css('div.vT_detail_header > h2'))
        contents = (response.css('div.table > *') or response.css('#jjDiv')).extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(response.css('div.table')))
        return [g]
