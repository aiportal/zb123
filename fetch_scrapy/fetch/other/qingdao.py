import scrapy
from .. import HtmlMetaSpider
from .. import MetaLinkExtractor, DateExtractor, HtmlContentExtractor
import re


class QingdaoSpider(HtmlMetaSpider):
    name = 'shandong/qingdao'
    alias = '山东'
    allowed_domains = ["ccgp-qingdao.gov.cn"]
    start_referer = None
    start_urls = ['http://www.ccgp-qingdao.gov.cn/mhxt/MhxtSearchBulletinController.zc']
    start_params = {
        'method': 'bulletinChannelRightDown',
        'channelCode': {'sxqcg_cggg': '招标公告/采购公告', 'sxqcg_zbgg': '中标公告'},
        'pageNo': 1,
        'pageSize': 15
    }
    # 索引页详情链接
    link_extractor = MetaLinkExtractor(css='div.infoLink ul > li', url_attr='href',
                                       attrs_xpath={'text': './text()', 'start': '../span//text()'})
    # 索引页翻页链接
    page_extractor = MetaLinkExtractor(css='#searchHas', url_attr='href')

    def start_requests(self):
        url = self.start_urls[0] + '?method=bulletinChannelRightDown'
        for k, v in self.start_params['channelCode'].items():
            form = {'channelCode': k, 'pageNo': str(1), 'pageSize': str(15)}
        yield scrapy.FormRequest(url=url, formdata=form, meta={'subject': v}, dont_filter=True)

    def link_requests(self, response):
        for link in self.link_extractor.extract_links(response):
            url = re.sub('/mhxt/', '/', link.url)
            data = dict(link.meta, **response.meta['params'])
            yield scrapy.Request(url, meta={'data': data})

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']

        # GatherItem
        g = self.gather_item(response)

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
