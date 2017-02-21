import scrapy
from . import JsonMetaSpider, GatherItem
from . import DateExtractor, JsonLinkGenerator, JsonPageGenerator, HtmlContentExtractor
import json


class HunanSpider(JsonMetaSpider):
    name = 'hunan'
    alias = '湖南'
    allowed_domains = None      # ['ccgp-shandong.gov.cn', 'ccgp-shandong.gov.cn:8080']
    start_referer = None        # 'http://www.ccgp-hunan.gov.cn:8080/page/notice/more.jsp'
    start_urls = ['http://www.ccgp-hunan.gov.cn:8080/portal/protalAction!getNoticeList.action']
    start_params = {
        'page': {1: None},
        'pageSize': {50: None},
    }
    custom_settings = {'COOKIES_ENABLED': True, 'DOWNLOAD_DELAY': 2.6}

    # 详情页链接（带框架的详情页）
    link_generator = JsonLinkGenerator('/portal/protalAction!viewNoticeContent.action?noticeId={0[NOTICE_ID]}',
                                       # '/page/notice/notice.jsp?noticeId={0[NOTICE_ID]}',
                                       '', lambda x: x)

    # 翻页链接（应该首次请求时获取记录总数，此处直接写数值）
    # 获取记录总数：http://www.ccgp-hunan.gov.cn:8080/portal/protalAction!getNoticeListCount.action
    page_generator = JsonPageGenerator('page', 'pageSize', lambda x: 28351)

    def parse(self, response):
        # 访问较为频繁时，服务器返回不正确的JSON包，需要稍后重试
        if response.body == b'[]':
            return [scrapy.Request(response.url, meta=response.meta)]
        try:
            objs = json.loads(response.body.decode())
            return super().parse(response)
        except:
            return [scrapy.Request(response.url, meta=response.meta)]

    def link_requests(self, response):
        if not hasattr(response, 'text'):
            response.text = response.body.decode()
        return super().link_requests(response)

    def page_requests(self, response):
        if not hasattr(response, 'text'):
            response.text = response.body.decode()
        return super().page_requests(response)

    def parse_item(self, response):
        """ 解析详情页 """
        # TODO: 应该先载入框架页，再请求详情页，即使详情页请求失败，也返回Item对象，这样就不会漏掉信息。
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
        g['subject'] = self.join_words(data.get('NOTICE_NAME'), data.get('PRCM_MODE_NAME'))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(xpath=('//body/table/tr', '//body/*'))
        if not response.xpath('//body/table/tr'):
            content_extractor = HtmlContentExtractor(xpath=('//body/*',))
        g['contents'] = content_extractor.extract_contents(response)
        if response.text.startswith('[{') or response.text.startswith('{"count":'):
            g['contents'] = []  # 空内容重试多次时，会返回索引页的JSON或count内容。
            # TODO: 应该用配置项控制空返回值的重试功能是否启用，此处即使response返回空值，也可以返回Item对象。
        g['pid'] = None
        g['tender'] = None
        g['budget'] = None
        g['tels'] = None
        g['extends'] = data
        g['digest'] = content_extractor.extract_digest(response)

        # 附件
        # files_extractor = FileLinkExtractor(css='#file_list a', attrs_css={'text': './text()'})
        # g['attachments'] = [f for f in files_extractor.extract_files(response)]
        yield g
