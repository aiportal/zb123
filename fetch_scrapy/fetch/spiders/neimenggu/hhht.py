import scrapy
from fetch.items import GatherItem
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
import re


class HhhtSpider(scrapy.Spider):
    """
    @title: 呼和浩特市公共资源交易中心
    @href: http://www.ggzyjy.com.cn/hsweb/
    """
    name = 'neimenggu/hhht'
    alias = '内蒙古/呼和浩特'
    allowed_domains = ['ggzyjy.com.cn']

    start_urls = [
        # 政府采购
        ('http://www.ggzyjy.com.cn/hsweb/004/004002/004002001/MoreInfo.aspx?CategoryNum=004002001', '招标公告/政府采购'),
        ('http://www.ggzyjy.com.cn/hsweb/004/004002/004002003/MoreInfo.aspx?CategoryNum=004002003', '中标公告/政府采购'),
        ('http://www.ggzyjy.com.cn/hsweb/004/004002/004002004/MoreInfo.aspx?CategoryNum=004002004', '更正公告/政府采购'),
        # ('http://www.ggzyjy.com.cn/hsweb/004/004002/004002007/MoreInfo.aspx?CategoryNum=004002007', '其他公告/废标公告/政府采购'),
        # 建设工程
        ('http://www.ggzyjy.com.cn/hsweb/004/004001/004001001/MoreInfo.aspx?CategoryNum=004001001', '招标公告/建设工程'),
        ('http://www.ggzyjy.com.cn/hsweb/004/004001/004001002/MoreInfo.aspx?CategoryNum=004001002', '更正公告/建设工程'),
        ('http://www.ggzyjy.com.cn/hsweb/004/004001/004001003/MoreInfo.aspx?CategoryNum=004001003', '招标公告/建设工程'),
        # 交通工程
        ('http://www.ggzyjy.com.cn/hsweb/004/004010/004010001/MoreInfo.aspx?CategoryNum=004010001', '招标公告/交通工程'),
        ('http://www.ggzyjy.com.cn/hsweb/004/004010/004010002/MoreInfo.aspx?CategoryNum=004010002', '更正公告/交通工程'),
        ('http://www.ggzyjy.com.cn/hsweb/004/004010/004010003/MoreInfo.aspx?CategoryNum=004010003', '中标公示/交通工程'),
        # 水利工程
        ('http://www.ggzyjy.com.cn/hsweb/004/004011/004011001/MoreInfo.aspx?CategoryNum=004011001', '招标公告/水利工程'),
        ('http://www.ggzyjy.com.cn/hsweb/004/004011/004011002/MoreInfo.aspx?CategoryNum=004011002', '更正公告/水利工程'),
        ('http://www.ggzyjy.com.cn/hsweb/004/004011/004011003/MoreInfo.aspx?CategoryNum=004011003', '中标公告/水利工程'),
        # 电力工程
        ('http://www.ggzyjy.com.cn/hsweb/004/004012/004012001/MoreInfo.aspx?CategoryNum=004012001', '招标公告/电力工程'),
        ('http://www.ggzyjy.com.cn/hsweb/004/004012/004012002/MoreInfo.aspx?CategoryNum=004012002', '更正公告/电力工程'),
        ('http://www.ggzyjy.com.cn/hsweb/004/004012/004012003/MoreInfo.aspx?CategoryNum=004012003', '中标公告/电力工程'),
    ]

    custom_settings = {'COOKIES_ENABLED': True, 'DOWNLOAD_DELAY': 8.88}

    def start_requests(self):
        for i, (url, subject) in enumerate(self.start_urls):
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data, 'cookiejar': i, 'proxy': True}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css=('#MoreInfoList1_DataGrid1 > tr > td > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def parse(self, response):
        links = self.link_extractor.extract_links(response)
        links = SpiderTool.url_filter(links, key=lambda x: x.url)
        for link in links:
            link.meta.update(response.meta['data'])
            yield scrapy.Request(link.url, meta={'data': link.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """

        data = response.meta['data']
        day = FieldExtractor.date(data.get('day'), response.css('#tdTitle font.webfont'))
        contents = response.css('#TDContent > *').extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=data.get('title') or data.get('text'),
            contents=contents
        )

        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(response.css('#TDContent > *')))
        return [g]
