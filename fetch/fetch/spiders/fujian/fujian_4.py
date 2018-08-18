import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
from datetime import datetime


class fujian_4Spider(scrapy.Spider):
    """
    @title: 福建招标与采购网
    @href: http://www.fjbid.gov.cn/
    """
    name = 'fujian/4'
    alias = '福建'
    allowed_domains = ['fjbid.gov.cn']
    start_urls = [
        ('http://www.fjbid.gov.cn/zbgg1/zbgg/', '招标公告'),
        # ('http://www.fjbid.gov.cn/zbgg1/zbgs/', '中标公告'),
    ]

    link_extractor = NodesExtractor(css='table.bian-lan1 tr > td:nth-child(2) > a[target=_blank]',
                                    attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        rows = self.link_extractor.extract_nodes(response)
        assert rows
        for row in rows:
            path, date, pid = SpiderTool.re_text("getUrl\('(.+)','(.+)',(\d+),\w+\)", row['onmouseover'])
            day = FieldExtractor.date(date)
            url = urljoin(response.url, '{0}/{1:%Y%m}/t{1:%Y%m%d}_{2}.htm'.format(path, day, pid))
            row.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.xpath('//td[@class="t14" and @height="30"]')

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
