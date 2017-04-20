import scrapy
from fetch.extractors import NodesExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json


class jiangsuTrafficSpider(scrapy.Spider):
    """
    @title: 江苏省交通运输厅
    @href: http://www.jscd.gov.cn/
    """
    name = 'jiangsu/traffic'
    alias = '江苏/交通'
    # allowed_domains = ['jscd.gov.cn', '218.2.208.144']
    start_urls = [
        ('http://218.2.208.144:8094/EBTS/publish/announcement/getList?placard_type=1',
         'http://218.2.208.144:8094/EBTS/publish/announcement/doEdit?proId={0[placard_id]}',
         '招标公告'),
        ('http://218.2.208.144:8094/EBTS/publish/announcement/query',
         'http://218.2.208.144:8094/EBTS/publish/announcement/edit?str={0[zb_placard_id]},{0[zb_placard_flag]}',
         '中标公告'),
    ]
    start_params = {
        'page': '1',
        'rows': '10'
    }

    def start_requests(self):
        for url, detail, subject in self.start_urls:
            data = dict(subject=subject, detail=detail)
            form = self.start_params.copy()
            yield scrapy.FormRequest(url, formdata=form, meta={'data': data, 'form': form}, dont_filter=True)

    def parse(self, response):
        pkg = json.loads(response.text)
        detail = response.meta['data']['detail']
        for row in pkg['rows']:
            url = detail.format(row)
            row = {k: v for k, v in row.items() if v}
            row.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

        form = response.meta['form']
        page, size = int(form['page']) + 1, int(form['rows'])
        if page * size < pkg['total']:
            form['page'] = str(page)
            yield scrapy.FormRequest(response.url, formdata=form, meta=response.meta, dont_filter=True)

    def parse_item(self, response):
        """ 解析详情页 """
        """
            {
                "tender_project_type": "施工",
                "placard_flag": "9",
                "placard_id": "2507949f74b94112b24f364f60436140",
                "build_type": "路面",
                "placard_name": "G328东延（姜堰一区两区连接线）、姜高路东延土方工程",
                "placard_send_date": "2017-04-20",
                "sign_start_date": "2017-04-20 11:00",
                "sign_end_date": "2017-04-26 17:30"
            }
            {
                "zb_placard_name": "2016年通州区养护中小修项目",
                "zb_amount": "3246308.93",
                "zb_placard_send_date": "2017-04-20 00:00:00",
                "bid_notice_date": "2017-04-20",
                "create_date": "2017-04-20 12:50:44.5541",
                "update_date": "2017-04-20 13:35:14.2282",
                "zb_placard_id": "f4b33d812f634e5f9d6321bc92def7f2",
                "zb_placard_flag": "9",
                "placard_property_id": "001",
                "bid_unit_id": "10698",
                "bid_unit_name": "南通市通州区公路管理站",
                "zb_unit_id": "79e223f9152f44f69502ec48edfc3904",
                "zb_unit_name": "南通市江海公路工程有限公司",
                "tender_id": "19bb460a91f54263ac51d89530ef2482",
                "project_manager_id": "b2ad2c6fa49640228c694e57e4be5640",
                "project_manager": "吴卫国",
                "create_user_id": "SHXPJG",
                "update_user_id": "SHXPJG",
                "delete_flag": "0",
                "bid_unit_area": "通州区金沙镇银河路",
                "project_id": "df21969c52154df58149c5f65d93c857"
                }
        """
        data = response.meta['data']
        body = response.css('#detailform') or response.css('#body')

        day = FieldExtractor.date(*[data.get(k) for k in ('placard_send_date', 'sign_start_date',
                                                          'create_date', 'bid_notice_date', 'zb_placard_send_date')])
        title = data.get('placard_name') or data.get('zb_placard_name')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject'), data.get('tender_project_type')])
        g.set(budget=data.get('zb_amount') or FieldExtractor.money(body))
        g.set(extends=data)
        return [g]
