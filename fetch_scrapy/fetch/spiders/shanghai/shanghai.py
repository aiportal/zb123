import scrapy
from .. import HtmlMetaSpider, GatherItem
from .. import NodesExtractor, NodeValueExtractor, MetaLinkExtractor, FileLinkExtractor, DateExtractor, HtmlContentExtractor


# 上海政府采购：http://www.zfcg.sh.gov.cn/

# 市级采购公告：http://www.zfcg.sh.gov.cn/news.do?method=purchasePracticeIndexNew&flag=cggg&bFlag=00&treenum=05
# (iframe)        http://www.zfcg.sh.gov.cn/news.do?method=purchasePracticeMore&flag=cggg&bFlag=00&treenum=05
# 采购结果公告：http://www.zfcg.sh.gov.cn/news.do?method=purchasePracticeIndexNew&flag=cjgg&bFlag=00&treenum=06
# (iframe)        http://www.zfcg.sh.gov.cn/news.do?method=purchasePracticeMore&flag=cjgg&bFlag=00&treenum=06
# 区县采购公告：http://www.zfcg.sh.gov.cn/news.do?method=purchasePracticeIndexNew&flag=cggg&bFlag=qxgg&treenum=05
# (iframe)        http://www.zfcg.sh.gov.cn/news.do?method=purchasePracticeMore&flag=cggg&bFlag=qxgg&treenum=05
# 采购结果公告：http://www.zfcg.sh.gov.cn/news.do?method=purchasePracticeIndexNew&flag=cjgg&bFlag=qxgg&treenum=06
# (iframe)        http://www.zfcg.sh.gov.cn/news.do?method=purchasePracticeMore&flag=cjgg&bFlag=qxgg&treenum=06


class ShanghaiSpider(HtmlMetaSpider):
    name = 'shanghai'
    alias = '上海'
    allowed_domains = ['zfcg.sh.gov.cn']
    start_pages = [
        ('http://www.zfcg.sh.gov.cn/news.do?method=purchasePracticeMore{0}'.format(k),
         {'subject': v}) for k, v in
        {
            '&flag=cggg&bFlag=00&treenum=05': '招标公告/市级',
            '&flag=cjgg&bFlag=00&treenum=06': '中标公告/市级',
            '&flag=cggg&bFlag=qxgg&treenum=05': '招标公告/区县',
            '&flag=cjgg&bFlag=qxgg&treenum=06': '中标公告/区县'
        }.items()
    ]

    def start_requests(self):
        for url, data in self.start_pages:
            yield scrapy.Request(url, meta={'params': data}, dont_filter=True)

    def link_requests(self, response):
        link_extractor = NodesExtractor(css='#bulletininfotable_table tr a',
                                        attrs_xpath={'days': '../../td[3]//text()', 'text': './/text()'})
        for node in link_extractor.extract_nodes(response):
            url = 'http://www.zfcg.sh.gov.cn/emeb_bulletin.do?method=showbulletin&bulletin_id=' + node['value']
            data = dict(response.meta['params'], **node)
            yield scrapy.Request(url, meta={'data': data}, callback=self.parse_item)

    def page_requests(self, response):
        page_extractor = NodeValueExtractor(css='.nextPage', value_xpath='./@onclick', value_regex='(\d+)')
        page = page_extractor.extract_value(response)
        if page:
            form = { 'bulletininfotable_p': str(page) }
            yield scrapy.FormRequest.from_response(response, formid='bulletininfotable', formdata=form, meta=response.meta)

    def parse_item(self, response):
        pass
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

        days = data.get('days', '').strip('()').split('/')
        g['day'] = DateExtractor.extract(days and days[0] or None)
        g['end'] = DateExtractor.extract(days[1:] and days[1] or None, max_day=None)
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.alias
        g['subject'] = data.get('subject')
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css='#templateContext > p, #templateContext > table')
        g['contents'] = content_extractor.extract_contents(response)
        g['pid'] = None
        g['tender'] = None
        g['budget'] = None
        g['tels'] = None
        g['extends'] = data
        g['digest'] = content_extractor.extract_digest(response)
        yield g
