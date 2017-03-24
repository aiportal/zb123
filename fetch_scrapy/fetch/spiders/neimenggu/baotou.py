import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import re


class BaotouSpider(scrapy.Spider):
    name = 'neimenggu/baotou'
    alias = '内蒙古/包头'
    allowed_domains = ['btzfcg.gov.cn']
    start_urls = ['http://www.btzfcg.gov.cn/portal/topicView.do?method=view']
    start_params = {
        'view': 'stockBulletin',
        'id': {
            '1660': '招标公告/市级',
            '2014': '中标公告/市级',
            '1663': '更正公告/市级',
            # '2015': '合同公告/市级',
            # '555845': '验收公告/市级',
            '1662': '招标公告/县级',
            '1664': '中标公告/县级',
            '1666': '更正公告/县级',
            # '2016': '合同公告/县级',
            # '555846': '验收公告/县级',
        },
        'ver': '2',
        'ec_i': 'topicChrList_20070702',            # 控件ID
        'topicChrList_20070702_p': '1',             # 页码
        'topicChrList_20070702_crd': '50',          # 每页行数
    }

    def start_requests(self):
        url = self.start_urls[0]
        for form, data in SpiderTool.iter_params(self.start_params):
            yield scrapy.FormRequest(url, formdata=form, meta={'form': form, 'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css=('#topicChrList_20070702_table > tbody > tr > td > a',),
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})
    page_extractor = NodeValueExtractor(xpath=('//select[@name="__ec_pages"]/option',), value_xpath='./text()')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for link in links:
            url = self.real_url(link.url)
            link.meta['subject'] = response.meta['data']['id']
            yield scrapy.Request(url, meta={'data': link.meta}, callback=self.parse_item)

        pages = self.page_extractor.extract_values(response)
        count = max([int(x) for x in pages])
        form = response.meta['form']
        page = int(form['topicChrList_20070702_p']) + 1
        if page <= count:
            form['topicChrList_20070702_p'] = str(page)
            yield scrapy.FormRequest(response.url, formdata=form, meta=response.meta)

    @staticmethod
    def real_url(url):          # 减少一次302跳转
        mc = re.findall('=(\d+)$', url)
        if mc:
            return url
            # return 'http://www.btzfcg.gov.cn/portal/documentView.do?method=view&id={}&ver=null'.format(mc[0])
        else:
            return url

    def parse_item(self, response):
        """ 解析详情页 """

        data = response.meta['data']
        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        contents = response.css('#bulletinContent').extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(response.css('#bulletinContent')))
        return [g]
