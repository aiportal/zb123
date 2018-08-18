import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import re


class Sichuan3Spider(scrapy.Spider):
    name = 'sichuan/3'
    alias = '四川'
    allowed_domains = ['spprec.com']
    start_urls = [
        ('http://www.spprec.com/sczw/jyfwpt/005001/005001001/MoreInfo.aspx?CategoryNum=005001001', '招标公告/工程建设'),
        ('http://www.spprec.com/sczw/jyfwpt/005001/005001002/MoreInfo.aspx?CategoryNum=005001002', '更正公告/工程建设'),
        ('http://www.spprec.com/sczw/jyfwpt/005001/005001003/MoreInfo.aspx?CategoryNum=005001003', '中标结果/工程建设'),

        ('http://www.spprec.com/sczw/jyfwpt/005002/005002002/005002002002/MoreInfo.aspx?CategoryNum=005002002002', '采购公告/政府采购'),
        ('http://www.spprec.com/sczw/jyfwpt/005002/005002004/005002004002/MoreInfo.aspx?CategoryNum=005002004002', '中标公告/政府采购'),
        ('http://www.spprec.com/sczw/jyfwpt/005002/005002005/MoreInfo.aspx?CategoryNum=005002005', '更正公告/政府采购'),

        ('http://www.spprec.com/sczw/jyfwpt/005003/005003001/MoreInfo.aspx?CategoryNum=005003001', '招标公告/铁路工程'),
        ('http://www.spprec.com/sczw/jyfwpt/005003/005003002/MoreInfo.aspx?CategoryNum=005003002', '更正公告/铁路工程'),
        ('http://www.spprec.com/sczw/jyfwpt/005003/005003003/MoreInfo.aspx?CategoryNum=005003003', '中标公告/铁路工程'),
    ]
    custom_settings = {
        'COOKIES_ENABLED': True
    }

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data})

    link_extractor = MetaLinkExtractor(css=('#MoreInfoList1_DataGrid1 > tr > td > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})
    # page_extractor = NodeValueExtractor(css=('#MoreInfoList1_Pager img[src$="nextn.gif"]',),
    #                                     value_xpath='../@href')

    def parse(self, response):
        links = self.link_extractor.extract_links(response)
        links = SpiderTool.url_filter(links, lambda x: x.url)
        for link in links:
            link.meta.update(**response.meta['data'])
            yield scrapy.Request(link.url, meta={'data': link.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#ivs_content')

        day = FieldExtractor.date(data.get('day'), response.css('#tblInfo > tbody > tr:nth-child(3)'))
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
