import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class yangzhou_2Spider(scrapy.Spider):
    """
    @title: 扬州工程建设信息网
    @href: http://www.yzcetc.com/yzcetc/
    """
    name = 'jiangsu/yangzhou/2'
    alias = '江苏/扬州'
    allowed_domains = ['yzcetc.com']
    start_urls = [
        ('http://www.yzcetc.com/yzcetc/YW_Info/ZaoBiaoReport/MoreReportList_YZ_New.aspx?CategoryNum=003', '招标公告'),
        ('http://www.yzcetc.com/yzcetc/YW_Info/ZhongBiaoGS/MoreGSList_YZ_New.aspx?CategoryNum=003', '中标公告'),
    ]

    link_extractor = NodesExtractor(css='#MoreInfoList1_DataGrid1 tr > td > a',
                                    attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()',
                                                 'industry': '../../td[last()-1]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        rows = self.link_extractor.extract_nodes(response)
        for row in rows:
            href = SpiderTool.re_text('window\.open\("(.+)","",".+"\)', row['onclick'])
            url = urljoin(response.url, href)
            row.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#Table1') or response.css('#Form1')
        prefix = '^\[\w{1,5}\]'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
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
        g.set(industry=data.get('industry'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
