import scrapy
from . import HtmlMetaSpider, GatherItem
from . import NodeValueExtractor, MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re


# 'http://www.ccgp-hebei.gov.cn/zfcg/web/getBidingList_1.html',           # 招标公告
# 'http://www.ccgp-hebei.gov.cn/zfcg/web/getPreWinAnncList_1.html',       # 预中标公告
# 'http://www.ccgp-hebei.gov.cn/zfcg/web/getBidWinAnncList_1.html',       # 中标公告
# 'http://www.ccgp-hebei.gov.cn/zfcg/web/getCorrectionAnncList_1.html',   # 更正公告
# 'http://www.ccgp-hebei.gov.cn/zfcg/web/getCancelBidAnncList_1.html',    # 废标公告
# 'http://www.ccgp-hebei.gov.cn/zfcg/web/getSingleSourceList_1.html',     # 单一来源
# 'http://www.ccgp-hebei.gov.cn/zfcg/web/getcontractList_1.html',         # 合同公告

# http://www.ccgp-hebei.gov.cn/zfcg/1/bidingAnncDetail_67507.html           # 招标公告
# http://www.ccgp-hebei.gov.cn/zfcg/preBidingAnncDetail_43594.html          # 预中标公告
# http://www.ccgp-hebei.gov.cn/zfcg/bidWinAnncDetail_55732.html             # 中标公告
# http://www.ccgp-hebei.gov.cn/zfcg/correctionAnncDetail_11610.html         # 更正公告
# http://www.ccgp-hebei.gov.cn/zfcg/cancelBidAnncDetail_11036.html          # 废标公告
# http://www.ccgp-hebei.gov.cn/zfcg/1/singleSourceDetail_2791.html          # 单一来源
# http://www.ccgp-hebei.gov.cn/zfcg/bidContractDetail_8360.html             # 合同公告


class HebeiSpider(HtmlMetaSpider):
    name = 'hebei'
    alias = '河北'
    allowed_domains = ["ccgp-hebei.gov.cn"]
    start_referer = None
    start_urls = ['http://www.ccgp-hebei.gov.cn/zfcg/']
    start_params = {}

    url_partitions = {
        '招标公告': ('web/getBidingList_1.html', 'bidingAnncDetail'),
        '中标公告/预中标公告': ('web/getPreWinAnncList_1.html', 'preBidingAnncDetail'),
        '中标公告': ('web/getBidWinAnncList_1.html', 'bidWinAnncDetail'),
        '更正公告': ('web/getCorrectionAnncList_1.html', 'correctionAnncDetail'),
        '其他公告/废标公告': ('web/getCancelBidAnncList_1.html', 'cancelBidAnncDetail'),
        '其他公告/单一来源': ('web/getSingleSourceList_1.html', 'singleSourceDetail'),
        '其他公告/合同公告': ('web/getcontractList_1.html', 'bidContractDetail'),
    }

    def start_requests(self):
        for k, v in self.url_partitions.items():
            url = self.start_urls[0] + v[0]
            yield scrapy.Request(url, meta={'params': {'subject': k, 'page': 1}})

    # 详情页链接
    link_extractor = MetaLinkExtractor(css='tr[onclick^=watchContent]', url_attr='onclick',
                                       attrs_xpath={'text': './/a//text()', 'digest': './following-sibling::tr[1]'})

    def link_requests(self, response):
        params = response.meta['params']
        file_name = self.url_partitions[params['subject']][1]
        for node in self.link_extractor.extract_links(response):
            value, _, pre = re.search(r"'(\d+)(',\s*'(\d+)')?", node.meta['onclick']).groups()
            pre = pre and (pre + '/') or ''
            url = 'http://www.ccgp-hebei.gov.cn/zfcg/{0}{1}_{2}.html'.format(pre, file_name, value)
            data = dict(node.meta, **params)
            yield scrapy.Request(url, meta={'data': data})

    # 翻页链接
    def page_requests(self, response):
        # $(document).ready(
        # ...
        # pageFenye("1", "16",
        # ...
        script = NodeValueExtractor.extract_text(response.css('script:contains("$(document).ready")::text'))
        page, total = re.search('pageFenye\(\s*"(\d+)"\s*,\s*"(\d+)"', script).groups()
        if page < total:
            params = response.meta['params']
            params['page'] = int(page) + 1
            url = re.sub('_(\d+)\.html$', '_{0}.html'.format(params['page']), response.url)
            yield scrapy.Request(url, meta={'params': params})

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        index_digest = self.parse_html_digest(data['digest'])
        html_digest = self.parse_table_digest(response.xpath('//table/tr[@bgcolor="#edf7fc"]/..'))

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(index_digest.get('发布时间'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias, index_digest.get('地域'))
        g['subject'] = self.join_words(data.get('subject'))
        g['industry'] = None

        # 详情页正文
        #
        # 采购人名称：<span>河北省木兰围场国有林场管理局</span><br>
        # 采购人联系方式：<span>13833420093</span><br>
        # 采购人地址 ：<span>围场满族蒙古族自治县围场镇</span><br>
        # 。。。
        content_html = re.sub('(<span>|</span>)', '', NodeValueExtractor.extract_text(response.css('span.txt7')))
        contents = [NodeValueExtractor.extract_text(s) for s
                    in scrapy.Selector(text=content_html).xpath('.//text()')
                    if NodeValueExtractor.extract_text(s)]
        contents_digest = dict([(x[0], ' : '.join(x[1:]))
                                for x in [re.split('：|:', s) for s in contents]
                                if len(x) > 1])
        g['contents'] = contents
        g['pid'] = None
        g['tender'] = index_digest.get('采购人')
        g['budget'] = None
        g['tels'] = None
        g['extends'] = data
        g['digest'] = dict(contents_digest, **index_digest, **html_digest)

        # 附件
        # files_extractor = FileLinkExtractor(css='#file_list a', attrs_css={'text': './text()'})
        # g['attachments'] = [f for f in files_extractor.extract_files(response)]
        yield g

    def parse_html_digest(self, html):
        values = [NodeValueExtractor.extract_text(s) for s in
                  scrapy.selector.Selector(text=html).xpath('.//text()')]
        values = [s.strip('：').strip() for s in values if s.strip('：').strip()]
        return dict([(values[i-1], values[i]) for i in range(1, len(values), 2)])

    def parse_table_digest(self, table_selector):
        """ 提取表格中的摘要信息，适用于横向键值对的摘要表格
        按行提取每一格的内容，两两组成键值对
        """
        digest = {}
        for tr in table_selector.xpath('./tr'):
            values = [NodeValueExtractor.extract_text(s.xpath('.//text()')) for s in tr.xpath('./td')]
            row_dict = dict([(values[i-1], values[i]) for i in range(1, len(values), 2)])
            digest.update(row_dict)
        return digest
