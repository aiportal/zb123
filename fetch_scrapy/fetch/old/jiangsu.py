import scrapy
from .. import HtmlMetaSpider
from fetch.extractors import NodeValueExtractor, MetaLinkExtractor, DateExtractor, HtmlPlainExtractor
import re
from functools import reduce
from itertools import chain


class JiangsuSpider(HtmlMetaSpider):
    name = 'jiangsu'
    alias = '江苏'
    allowed_domains = ["ccgp-jiangsu.gov.cn"]
    start_referer = None

    start_urls = ['http://www.ccgp-jiangsu.gov.cn/pub/jszfcg/cgxx']
    start_params = {
        'subject': {
            'cgyg': '预公告/采购预告',
            'cggg': '招标公告/采购公告',
            'gzgg': '更正公告',
            'cjgg': '中标公告/成交公告',
            'htgg': '其他公告/合同公告',
            'xqyj': '预公告/征求意见'
        }
    }

    def start_requests(self):
        for k, v in self.start_params['subject'].items():
            url = '{0}/{1}/'.format(self.start_urls[0], k)
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
        # content_extractor = HtmlPlainExtractor(xpath=(
        #     '//div[@class="detail_con"]/*[not(style)]',
        #     '//div[@class="TRS_Editor"]/*',
        #     '//div[@class="TRS_Editor"]/div/*',
        #     '//div[@class="detail_con"]/p/span/br/..//text()',
        #     # '//div[@id="tableDiv"]/table/*/tr'
        # ))
        # contents = content_extractor.contents(response)
        # digest = content_extractor.digest(contents)
        detail = response.css('div.detail_con, div.liebiao')
        assert detail
        contents = detail.extract()

        g['contents'] = contents
        g['pid'] = None
        g['tender'] = None
        g['budget'] = self.get_max_money(detail)
        g['tels'] = None
        g['extends'] = data
        g['digest'] = {}

        yield g

    def get_max_money(self, selector: scrapy.Selector):
        """ 提取最大金额 """
        patterns_yuan = ['([\d,]{5,})\.\d{1,2}\s*元?', '￥?\s*([\d,]{3,})\s*元']
        patterns_wan = ['￥?\s*([\d,.]+)\s*万元?']
        patterns_sci = ['(\d\.\d+)E(\d)']

        pattern_cn = '([零壹贰叁肆伍陆柒捌玖拾佰仟万亿]{2,})[圆元]整?'
        nums_cn = [('拾$', '0'), ('佰$', '00'), ('仟$', '000'), ('万$', '0000'),
                   ('拾', ''), ('佰', ''), ('仟', ''), ('万', ''),
                   ('零', '0'), ('壹', '1'), ('贰', '2'), ('叁', '3'), ('肆', '4'), ('伍', '5'),
                   ('陆', '6'), ('柒', '7'), ('捌', '8'), ('玖', '9')]

        money_all = []
        lns = [s.strip() for s in selector.xpath('.//text()').extract() if s.strip()]
        content = ''.join(lns)
        for ln in [content]:
            values_yuan = [int(s.replace(',', '')) for s in
                           chain(*[re.findall(p, ln) for p in patterns_yuan])]
            values_wan = [int(float(s.replace(',', '')) * 10000) for s in
                          chain(*[re.findall(p, ln) for p in patterns_wan])]
            values_sci = [int(float(s[0]) * (10 ** int(s[1]))) for s in
                          chain(*(re.findall(p, ln) for p in patterns_sci))]

            values_cn = []
            if re.search(pattern_cn, ln):
                values_cn = [int(reduce(lambda s, r: re.sub(r[0], r[1], s), nums_cn, x))
                             for x in re.findall(pattern_cn, ln)]

            money_all.extend(values_yuan + values_wan + values_sci + values_cn)
        if any(money_all):
            return max(money_all)
        return None
