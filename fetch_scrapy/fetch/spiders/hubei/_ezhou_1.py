import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json


class ezhou_1Spider(scrapy.Spider):
    """
    @title: 鄂州市公共资源交易中心
    @href: http://www.ezztb.gov.cn/
    """
    name = 'hubei/ezhou/1'
    alias = '湖北/鄂州'
    allowed_domains = ['ezztb.gov.cn']
    start_urls = ['http://www.ezztb.gov.cn/jiaoyixinxi/queryJiaoYiXinXiPagination.do']
    start_params = [
        # ('招标公告/工程建设', {'gongShiType': '10', 'type': '10'},
        #  'http://www.ezztb.gov.cn/jiaoyixingxi/zbgg_view.html?guid={[gongShiGuid]}',
        #  'http://www.ezztb.gov.cn/jyw/jyw/showGongGao.do?ggGuid={[gongShiGuid]}'),
        # ('中标公告/工程建设', {'gongShiType': '50', 'type': '10'},
        #  'http://www.ezztb.gov.cn/jiaoyixingxi/zbgs_view.html?guid={}',
        #  ''),
        # ('废标公告/工程建设', {'gongShiType': '130', 'type': '10'}),
        # ('招标公告/政府采购', {'gongShiType': '70', 'type': '20'}),
        # ('中标公告/政府采购', {'gongShiType': '50', 'type': '20'}),
        # ('废标公告/政府采购', {'gongShiType': '130', 'type': '20'}),
    ]
    default_param = {
        'page': '1',
        'rows': '15',
        'title': '',
        'bianHao': '',
        'gongChengLeiBie': '',
        'gongChengType': '',
    }

    link_extractor = MetaLinkExtractor(css='tr > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        url = self.start_urls[0]
        for subject, param, top_url, req_url in self.start_params:
            param.update(**self.default_param)
            data = dict(subject=subject, top_url=top_url, req_url=req_url)
            yield scrapy.FormRequest(url, formdata=param, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        """ JSON """
        """
        {
            "total": 233,
            "totalPage": 16,
            "rows": [{
                    "gongShiGuid": "2cf3d05f-1332-41a7-bb14-3aeb9b875714",
                    "bianHao": "鄂州市公安局办公设备询价公告",
                    "title": "鄂州市公安局办公设备询价公告",
                    "caiDanBianHao": 20,
                    "type": 20,
                    "gongShiType": 70,
                    "gongChengType": 100,
                    "gongChengLeiBie": null,
                    "content": "<html...>"
                    ...
                },
                ...
            ]
        }
        """
        data = response.meta['data']
        pkg = json.loads(response.text)
        for row in pkg['rows']:
            row['content'] = None
            top_url = data['top_url'].format(row)
            req_url = data['req_url'].format(row)
            row.update(**response.meta['data'])
            yield scrapy.Request(req_url, meta={'data': row, 'top_url': top_url}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('')

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
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
