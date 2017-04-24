import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json


class Hunan1Spider(scrapy.Spider):
    """
    @title: 中国湖南政府采购网
    @href: http://ccgp-hunan.gov.cn/
    """
    name = 'hunan/1'
    alias = '湖南'
    allowed_domains = ['ccgp-hunan.gov.cn']
    start_urls = [
        ('http://ccgp-hunan.gov.cn/mvc/getNoticeList4Web.do',
         'http://ccgp-hunan.gov.cn/page/notice/notice.jsp?noticeId={[NOTICE_ID]}'),
        ('http://ccgp-hunan.gov.cn/mvc/getNoticeListOfCityCounty.do',
         'http://ccgp-hunan.gov.cn/page/notice/notice.jsp?noticeId={[NOTICE_ID]}&area_id=1'),
    ]
    start_params = {
        'nType': {'prcmNotices': '招标公告', 'dealNotices': '中标公告', 'modfiyNotices': '更正公告'},
        'page': '1',
        'pageSize': '18',
    }
    custom_settings = {'DOWNLOAD_DELAY': 1.8}

    def start_requests(self):
        for url, detail in self.start_urls:
            for form, data in SpiderTool.iter_params(self.start_params):
                data.update(detail=detail)
                yield scrapy.FormRequest(url, formdata=form, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        try:
            data = response.meta['data']
            pkg = json.loads(response.text)
            rows = 'rows' in pkg and pkg['rows'] or pkg
            for row in rows:
                url = data['detail'].format(row)
                row.update(**data)
                yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)
        except Exception as ex:
            print(ex)

    def parse_item(self, response):
        """ 解析详情页 """
        """
            "RN": 1,
            "NOTICE_NAME": "更正公告",
            "NOTICE_CATEGORY_CODE": "04",
            "PRCM_PLAN_ID": -1,
            "PRCM_MODE_CODE": "03",
            "PRCM_MODE_CODE1": null,
            "DEPT_ID": null,
            "AREA_ID": 124,
            "AREA_NAME": "娄星区",
            "NOTICE_ID": 1000174426,
            "ORG_CODE": null,
            "PRCM_MODE_NAME": "竞争性谈判",
            "NOTICE_TITLE": "娄底三中博远楼高考监考系统改造",
            "NOTICE_TYPE_NAME": "更正公告",
            "NEWWORK_DATE": "2017-04-21",
            "NEWWORK_DATE_ALL": {},
            "SRC_CODE": "2"
        """
        data = response.meta['data']
        body = response.css('body')

        day = FieldExtractor.date(data.get('NEWWORK_DATE'))
        title = data.get('NOTICE_TITLE')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias, data.get('AREA_NAME')])
        g.set(subject=[data.get('subject'), data.get('PRCM_MODE_NAME')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
