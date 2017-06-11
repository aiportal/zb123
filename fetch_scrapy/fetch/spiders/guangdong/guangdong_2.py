import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class guangdong_2Spider(scrapy.Spider):
    """
    @title: 广东省公共资源交易中心
    @href: http://www.gdggzy.org.cn/prip-portal-web/main/Index.do
    """
    name = 'guangdong/2'
    alias = '广东'
    allowed_domains = ['gdggzy.org.cn']
    start_urls = ['http://www.gdggzy.org.cn/prip-portal-web/main/viewList.do']
    start_params = {
        'typeId': {
            '30011': '招标公告/政府采购',
            '30012': '中标公告/政府采购',
            '200122': '招标公告/建设工程',
            '200125': '中标公告/建设工程',
        },
        'city': 'gd',
        'currPage': '1',
        'pageSize': '20',
    }
    detail_url = 'http://www.gdggzy.org.cn/prip-portal-web/PortalNews/portalNewsConten.do?id={}'

    link_extractor = MetaLinkExtractor(css='div.list_box ul > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../li[last()]//text()'})

    def start_requests(self):
        url = self.start_urls[0]
        for form, data in SpiderTool.iter_params(self.start_params):
            yield scrapy.FormRequest(url, formdata=form, meta={'data': data, 'form': form})

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            pid = SpiderTool.re_text('=(\d+)$', lnk.url)
            url = self.detail_url.format(pid)
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': lnk.meta, 'top_url': lnk.url}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#portalNewsContent') or response.css('body')
        pid = '[（(](项目编号：)?[A-Z0-9-（）]{8,}[)）]'

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
        g.set(subject=[data.get('typeId')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
