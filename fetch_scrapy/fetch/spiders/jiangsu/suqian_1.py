import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class JiangsuSuqianSpider(scrapy.Spider):
    """
    @title: 宿迁市公共资源交易网
    @href: http://www.sqggzyjy.gov.cn/sqzbtb/default.aspx
    """
    name = 'jiangsu/suqian/1'
    alias = '江苏/宿迁'
    allowed_domains = ['sqggzyjy.gov.cn']
    start_urls = [
        ('http://www.sqggzyjy.gov.cn/sqzbtb/jyxx/008001/008001001/', '招标公告/工程建设'),
        ('http://www.sqggzyjy.gov.cn/sqzbtb/jyxx/008001/008001006/', '中标公告/工程建设'),
        ('http://www.sqggzyjy.gov.cn/sqzbtb/jyxx/008002/008002007/', '预公告/政府采购'),
        ('http://www.sqggzyjy.gov.cn/sqzbtb/jyxx/008002/008002001/', '招标公告/政府采购'),
        ('http://www.sqggzyjy.gov.cn/sqzbtb/jyxx/008002/008002003/', '中标公告/政府采购'),
        ('http://www.sqggzyjy.gov.cn/sqzbtb/jyxx/008002/008002002/', '更正公告/政府采购'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='tr > td > a[target=_blank]',
                                       attrs_xpath={'text': './text()', 'day': '../../td[last()]//text()',
                                                    'tags': './font//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#TDContent, trAttach') or response.css('.infodetail, trAttach') or response.css('#tblInfo')
        tags = data.get('tags', '').strip('[]').split('][') + ['']
        assert len(tags) >= 2

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias, tags[0]])
        g.set(subject=[data.get('subject'), tags[1]])
        g.set(budget=FieldExtractor.money(body))
        return [g]
