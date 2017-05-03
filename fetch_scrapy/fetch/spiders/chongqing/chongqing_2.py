import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class chongqing_2Spider(scrapy.Spider):
    """
    @title: 
    @href: 
    """
    name = '/chongqing_2'
    alias = ''
    allowed_domains = ['']
    start_urls = [
        ('http://www.cqggzy.com/services/PortalsWebservice/getInfoList?response=application/json'
         '&pageIndex=1&pageSize=18&siteguid=d7878853-1c74-4913-ab15-1d72b70ff5e7&categorynum={}'
         '&title=&infoC='.format(k), v)
        for k, v in [
            # ('', '招标公告/建设工程'),
            # ('', '中标公告/建设工程'),
            # ('', '招标公告/政府采购'),
            # ('', '中标公告/政府采购'),
        ]
    ]

    link_extractor = MetaLinkExtractor(css='tr > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert len(links) > 0
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('')

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
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
