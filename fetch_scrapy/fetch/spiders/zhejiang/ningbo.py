import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from datetime import date


class NingboSpider(scrapy.Spider):
    name = 'zhejiang/ningbo'
    alias = '浙江/宁波'
    allowed_domains = ['nbzfcg.cn']
    start_urls = [
        # ('http://www.nbzfcg.cn/project/DemandNotice.aspx?NoticeType=2', '预公告'),   # 页面结构不同
        ('http://www.nbzfcg.cn/project/MoreNotice.aspx?Type=2', '招标公告'),
        ('http://www.nbzfcg.cn/project/MoreNotice.aspx?Type=3', '中标公告'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data})

    link_extractor = MetaLinkExtractor(
        css=('#ctl00_ContentPlaceHolder3_gdvNotice3 tr > td > a[href^="Notice_view.aspx"]',),
        attrs_xpath={'text': './/text()', 'area': '../../td[1]//text()', 'tender': '../../td[2]//text()',
                     'pid': '../../td[4]//text()', 'end': '../../td[last()]//text()'})
    page_extractor = NodeValueExtractor(
        css=('#ctl00_ContentPlaceHolder3_gdvNotice3_ctl18_AspNetPager1 a:contains(下页)',), value_xpath='./@href')

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
        body = response.css('#ctl00_ContentPlaceHolder3_lblNoticeContent') or response.css('body')

        day = FieldExtractor.date(body, str(date.today()))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias, data.get('area')])
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        g.set(tender=data.get('tender'))
        g.set(pid=data.get('pid'))
        g.set(end=FieldExtractor.date(data.get('end')))
        return [g]
