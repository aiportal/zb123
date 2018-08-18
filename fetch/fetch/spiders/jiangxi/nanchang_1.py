import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class nanchang_1Spider(scrapy.Spider):
    """
    @title: 南昌建设招投标网
    @href: http://www.ncjsztb.com/ncjsztbw/
    """
    name = 'jiangxi/nanchang/1'
    alias = '江西/南昌'
    allowed_domains = ['ncjsztb.com']
    start_urls = [
        ('http://www.ncjsztb.com/ncjsztbw/Template/Default/zbgg_more.aspx', '招标公告/建设工程'),
    ]

    link_extractor = MetaLinkExtractor(css='a[target=_blank]:contains(查看)',
                                       attrs_xpath={'text': '../../td[2]//text()',
                                                    'day': '../../td[last()-1]//text()'})

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
        body = response.css('#TDContent, #trAttach')

        day = FieldExtractor.date(data.get('day') or response.css('#tdTitle font:contains(信息时间)'))
        title = data.get('title') or data.get('text')
        if title.endswith('...'):
            title = FieldExtractor.text(response.css('#tdTitle font > b')) or title
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
