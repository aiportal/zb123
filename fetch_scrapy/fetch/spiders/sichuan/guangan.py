import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem


class GuangAnSpider(scrapy.Spider):
    """
    @title: 广安公共资源交易网
    @href: http://www.gasggzy.com/
    @href: http://www.gasggzy.com/gasggzy/zwgk/
    """
    name = 'sichuan/guangan'
    alias = '四川/广安'
    start_urls = [
        ('http://www.gasggzy.com/gasggzy/gcjs/009001/{0}/MoreInfo.aspx?CategoryNum={0}'.format(k), v)
        for k, v in [
            ('009001001', '招标公告/工程建设'),
            ('009001004', '中标公告/工程建设'),
            ('009001002', '更正公告/工程建设'),
        ]
    ] + [
        ('http://www.gasggzy.com/gasggzy/zfcg/010001/{0}/MoreInfo.aspx?CategoryNum={0}'.format(k), v)
        for k, v in [
            ('010001002', '招标公告/政府采购'),
            ('010001003', '中标公告/政府采购'),
            ('010001004', '更正公告/政府采购'),
        ]
    ] + [
        ('http://www.gasggzy.com/gasggzy/zfcg/010002/010002002/MoreInfo.aspx?CategoryNum=010002002', '招标公告/政府采购/广安区'),
        ('http://www.gasggzy.com/gasggzy/zfcg/010003/010003002/MoreInfo.aspx?CategoryNum=010003002', '招标公告/政府采购/前锋区'),
        ('http://www.gasggzy.com/gasggzy/zfcg/010004/010004002/MoreInfo.aspx?CategoryNum=010004002', '招标公告/政府采购/岳池县'),
        ('http://www.gasggzy.com/gasggzy/zfcg/010005/010005002/MoreInfo.aspx?CategoryNum=010005002', '招标公告/政府采购/武胜县'),
        ('http://www.gasggzy.com/gasggzy/zfcg/010006/010006002/MoreInfo.aspx?CategoryNum=010006002', '招标公告/政府采购/邻水县'),
        ('http://www.gasggzy.com/gasggzy/zfcg/010007/010007002/MoreInfo.aspx?CategoryNum=010007002', '招标公告/政府采购/华蓥市'),
    ] + [
        # ('http://www.gasggzy.com/gasggzy/gcjs/009002/009002001/MoreInfo.aspx?CategoryNum=009002001', '招标公告/工程建设/广安区'),
        # ('http://www.gasggzy.com/gasggzy/gcjs/009003/009003001/MoreInfo.aspx?CategoryNum=009003001', '招标公告/工程建设/前锋区'),
        ('http://www.gasggzy.com/gasggzy/gcjs/009004/009004001/MoreInfo.aspx?CategoryNum=009004001', '招标公告/工程建设/岳池县'),
        ('http://www.gasggzy.com/gasggzy/gcjs/009006/009006001/MoreInfo.aspx?CategoryNum=009006001', '招标公告/工程建设/邻水县'),
        # ('http://www.gasggzy.com/gasggzy/gcjs/009005/009005001/MoreInfo.aspx?CategoryNum=009005001', '招标公告/工程建设/武胜县'),
        # ('http://www.gasggzy.com/gasggzy/gcjs/009007/009007001/MoreInfo.aspx?CategoryNum=009007001', '招标公告/工程建设/华蓥市'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            yield scrapy.Request(url, meta={'data': dict(subject=subject)})

    link_extractor = MetaLinkExtractor(css=('#MoreInfoList1_DataGrid1 tr > td > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})
    page_extractor = NodeValueExtractor(css=('#MoreInfoList1_Pager a > img[src$="nextn.gif"]',), value_xpath='../@href')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        # pager = self.page_extractor.extract_value(response) or ''
        # target, arg = SpiderTool.re_text("__doPostBack\('(.+)','(\d+)'\)", pager)
        # if target and arg:
        #     form = {
        #         '__EVENTTARGET': target,
        #         '__EVENTARGUMENT': arg,
        #     }
        #     yield scrapy.FormRequest.from_response(response, formdata=form, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.detail') or response.css('div.content') or response.css('div.page') \
            or response.css('div.container') \
            # or response.css('body')

        day = FieldExtractor.date(data.get('day'), response.css('p.publish-time'))
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
