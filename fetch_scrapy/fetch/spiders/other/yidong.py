import scrapy
from fetch.extractors import NodesExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem


# 中国移动采购与招标网
# https://b2b.10086.cn


class YidongSpider(scrapy.Spider):
    name = 'other/yidong'
    alias = '其他/中国移动'
    allowed_domains = ['10086.cn']
    start_urls = [
        ('https://b2b.10086.cn/b2b/main/listVendorNoticeResult.html?noticeBean.noticeType=2', '招标公告'),
        ('https://b2b.10086.cn/b2b/main/listVendorNoticeResult.html?noticeBean.noticeType=7', '中标公告'),
    ]
    start_params = {
        'page.currentPage': '1',
        'page.perPageSize': '20',
        'noticeBean.sourceCH': '',
        'noticeBean.source': '',
        'noticeBean.title': '',
        'noticeBean.startDate': '',
        'noticeBean.endDate': '',
    }

    def start_requests(self):
        for url, subject in self.start_urls:
            form = self.start_params
            data = dict(subject=subject)
            yield scrapy.FormRequest(url, formdata=form, meta={'data': data, 'form': form})

    link_extractor = NodesExtractor(css=('table tr[onclick^=selectResult] > td > a',),
                                    attrs_xpath={'text': './/text()', 'value': '../../@onclick',
                                                 'area': '../../td[1]//text()', 'day': '../../td[last()]//text()'})
    page_extractor = NodeValueExtractor(css=('#pageid2 a:contains(下一页)',), value_xpath='./@onclick')

    def parse(self, response):
        nodes = self.link_extractor.extract_nodes(response)
        for node in nodes:
            value = SpiderTool.re_text("selectResult\('(.+)'\)", node['value'])
            url = 'https://b2b.10086.cn/b2b/main/viewNoticeContent.html?noticeBean.id=' + value
            node.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': node}, callback=self.parse_item)

        pager = self.page_extractor.extract_value(response) or ''
        page = SpiderTool.re_nums('gotoPage\((\d+)\)', pager)
        if page:
            form = response.meta['form']
            form.update(**{'page.currentPage': str(page)})
            yield scrapy.FormRequest(response.url, formdata=form, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#mobanDiv') or response.css('table.zb_table') or response.css('body')

        day = FieldExtractor.date(data.get('day'))
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
        return [g]
