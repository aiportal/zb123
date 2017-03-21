import scrapy
from fetch.spiders import HtmlMetaSpider
from fetch.extractors import NodeValueExtractor, MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
from fetch.items import GatherItem
import re


class SichuanSpider(HtmlMetaSpider):
    name = 'sichuan'
    alias = '四川'
    allowed_domains = ["sczfcg.com"]
    start_referer = None
    start_urls = ['http://www.sczfcg.com/CmsNewsController.do']
    start_params = {
        'method': {'recommendBulletinList': None},
        'moreType': {'provincebuyBulletinMore': None},
        'channelCode': {'cgygg': '预公告/采购预告',
                        'cggg': '招标公告/采购公告',
                        # 'jgygg': '中标公告/结果预告',
                        'jggg': '中标公告/结果公告',
                        'gzgg': '更正公告',
                        'shiji_cggg1': '预公告/市县',
                        'shiji_cggg': '招标公告/市县',
                        # 'shiji_jggg1': '中标公告/市县',
                        'shiji_jggg': '中标公告/市县',
                        'shiji_gzgg': '更正公告/市县'},
        'rp': {'25': None},
        'page': {'1': None},
    }
    # 详情页链接
    link_extractor = MetaLinkExtractor(css='div.colsList > ul > li > a', url_attr='href',
                                       attrs_xpath={'text': './text()', 'start': '../span//text()'})

    # 翻页链接
    def page_requests(self, response):
        page = int(NodeValueExtractor.extract_text(response.css('#page').xpath('./@value'))) + 1
        total = int(NodeValueExtractor.extract_text(response.css('#totalPageNum').xpath('./@value')))
        if page <= total:
            url = self.replace_url_param(response.url, page=page)
            yield scrapy.Request(url, meta={'params': response.meta['params']})

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('start'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias)
        g['subject'] = self.join_words(data.get('channelCode'))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css='div.frameReport > table tr')
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
