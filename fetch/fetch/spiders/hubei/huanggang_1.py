import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class huanggang_1Spider(scrapy.Spider):
    """
    @title: 黄冈公共资源交易信息网
    @href: http://www.hgzbtb.com/ceinwz/indexhg.htm
    """
    name = 'hubei/huanggang/1'
    alias = '湖北/黄冈'
    allowed_domains = ['hgzbtb.com']
    start_base = 'http://www.hgzbtb.com/ceinwz/WebInfo_List.aspx?showDate=1'
    start_urls = [
        (start_base + '&newsid=400&zfcg=0100000&FromUrl=zfcgzq','招标公告/政府采购'),
        (start_base + '&newsid=401&zfcg=0000010&FromUrl=zfcgzq', '中标公告/政府采购'),
        (start_base + '&newsid=700&jscg=0100000&FromUrl=jsgczq&zbdl=1', '招标公告/建设工程'),
        (start_base + '&newsid=701&jscg=0000010&FromUrl=jsgczq&zbdl=1', '中标公告/建设工程'),
    ]
    detail_url = 'http://www.hgzbtb.com/temphtml/_a99de280-eabc-4e45-a95c-5ebfc297800b.doc20170502172906.html'

    link_extractor = MetaLinkExtractor(css='table.myGVClass tr > td > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        if response.css('#frmBestwordHtml'):
            src = response.css('#frmBestwordHtml').xpath('./@src').extract_first()
            url = urljoin(response.url, src)
            return scrapy.Request(url, meta=response.meta, callback=self.parse_item)

        data = response.meta['data']
        if '/temphtml/' in response.url:
            body = response.css('body')
        else:
            body = response.css('#ctl00_ContentPlaceHolder1_BodyLabel')
        prefix = '^\[\w{2,8}\]'

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        title = re.sub(prefix, '', title)
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
