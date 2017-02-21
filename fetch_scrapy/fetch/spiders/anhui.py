import scrapy
from . import HtmlMetaSpider, GatherItem
from . import NodeValueExtractor, MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re


class AnhuiSpider(HtmlMetaSpider):
    name = 'anhui'
    alias = '安徽'
    allowed_domains = ["ahzfcg.gov.cn"]
    start_referer = None
    start_urls = ['http://www.ahzfcg.gov.cn/mhxt/MhxtSearchBulletinController.zc']
    start_params = {
        'method': {'bulletinChannelRightDown': None},
        'bType': {'01': '招标公告/采购公告', '02': '更正公告', '03': '中标公告', '04': '中标公告/成交公告', '06': '其他公告/单一来源公示',
                  '99': '其他公告/合同公告', '07': '其他公告/废标、流标公告'},
        'pageNo': {1: None},
        'pageSize': {10: None}
    }
    # 详情页链接
    link_extractor = MetaLinkExtractor(css='ul > li > a', url_attr='href',
                                       attrs_xpath={'text': './text()', 'start': '../span//text()'},
                                       url_process=lambda x: '/' + x)

    # 翻页
    def page_requests(self, response):
        params = response.meta['params']
        page = NodeValueExtractor.extract_text(response.css('input[name=pageNo]::attr(value)'))
        total = NodeValueExtractor.extract_text(response.css('input[name=totalPageCount]::attr(value)'))
        if int(page) < int(total):
            params['pageNo'] = int(page) + 1
            url = self.replace_url_param(response.url, pageNo=params['pageNo'])
            yield scrapy.Request(url, meta={'params': params})

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('start'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias)
        g['subject'] = self.join_words(data.get('bType'))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css=('div.frameNews table tr', 'div.frameNews > *'))
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
