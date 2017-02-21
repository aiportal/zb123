import scrapy
from . import HtmlMetaSpider, GatherItem
from . import NodeValueExtractor, MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re


class JiangsuSpider(HtmlMetaSpider):
    name = 'jiangsu'
    alias = '江苏'
    allowed_domains = ["ccgp-jiangsu.gov.cn"]
    start_referer = None

    start_urls = ['http://www.ccgp-jiangsu.gov.cn/pub/jszfcg/cgxx/']
    start_params = {
        'subject': {'cgyg': '预公告/采购预告', 'cggg': '招标公告/采购公告', 'gzgg': '更正公告', 'cjgg': '中标公告/成交公告',
                    'htgg': '其他公告/合同公告', 'xqyj': '预公告/征求意见'}
    }

    def start_requests(self):
        for k, v in self.start_params['subject'].items():
            url = self.start_urls[0] + k + '/'
            params = {'subject': v, 'url': url}
            yield scrapy.Request(url, meta={'params': params})

    # 详情页链接
    link_extractor = MetaLinkExtractor(css='div.list_list > ul > li > a', url_attr='href',
                                       attrs_xpath={'text': './text()', 'start': '../text()'})

    # 翻页链接
    def page_requests(self, response):
        script = NodeValueExtractor.extract_text(response.css('div.fanye > script ::text'))
        args = re.search('\((\d+)\s*,\s*(\d+)', script)   # createPageHTML(4, 1, "index", "html");
        count = int(args.group(1))
        page = int(args.group(2)) + 1
        if page < count:
            url = response.meta['params']['url'] + 'index_{0}.html'.format(page)
            yield scrapy.Request(url, meta={'params': response.meta['params']})

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        title = NodeValueExtractor.extract_text(response.css('div.dtit ::text'))
        g['day'] = DateExtractor.extract(data.get('start'))
        g['end'] = None
        g['title'] = data.get('text', '').endswith('...') and title or data.get('text')
        g['area'] = self.join_words(self.alias)
        g['subject'] = self.join_words(data.get('subject'))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css=('div.detail_con p', 'div.liebiao tr'))
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
