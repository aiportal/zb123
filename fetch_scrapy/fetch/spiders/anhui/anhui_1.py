import scrapy
from fetch.extractors import MetaLinkExtractor, NodeValueExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
import re


# 安徽省政府采购
# http://www.ahzfcg.gov.cn/


class AnhuiNewSpider(scrapy.Spider):
    name = 'anhui/0'
    alias = '安徽'
    allow_domains = ['ahzfcg.gov.cn']
    start_urls = ['http://www.ahzfcg.gov.cn/mhxt/MhxtSearchBulletinController.zc?method=bulletinChannelRightDown']
    start_params = {
        'channelCode': 'sjcg',
        'bType': {
            '01': '招标公告/采购公告',
            '02': '更正公告',
            '03': '中标公告',
            # '04': '成交公告',
            # '06': '单一来源公示',
            # '99': '合同公告',
            '07': '废标公告',
            # '08': '其他公告',
        },
        'pageNo': '1',
    }

    def start_requests(self):
        url = self.start_urls[0]
        for form, data in SpiderTool.iter_params(self.start_params):
            yield scrapy.FormRequest(url, formdata=form, meta={'form': form, 'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='div.infoLink ul > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})
    # page_extractor = NodeValueExtractor(css='input[name=totalPageCount]', value_xpath='./@value')

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            url = re.sub(r'/mhxt/news/', '/news/', lnk.url)
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': lnk.meta}, callback=self.parse_item)

        # pager = self.page_extractor.extract_value(response)
        # count = SpiderTool.re_nums('(\d+)', pager)
        # page = int(response.meta['form']['pageNo']) + 1
        # if page < count:
        #     response.meta['form']['pageNo'] = str(page)
        #     yield scrapy.FormRequest(response.url, formdata=response.meta['form'], meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.frameNews')

        day = FieldExtractor.date(data.get('day'), body)
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
