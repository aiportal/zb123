import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class erlianhaote_1Spider(scrapy.Spider):
    """
    @title: 二连浩特市公共资源服务中心
    @href: http://zwggzy.elht.gov.cn/
    """
    name = 'neimenggu/erlianhaote/1'
    alias = '内蒙古/二连浩特'
    allowed_domains = ['elht.gov.cn']
    start_urls = [
        ('http://zwggzy.elht.gov.cn/zfcg/zbgg/', '招标公告/政府采购'),
        ('http://zwggzy.elht.gov.cn/zfcg/zbgs/', '中标公告/政府采购'),
        ('http://zwggzy.elht.gov.cn/zfcg/fbgg/', '废标公告/政府采购'),
        ('http://zwggzy.elht.gov.cn/jsztb/zbgg/', '招标公告/建设工程'),
        ('http://zwggzy.elht.gov.cn/jsztb/zbgs/', '中标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='#mm2 ul > li > a',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

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
        data = response.meta['data']
        body = response.css('#div_content')

        day = FieldExtractor.date(data.get('day') or response.css('div.title_f'))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name,
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
