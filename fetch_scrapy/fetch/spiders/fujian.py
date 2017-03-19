import scrapy
from . import HtmlMetaSpider, GatherItem
from . import DateExtractor, MetaLinkExtractor, MoneyExtractor
import json


class FujianSpider(HtmlMetaSpider):
    name = 'fujian'
    alias = '福建'
    allowed_domains = ["cz.fjzfcg.gov.cn"]

    start_referer = 'http://cz.fjzfcg.gov.cn/n/webfjs/secpag.do'
    start_urls = ['http://cz.fjzfcg.gov.cn/notice/noticelist/']
    start_params = {
        'notice_type': {
            '200000001': '招标公告/采购公告',
            '200000002': '更正公告',
            '200000004': '中标公告/合同公告',
            '200000005': '预公告/资格预审',
        },
        'page': 1
    }
    custom_settings = {'COOKIES_ENABLED': True, 'DOWNLOAD_DELAY': 2.1}

    def start_requests(self):
        for k, v in self.start_params['notice_type'].items():
            url = '{0}?notice_type={1}&page={2}'.format(self.start_urls[0], k, 1)
            params = {'subject': v, 'page': '1'}
            yield scrapy.Request(url, meta={'params': params}, dont_filter=True)

    def link_requests(self, response):
        link_extractor = MetaLinkExtractor(css=('ul.pag_box20 > li > a',),
                                           attrs_xpath={'text': './/text()',
                                                        'day': '../span//text()'})
        for link in link_extractor.extract_links(response):
            data = dict(link.meta, **response.meta['params'])
            yield scrapy.Request(link.url, meta={'data': data})

    def page_requests(self, response):
        page_extractor = MetaLinkExtractor(css=('div.pag_box23 > p > a', ),
                                           attrs_xpath={'text': './/text()'})
        pages = [int(x.meta['text']) for x in page_extractor.extract_links(response)
                 if x.meta['text'].isdecimal()]
        count = max(pages + [1])
        page = int(response.meta['params']['page']) + 1
        if page < count:
            response.meta['params']['page'] = str(page)
            url = self.replace_url_param(response.url, page=page)
            return [scrapy.Request(url, meta=response.meta)]
        else:
            return []

    def parse_item(self, response):
        """ 解析详情页
        """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('day'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias)
        g['subject'] = data.get('subject')
        g['industry'] = None

        g['contents'] = response.css('div.pag_box29').extract()
        g['pid'] = data.get('proId')
        g['tender'] = None
        g['budget'] = MoneyExtractor.money_max(response.css('div.pag_box29'))
        g['tels'] = None
        g['extends'] = data
        g['digest'] = None

        return [g]
