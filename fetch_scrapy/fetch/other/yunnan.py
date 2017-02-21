import scrapy
from . import HtmlMetaSpider, GatherItem
from . import NodeValueExtractor, MetaLinkExtractor, DateExtractor, HtmlContentExtractor, FileLinkExtractor
import re


class YunnanSpider(HtmlMetaSpider):
    name = 'yunnan'
    alias = '云南'
    allowed_domains = ['yngp.com']
    start_referer = None
    start_urls = [
        'http://www.yngp.com/bulletin.do?method=moreList&sign=0&districtCode=all',
        'http://www.yngp.com/bulletin.do'
    ]
    start_params = {
        'sign': {
            '1': '招标公告',    # 谈判、询价、更正
            '2': '结果公告',
            # '3': '结果公告/单一来源', '4': '结果公告/进口产品', '5': '结果公告/合同公告'
        }
    }

    # 索引页详情链接
    link_extractor = MetaLinkExtractor(css='#bulletinstable_table tr > td > font', url_attr='value',
                                       url_process=lambda x: '/bulletin_zz.do?method=showBulletin&bulletin_id=' + x,
                                       attrs_xpath={'text': './text()', 'start': '../../td[last()]//text()',
                                                    'area': '../../td[2]//text()'})

    # 索引页翻页链接
    page_extractor = NodeValueExtractor(css='#bulletinstable_toolbar input[title=下一页]', value_xpath='./@onclick',
                                        value_regex='(\d+)')

    # 首先访问默认索引页，然后用from_response创建FormRequest
    def start_requests(self):
        yield scrapy.Request(self.start_urls[0])

    def parse(self, response):
        if isinstance(response.request, scrapy.FormRequest):
            requests = [r for r in super().parse(response)]
            return requests
        for k, v in self.start_params['sign'].items():
            form = {'sign': k}
            meta = {'params': {'sign': v}}
            headers = {'useAjaxPrep': True}
            yield scrapy.FormRequest.from_response(response, formid='bulletinstable', formdata=form, meta=meta,
                                                   headers=headers)

    def link_requests(self, response):
        for req in super().link_requests(response):
            data = req.meta['data']
            if not data.get('value', '').startswith('always_show'):
                yield req

    def page_requests(self, response):
        page = self.page_extractor.extract_value(response)
        if page:
            form = {'bulletinstable_p': page}   # 'bulletinstable_crd': 50  # 每页行数
            yield scrapy.FormRequest.from_response(response, formid='bulletinstable', formdata=form, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = GatherItem(source=self.name, uuid=self.uuid(), url=response.request.url)
        g['html'] = response.text
        g['index_url'] = response.request.headers.get('Referer').decode()
        g['top_url'] = response.meta.get('top_url')
        g['real_url'] = response.url

        g['day'] = DateExtractor.extract(data.get('start'))
        g['end'] = None
        g['title'] = data.get('title') or data.get('text')
        g['area'] = self.join_words(self.alias)
        g['subject'] = self.join_words(data.get('colcode'))
        g['industry'] = None

        # 详情页正文
        content_extractor = HtmlContentExtractor(css=('td.aa > *', 'td[bgcolor="#FFFFFF"] > table[width="100%"] tr'))
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
