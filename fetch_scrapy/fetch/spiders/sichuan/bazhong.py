import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem


class BaZhongSpider(scrapy.Spider):
    """
    @title: 巴中市政务服务和公共资源交易服务中心
    @href: http://www.bzggzy.gov.cn/
    """
    name = 'sichuan/bazhong'
    alias = '四川/巴中'
    start_urls = ['http://220.166.21.50:82/Article/SearchArticle']
    #     ('http://220.166.21.50:82/Category/More?id=643', '招标公告/建设工程'),
    #     ('http://220.166.21.50:82/Category/More?id=644', '中标公告/建设工程'),
    #     ('http://220.166.21.50:82/Category/More?id=666', '更正公告/建设工程'),
    #     ('http://220.166.21.50:82/Category/More?id=646', '招标公告/政府采购'),
    #     ('http://220.166.21.50:82/Category/More?id=647', '中标公告/政府采购'),
    #     ('http://220.166.21.50:82/Category/More?id=668', '更正公告/政府采购'),
    # ]
    start_params = {
        'categoryId': {
            '643': '招标公告/建设工程',
            '644': '中标公告/建设工程',
            '666': '更正公告/建设工程',
            '646': '招标公告/政府采购',
            '647': '中标公告/政府采购',
            '668': '更正公告/政府采购',
        },
        'typeId': '0',
        'pageNum': '1',
        'pageSize': '15',
        'search': 'false',
        'Title': '',
        'StartTime': '',
        'EndTime': '',
    }

    def start_requests(self):
        url = self.start_urls[0]
        for form, data in SpiderTool.iter_params(self.start_params):
            yield scrapy.FormRequest(url, formdata=form, meta={'data': data, 'form': form})

    link_extractor = MetaLinkExtractor(css=('#listCon ul > li > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})
    page_extractor = NodeValueExtractor(css=('div.pagination a:contains(下一页)',), value_xpath='./@onclick')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(subject=response.meta['data']['categoryId'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        pager = self.page_extractor.extract_value(response) or ''
        page, count = SpiderTool.re_nums('SearchArticleOnce\(\d+,\d+,(\d+),(\d+)\)', pager)
        if page < count:
            form = response.meta['form']
            form.update(pageNum=str(page))
            yield scrapy.FormRequest(response.url, formdata=form, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.content_box') or response.css('#content') or response.css('#textContent') \
            or response.css('div.new_detail') \
            # or response.css('body')

        day = FieldExtractor.date(data.get('day'), response.css('div.news_time'))
        title = data.get('title') or data.get('text') or FieldExtractor.text(response.css('div.news_tit'))
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
