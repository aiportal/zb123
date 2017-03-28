import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import re


# 中华人民共和国工业和信息化部，通信工程建设项目招标投标管理信息平台
# https://txzb.miit.gov.cn


class TongxinSpider(scrapy.Spider):
    name = 'other/tongxin'
    alias = '其他/通信'
    allowed_domains = ['miit.gov.cn']
    start_urls = [
        ('https://txzb.miit.gov.cn/DispatchAction.do?efFormEname=POIX14&pagesize=11', '招标公告'),
        # ('https://txzb.miit.gov.cn/DispatchAction.do?efFormEname=POIX12&type=2', '中标公告'),
    ]
        # 'https://txzb.miit.gov.cn/DispatchAction.do?reg=denglu&pagesize=11']
    # start_params = {
    #     'efFormEname': {'POIX14': '招标公告'},
    #     # 'methodName': 'queryZhongbiao',
    #     'page': '1',
    # }

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='#newsItem tr > td > a', attrs_xpath={'text': './/text()'})
    page_extractor = NodeValueExtractor(css='#pageFrm td:contains(下一页)', value_xpath='./@page')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        pager = self.page_extractor.extract_value(response) or ''
        if pager:
            form = {'page': pager}
            yield scrapy.FormRequest.from_response(response, formdata=form, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#ef_region_inqu table') or response.css('body')

        day = FieldExtractor.date(data.get('text'))
        title = data.get('title') or re.sub('\s*\d{4}-\d{2}-\d{2}\s*$', '', data.get('text', ''))
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
