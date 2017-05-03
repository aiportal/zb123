import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json
import re


class SichuanAba1Spider(scrapy.Spider):
    """
    @title: 阿坝羌族自治州公共资源交易中心
    @href: http://www.abatc.cn/Index.html
    """
    name = 'sichuan/aba/1'
    alias = '四川/阿坝'
    allowed_domains = ['abatc.cn']
    start_urls = [
        'http://www.abatc.cn/TrueLoreAjax/TrueLore.Web.WebUI.WebAjaxService,TrueLore.Web.WebUI.ashx',
        'http://www.abatc.cn/Jyweb/JYXTXXFBView.aspx?Type={0[XTType]}&SubType={0[XXType]}&ID={0[XXId]}',
    ]
    start_params = [
        (r'[0,15,"XXKSSJ DESC","XMMC","","XTType={{0}} AND XXType={{1}} AND FBZT=1 AND XXKSSJ<getdate() ",'\
         r'"[{{\"pvalue\":\"{0[Type]}\"}},{{\"pvalue\":\"{0[SubType]}\"}}]"]'.format(d), v)
        for d, v in [
            ({'Type': 1, 'SubType': 260}, '招标公告/建设工程'),
            ({'Type': 1, 'SubType': 290}, '中标公告/建设工程'),
            ({'Type': 2, 'SubType': 320}, '招标公告/政府采购'),
            ({'Type': 2, 'SubType': 270}, '中标公告/政府采购'),
            ({'Type': 2, 'SubType': 360}, '其他公告/废标公告'),
        ]
    ]

    def start_requests(self):
        url = self.start_urls[0]
        headers = {'Ajax-method': 'GetPageJYXXFB', 'Content-Type': 'text/plain; charset=UTF-8'}

        for body, subject in self.start_params:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, body=body, method='POST', headers=headers, dont_filter=True)

    def parse(self, response):
        data = response.meta['data']
        re_row = ',?(\w+):([^,]+)(?:,|$)'

        lns = response.text.strip('[{}]').split('},{')
        assert len(lns) == 15
        for ln in lns:
            row = {k: v for k, v in re.findall(re_row, ln) if v.strip('"') and v != 'null'}
            url = self.start_urls[1].format(row)
            row.update(**data)
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        """
        {
            "IsNew": 0,
            "XXId": 14221,
            "XXLY": "交易系统",
            "XMBH": "九寨沟公资工招【2017】20号",
            "XMMC": "九寨沟县永和乡灾后重建防洪堤项目",
            "GCBH": "",
            "GCMC": "",
            "XXBT": "",
            "XXFBT": "",
            "ChengJiao_FangShi": 0,
            "BiaoDiNo": "",
            "BiaoDiName": "",
            "ZZBDBH": "",
            "ZZBDMC": "",
            "FBZT": 1,
            "XXKSSJ": "2017-04-20 09:19:00",
            "XXJSSJ": null,
            "XXFJOldFileName": "永和乡招标公告.rar",
            "XXFJNewFileName": "d35d19e0-0ec3-447e-8676-1eeaed24fa09.rar",
            "XXFJTime": null,
            "XTType": 1,
            "XXType": 260,
            "XMGuid": "7f0a4a9c-0c41-4bbc-9e01-f2ac85007800",
            "Guid": "53c71c7e-cae7-4d7a-ba85-550591b8efc1",
            "IsAdd": 0,
            "AddXMType": null,
            "Creator": "ZlM3sZDyHuFGqKIQMoScDfCULaQGXC1/nE1DXiycR69xLH9g+EZ+N1BOp5tyd9v/",
            "CreateTime": "2017-04-19 17:44:54",
            "Modifier": "ZlM3sZDyHuFGqKIQMoScDfCULaQGXC1/nE1DXiycR69xLH9g+EZ+N1BOp5tyd9v/",
            "ModifyTime": "2017-04-20 09:23:06",
            "InDate": 0,
            "BrowseCount": 334,
            "KBKSSJ": "2017-05-11 10:00:00",
            "RecordsCount": 996,
            "isBG": "0"
        }
        """
        data = response.meta['data']
        body = response.css('#cphMiddle_divContent, .xx_content, #cphMiddle_divAttach')

        day = FieldExtractor.date(data.get('XXKSSJ'), response.css('#cphMiddle_lblCount'))
        title = data.get('XMMC') or data.get('text')
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
