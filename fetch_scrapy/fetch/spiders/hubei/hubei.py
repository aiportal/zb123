import scrapy
from .. import HtmlMetaSpider, GatherItem
from fetch.extractors import NodeValueExtractor, MetaLinkExtractor, DateExtractor, HtmlContentExtractor
import re
from urllib import parse


# 湖北省政府采购网：http://ccgp-hubei.gov.cn/
# 首页内嵌网址：http://www.ccgp-hubei.gov.cn/indexAction!index.action
# 首先访问首页内嵌网址，获得有效的Cookie，之后使用此Cookie打开详情页才有内容。

# TODO: Redirecting (307) to <GET http://tieba.baidu.com/_PXCK_1477450875_82> from <GET http://ccgp-hubei.gov.cn/pages/html/xzbnotice.html>


class HubeiSpider(HtmlMetaSpider):
    name = 'hubei'
    alias = '湖北'
    allowed_domains = ["ccgp-hubei.gov.cn"]
    start_referer = 'http://www.ccgp-hubei.gov.cn/indexAction!index.action'
    start_urls = ['http://ccgp-hubei.gov.cn/fnoticeAction!listFNoticeInfos.action']
    start_pages = [
        ('http://ccgp-hubei.gov.cn/pages/html/{0}.html'.format(k), {'subject': v}) for k, v in
        {
            'szbnotice': '招标公告/省级',
            'sjgnotice': '中标公告/省级',
            'sgznotice': '更正公告/省级',
            'sfbnotice': '废标公告/省级',
            'sdynotice': '单一来源公告/省级',
            'sqtnotice': '其它公告/省级',
            'xzbnotice': '招标公告/市级',
            'xjgnotice': '中标公告/市级',
            'xgznotice': '更正公告/市级',
            'xfbnotice': '废标公告/市级',
            'xdynotice': '单一来源公告/市级',
            'xqtnotice': '其它公告/市级',
        }.items()
    ]
    custom_settings = {'COOKIES_ENABLED': True, 'DOWNLOAD_DELAY': 1.2}
    cookie = {}

    def start_requests(self):
        yield scrapy.Request(self.start_referer, callback=self.start_requests_real,  dont_filter=True)

    def start_requests_real(self, response):
        cookie = response.headers.get('Set-Cookie', '').decode().split(';')[0].split('=')
        if cookie and len(cookie) > 1:
            self.cookie = {cookie[0]: cookie[1]}
        for url, data in self.start_pages:
            yield scrapy.Request(url, meta={'params': data}, dont_filter=True)

    # 详情页链接
    link_extractor = MetaLinkExtractor(css='div.news_content > ul > li > a', url_attr='href',
                                       attrs_xpath={'text': './text()', 'start': '../span//text()', 'area': '../text()',
                                                    'tag1': '../font[1]//text()', 'tag2': '../font[2]//text()'})

    def link_requests(self, response):
        for link in self.link_extractor.extract_links(response):
            response.meta['top_url'] = link.url
            ggid = parse.parse_qs(parse.urlsplit(link.url).query)['GGID'][0]
            url = 'http://ccgp-hubei.gov.cn/fnoticeAction!findFNoticeInfoByGgid_n.action?queryInfo.GGID=' + ggid
            data = dict(link.meta, **response.meta['params'])
            cookie = response.headers.get('Set-Cookie', '').decode().split(';')[0].split('=')
            if cookie:
                yield scrapy.Request(url, meta={'data': data}, cookies=self.cookie)
            else:
                yield scrapy.Request(url, meta={'data': data})

    # 翻页
    page_extractor = NodeValueExtractor('div.news_content ~ div a[onclick^=toPage]:contains(下)',
                                        value_xpath='./@onclick',
                                        value_process=lambda x: x and re.search('(\d+)', x).group(1) or None)

    def page_requests(self, response):
        pages = self.page_extractor.extract_values(response)
        if pages:
            page = int(pages[0]) + 1
            url = self.replace_url_param(response.url, **{'queryInfo.curPage': page})
            yield scrapy.Request(url, meta={'params': response.meta['params']})

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('start'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias, data.get('area', '').strip('[]()'))
        g['subject'] = self.join_words(data.get('queryInfo.GGLX'), data.get('tag1'), data.get('tag2'))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css='div.notic_show_content > *')
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
