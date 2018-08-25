import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import random
import json


class neimenggu_1Spider(scrapy.Spider):
    """
    @title: 内蒙古自治区政府采购网
    @href: http://www.nmgp.gov.cn/
    """
    name = 'neimenggu/1'
    alias = '内蒙古'
    allowed_domains = ['nmgp.gov.cn']
    start_base = 'http://www.nmgp.gov.cn/zfcgwslave/web/index.php?'
    start_urls = [
        (start_base + 'r=zfcgw/anndata&type_name=1&byf_page=1&fun=cggg', '招标公告/政府采购'),
        (start_base + 'r=zfcgw/anndata&type_name=2&byf_page=1&fun=cggg', '更正公告/政府采购'),
        (start_base + 'r=zfcgw/anndata&type_name=3&byf_page=1&fun=cggg', '中标公告/政府采购'),
        (start_base + 'r=zfcgw/anndata&type_name=5&byf_page=1&fun=cggg', '废标公告/政府采购'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            url += '&_={}'.format(str(random.random())[2:])
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='table.recordlist tr > td > a',
                                       attrs_xpath={'text': './/text()', 'end': '../../td[last()]//text()',
                                                    'tags': '../font//text()'})

    def parse(self, response):
        """
        {
            "ADNAME": "敖汉旗", 
            "ADCODE": "150430", 
            "PURNAME": "通用设备", 
            "PURCODE": "A02", 
            "TITLE": "敖汉旗国土资源局通用设备询价招标公告", 
            "ENDDATE": "[截止：2018-08-31]", 
            "SUBDATE": "2018-08-24 22:28:30", 
            "wp_mark_id": "98264", 
            "ay_table_tag": "1", 
            "IS_CHANGE": null, 
            "TITLE_ALL": "敖汉旗国土资源局通用设备询价招标公告"
        }
        """
        detail_url = 'http://www.nmgp.gov.cn/ay_post/post.php?tb_id={0[ay_table_tag]}&p_id={0[wp_mark_id]}'

        pkg = json.loads(response.text)
        for row in pkg[0]:
            url = detail_url.format(row)
            row.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#content-box-1')

        day = FieldExtractor.date(data.get('SUBDATE'), response.css('#info-box span.feed-time'))
        title = data.get('TITLE') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name,
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias, data.get('ADNAME')])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
