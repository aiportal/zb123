import scrapy
from fetch.items import GatherItem
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
import re


class HhhtSpider(scrapy.Spider):
    name = 'neimenggu/hhht'
    alias = '内蒙古/呼和浩特'
    allowed_domains = ['ggzyjy.com.cn']

    start_urls = [
        # 政府采购
        ('http://www.ggzyjy.com.cn/hsweb/004/004002/004002001/MoreInfo.aspx?CategoryNum=004002001', '招标公告/政府采购'),
        ('http://www.ggzyjy.com.cn/hsweb/004/004002/004002003/MoreInfo.aspx?CategoryNum=004002003', '中标公告/政府采购'),
        ('http://www.ggzyjy.com.cn/hsweb/004/004002/004002004/MoreInfo.aspx?CategoryNum=004002004', '更正公告/政府采购'),
        ('http://www.ggzyjy.com.cn/hsweb/004/004002/004002007/MoreInfo.aspx?CategoryNum=004002007', '其他公告/废标公告/政府采购'),
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

    custom_settings = {
        'COOKIES_ENABLED': True
    }

    def start_requests(self):
        for url, subject in self.start_urls:
            yield scrapy.Request(url, meta={'data': {'subject': subject}}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css=('#MoreInfoList1_DataGrid1 > tr > td > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})
    page_extractor = NodeValueExtractor(css=('#MoreInfoList1_Pager img[src$="/nextn.gif"]',),
                                        value_xpath='../@href')
    page_regex = re.compile("__doPostBack\('(.+)','(\d+)'\)")

    def parse(self, response):
        links = self.link_extractor.extract_links(response)
        links = SpiderTool.url_filter(links, key=lambda x: x.url)
        for link in links:
            link.meta.update(response.meta['data'])
            yield scrapy.Request(link.url, meta={'data': link.meta}, callback=self.parse_item)

        pager = self.page_extractor.extract_value(response)
        if pager and self.page_regex.search(pager):
            page_name, page_num = self.page_regex.findall(pager)[0]
            form = {
                '__EVENTTARGET': page_name,
                '__EVENTARGUMENT': page_num,
            }
            yield scrapy.FormRequest.from_response(response, formdata=form, meta=response.meta)

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
