import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class yibin_1Spider(scrapy.Spider):
    """
    @title: 宜宾市公共资源交易信息网
    @href: http://www.ybsggzyjyxxw.com/
    """
    name = 'sichuan/yibin/1'
    alias = '四川/宜宾'
    allowed_domains = ['ybsggzyjyxxw.com']
    start_urls = [
        'http://www.ybsggzyjyxxw.com/TrueLoreAjax/TrueLore.Web.WebUI.WebAjaxService,TrueLore.Web.WebUI.ashx',
        'http://www.ybsggzyjyxxw.com/Jyweb/ZhaoBiaoGongGaoView.aspx?type={0[XTType]}&subtype={0[XXLB]}&Guid={0[GUID]}'
    ]
    start_params = [
        (r'[0,15,"FBSJ DESC","XMMC","","XXLB ={0}  AND XTType={1} ","[{\"pvalue\":\"260\"},{\"pvalue\":\"1\"}]"]',
         'GetPageJYXTXXFB', '招标公告/建设工程'),
    ]

    def start_requests(self):
        url = self.start_urls[0]
        for body, method, subject in self.start_params:
            headers = {'Ajax-method': method, 'Content-Type': 'text/plain; charset=UTF-8'}
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, body=body, method='POST', headers=headers, dont_filter=True)

    def parse(self, response):
        data = response.meta['data']
        re_row = ',?(\w+):([^,]+)(?:,|$)'

        lns = response.text.strip('[{}]').split('},{')
        assert len(lns) == 15
        for ln in lns:
            row = {k: v.strip('"') for k, v in re.findall(re_row, ln) if v.strip('"') and v != 'null'}
            url = self.start_urls[1].format(row)
            row.update(**data)
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        """
        {
            "GUID": "94c0b4dc-9b59-4061-bc96-13ce3ba5e177",
            "XMMC": "符月路至宜庆路连接公路路基工程项目（三块村至龙嘴村）",
            "XMBH": "GAOGL2017040004",
            "BDMC": "符月路至宜庆路连接公路路基工程项目（三块村至龙嘴村）/标段施工招标公告",
            "BDBH": "",
            "XXLB": 260,
            "FBSJ": "2017-05-04 00:00:00",
            "Fbjssj": "2017-05-08 23:59:00",
            "FUJIAN": "",
            "FUJIANURL": "",
            "FBZT": 3,
            "IsBYWJ": 0,
            "XTType": 1,
            "LYXX": 1,
            "BMZT": 0,
            "XXGKID": 0,
            "XXGKLX": 0,
            "BMKSSJ": "1900-01-01 00:00:00",
            "BMJZSJ": "1900-01-01 00:00:00",
            "GongGaoLY": 1,
            "GongGao_Guid": "0159e3fd-689e-4d09-85c1-6f0c4c99471e",
            "GongGao_Type": 1,
            "Search_BianHao": "GAOGL2017040004",
            "Search_Title": "符月路至宜庆路连接公路路基工程项目（三块村至龙嘴村）",
            "RecordsCount": 2588,
            "xxlxType": "招标公告"
        }
        """
        data = response.meta['data']
        body = response.css('#cphMiddle_divDianZi, #fjDiv') or response.css('#tbl招标公告模板, #gridviewFJ')

        day = FieldExtractor.date(data.get('FBSJ'), response.css('#cphMiddle_lblCount'))
        title = data.get('BDMC') or data.get('XMMC')
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
        g.set(extends=data)
        return [g]
