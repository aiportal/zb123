import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class guangdong_1Spider(scrapy.Spider):
    """
    @title: 广东省政府采购网
    @href: http://www.gdgpo.gov.cn/
    """
    name = 'guangdong/1'
    alias = '广东'
    allowed_domains = ['gdgpo.gov.cn']
    start_urls = ['http://www.gdgpo.gov.cn/queryMoreInfoList.do']
    start_params = {
        'channelCode': {
            '0005': '招标公告/采购公告',
            '0006': '更正公告',
            '0008': '中标公告',
        },
        # 'pageIndex': 1,
        # 'pageSize': 15
    }

    link_extractor = MetaLinkExtractor(css='ul.m_m_c_list > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../em//text()'})

    def start_requests(self):
        url = self.start_urls[0]
        for form, data in SpiderTool.iter_params(self.start_params):
            yield scrapy.FormRequest(url, formdata=form, meta={'data': data, 'form': form})

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.zw_c_c_cont')
        pid = '（[A-Z0-9-]{8,}）'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(pid, '', title)
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
