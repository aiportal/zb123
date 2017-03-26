import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem


class HefeiSpider(scrapy.Spider):
    name = 'anhui/hefei'
    alias = '安徽/合肥'
    allowed_domains = ['hfzfcg.gov.cn']
    start_urls = [
        ('http://www.hfzfcg.gov.cn/hfzbtb/ZtbPages/MoreInfo.aspx?CategoryNum=029002001001', '招标公告/工程建设'),
        ('http://www.hfzfcg.gov.cn/hfzbtb/ZtbPages/MoreInfo.aspx?CategoryNum=029002002001', '招标公告/政府采购'),
        ('http://www.hfzfcg.gov.cn/hfzbtb/ZtbPages/MoreInfo.aspx?CategoryNum=029002001002', '更正信息/工程建设'),
        ('http://www.hfzfcg.gov.cn/hfzbtb/ZtbPages/MoreInfo.aspx?CategoryNum=029002002002', '更正信息/政府采购')
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data})

    link_extractor = MetaLinkExtractor(css=('#SearchResult1_DataGrid1 tr > td > a',),
                                       attrs_xpath={'text': './/text()', 'area': '../../td[1]//text()',
                                                    'day': '../../td[last()]//text()'})
    page_extractor = NodeValueExtractor(css=('#SearchResult1_Pager a > img[src$="nextn.gif"]',),
                                        value_xpath='../@href')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        pager = self.page_extractor.extract_value(response) or ''
        target, arg = SpiderTool.re_text("__doPostBack\('(.+)','(\d+)'\)", pager)
        if target and arg:
            form = {
                '__EVENTTARGET': target,
                '__EVENTARGUMENT': arg,
            }
            yield scrapy.FormRequest.from_response(response, formdata=form, meta=response.meta)

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

