import scrapy
from . import JsonMetaSpider
from . import DateExtractor, HtmlPlainExtractor
import json


class HunanSpider(JsonMetaSpider):
    name = 'hunan'
    alias = '湖南'
    allowed_domains = None      # ['ccgp-shandong.gov.cn', 'ccgp-shandong.gov.cn:8080']
    start_referer = None        # 'http://www.ccgp-hunan.gov.cn:8080/page/notice/more.jsp'
    start_urls = [
        'http://www.ccgp-hunan.gov.cn:8080/mvc/getNoticeList4Web.do',           # 省级
        'http://www.ccgp-hunan.gov.cn:8080/mvc/getNoticeListOfCityCounty.do'    # 市县
    ]
    start_params = {
        'page': '1',
        'pageSize': '50',
    }
    custom_settings = {'COOKIES_ENABLED': True, 'DOWNLOAD_DELAY': 2.6}

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.FormRequest(url, formdata=self.start_params, meta={'params': self.start_params},
                                     headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})

    def link_requests(self, response):
        url_ref = 'http://www.ccgp-hunan.gov.cn:8080/page/notice/notice.jsp?noticeId={0}'
        url_item = 'http://www.ccgp-hunan.gov.cn:8080/mvc/viewNoticeContent.do?noticeId={0}&area_id={1}'
        data = json.loads(response.text)
        for row in isinstance(data, list) and data or data['rows']:
            ref = url_ref.format(row['NOTICE_ID'])
            url = url_item.format(row['NOTICE_ID'], row.get('AREA_ID') > 0 and '1' or '')
            meta = {'data': row, 'top_url': ref, 'index_url': response.url}
            yield scrapy.Request(url, meta=meta, headers={'Referer': ref}, callback=self.parse_item)

    def page_requests(self, response):
        params = response.meta['params']
        page = int(params['page'])
        size = int(params['pageSize'])

        data = json.loads(response.text)
        if isinstance(data, list):
            if len(data) == size:
                params['page'] = str(page + 1)
                yield scrapy.FormRequest(response.url, formdata=params, meta={'params': params})
        else:
            total = json.loads(response.text)['total']
            if (page * size) < total:
                params['page'] = str(page + 1)
                yield scrapy.FormRequest(response.url, formdata=params, meta={'params': params})

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        # 'AREA_ID'  = {int} -1
        # 'AREA_NAME'  = {str} '湖南省'
        # 'DEPT_ID'  = {NoneType} None
        # 'NEWWORK_DATE'  = {str} '2016-12-02'
        # 'NEWWORK_DATE_ALL'  = {dict} {...}
        # 'NOTICE_CATEGORY_CODE'  = {str} '01'
        # 'NOTICE_ID'  = {int} 29576
        # 'NOTICE_NAME'  = {str} '单一来源公示'
        # 'NOTICE_TITLE'  = {str} '湖南省防汛抗旱指挥部办公室喷水组合式防汛抢险舟采购单一来源采购公示'
        # 'NOTICE_TYPE_NAME'  = {str} '单一来源公告'
        # 'ORG_CODE'  = {str} '25217'
        # 'PRCM_MODE_CODE'  = {str} '05'
        # 'PRCM_MODE_CODE1'  = {NoneType} None
        # 'PRCM_MODE_NAME'  = {str} '单一来源'
        # 'PRCM_PLAN_ID'  = {NoneType} None
        # 'PRCM_PLAN_NO'  = {NoneType} None
        # 'RN'  = {int} 1
        # 'page'  = {int} 1
        # 'pageSize'  = {int} 50

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('NEWWORK_DATE'))
        g['end'] = None
        g['title'] = data.get('NOTICE_TITLE')
        g['area'] = self.join_words(self.alias, data.get('AREA_NAME'))
        g['subject'] = self._subjects(data)
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlPlainExtractor(xpath=('//body/div/p | //body/div/table',
                                                      '//body/div/div/p | //body/div/div/table',
                                                      '//form/div/table',
                                                      '//body/table/tr', '//body/*'))
        contents = content_extractor.contents(response)

        g['contents'] = contents
        g['pid'] = None
        g['tender'] = None
        g['budget'] = None
        g['tels'] = None
        g['extends'] = data
        g['digest'] = content_extractor.digest(contents)

        yield g

    def _subjects(self, data: dict):
        subject = {
            '采购公告': '招标公告',
            '更正公告': '更正公告',
            '成交公告': '中标公告',
            '合同公告': '其他公告',
            '单一来源公示': '其他公告',
        }.get(data['NOTICE_NAME'], '其他公告')
        return self.join_words(subject, data.get('NOTICE_NAME'), data.get('PRCM_MODE_NAME'))
