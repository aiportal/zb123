import scrapy
from . import JsonMetaSpider, GatherItem
from . import JsonLinkGenerator, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re
import json


class NingxiaSpider(JsonMetaSpider):
    name = 'ningxia'
    alias = '宁夏'
    allowed_domains = ['nxzfcg.gov.cn']
    start_referer = 'http://www.nxzfcg.gov.cn/ningxiaweb/002/002002/about.html'
    start_urls = ['http://www.nxzfcg.gov.cn/ningxia/services/BulletinWebServer/getInfoListInAbout']
    start_params = {
        'response': 'application/json',
        'siteguid': '2e221293-d4a1-40ed-854b-dcfea12e61c5',
        'categorynum': {'002001': '工程建设', '002002': '政府采购'},
        'cityname': '',
        'title': '',
        'pageIndex': 1,
        'pageSize': 18,
    }

    # 详情页
    def link_requests(self, response):
        base_url = 'http://www.nxzfcg.gov.cn/ningxia/WebbuilderMIS/RedirectPage/RedirectPage.jspx?' \
                   'infoid={0[infoid]}&categorynum={0[categorynum]}&locationurl=http://www.nxggzyjy.org/ningxiaweb'
        js = json.loads(json.loads(response.text)['return'])
        for item in js['Table']:
            url = base_url.format(item)
            data = dict(response.meta['params'], **item)
            yield scrapy.Request(url, meta={'data': data}, callback=self.parse_item)

    # 翻页
    def page_requests(self, response):
        page_count = 50     # TODO：有记录总数的请求网址，此处简化为常数
        params = response.meta['params']
        page = int(params.get('pageIndex', 0)) + 1
        if page < page_count:
            url = self.replace_url_param(response.url, pageIndex=page)
            params.update(pageIndex=page)
            yield scrapy.Request(url=url, meta={'params': params})

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)
        g['day'] = DateExtractor.extract(data.get('infodate', ''))
        g['end'] = None
        g['title'] = data.get('title')
        g['area'] = self.join_words(self.alias)
        subject = {
            '001': '招标公告', '002': '更正公告', '003': '其他公告'
        }.get(data.get('categorynum', '')[6:], '其他公告')
        g['subject'] = self.join_words(subject)
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css=('#mainContent > p, #mainContent table', ))
        g['contents'] = content_extractor.extract_contents(response)
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
