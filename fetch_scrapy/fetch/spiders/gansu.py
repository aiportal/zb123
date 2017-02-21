import scrapy
from . import HtmlMetaSpider, GatherItem
from . import NodeValueExtractor, MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re


class GansuSpider(HtmlMetaSpider):
    name = 'gansu'
    alias = '甘肃'
    allowed_domains = ["ccgp-gansu.gov.cn"]
    start_referer = 'http://www.ccgp-gansu.gov.cn/'
    start_urls = ['http://www.ccgp-gansu.gov.cn/web/doSearch.action']
    start_params = {
        'start': {0: None},
        'limit': {50: None}
    }
    # 详情页链接
    link_extractor = MetaLinkExtractor(css='ul.Expand_SearchSLisi > li > a', url_attr='href',
                                       attrs_xpath={'text': './text()', 'digest': '../p[1]//text()',
                                                    'tags': '../p[2]//text()'})

    # 索引页翻页
    def page_requests(self, response):
        start = int(NodeValueExtractor.extract_text(response.css('#start').xpath('./@value')))
        limit = int(NodeValueExtractor.extract_text(response.css('#limit').xpath('./@value')))
        total = int(NodeValueExtractor.extract_text(response.css('#total').xpath('./@value')))
        if start < total:
            url = self.replace_url_param(response.url, start=start+limit)
            yield scrapy.Request(url, meta={'params': response.meta['params']})

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        tags = [s.strip() for s in data['tags'].split('|') if s.strip()]
        digest = dict(x for x in [s.strip().split('：') for s in data['digest'].split('|')] if len(x) == 2)
        digest2 = self.parse_table_digest(response, 'div.property + table')

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(digest.get('发布时间'))
        g['end'] = DateExtractor.extract(digest.get('开标时间'))
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias, tags[1:] and tags[1] or None)
        tag = tags and tags[0] or None
        subject = {'询价公告': '预公告', '公开招标': '招标公告', '邀请招标': '招标公告', '竞争性谈判': '招标公告',
                   '竞争性磋商': '招标公告', '单一来源': '招标公告', '中标公告': '中标公告', '成交公告': '其他公告',
                   '更正公告': '更正公告', '废标流标公告': '其他公告', '其他公告': '其他公告',
                   '单一来源公示': '其他公告', '资格预审公告': '其他公告'}.get(tag, '其他公告')
        g['subject'] = self.join_words(subject, tag)
        g['industry'] = self.join_words(tags[2:] and tags[2] or None)

        # 详情页正文
        content_extractor = HtmlContentExtractor(css='div.conTxt > div > *')
        g['contents'] = content_extractor.extract_contents(response)
        g['pid'] = None
        g['tender'] = digest.get('采购人')
        g['budget'] = ([v for k, v in digest2.items() if k.startswith('采购预算')] or [None])[0]
        g['tels'] = None
        g['extends'] = data
        g['digest'] = dict(content_extractor.extract_digest(response), **digest2, **digest)

        # 附件
        # files_extractor = FileLinkExtractor(css='#file_list a', attrs_css={'text': './text()'})
        # g['attachments'] = [f for f in files_extractor.extract_files(response)]
        yield g

    def parse_table_digest(self, response, table_css):
        """ 提取表格中的摘要信息，适用于横向键值对的摘要表格
        按行提取每一格的内容，两两组成键值对
        """
        table = response.css(table_css)
        if not table:
            return {}
        digest = {}
        for tr in table.xpath('./tr'):
            values = [NodeValueExtractor.extract_text(s.xpath('.//text()')) for s in tr.xpath('./td')]
            row_dict = dict([(values[i-1], values[i]) for i in range(1, len(values), 2)])
            digest.update(row_dict)
        return digest
