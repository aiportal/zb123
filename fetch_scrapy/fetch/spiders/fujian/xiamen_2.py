import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
from datetime import date


class xiamen_2Spider(scrapy.Spider):
    """
    @title: 厦门工程招标投标信息网
    @href: http://www.cztb.xm.fj.cn/newasite/index.aspx
    """
    name = 'fujian/xiamen/2'
    alias = '福建/厦门'
    allowed_domains = ['xm.fj.cn']
    start_urls = [
        ('http://www.cztb.xm.fj.cn/newasite/Project/IST_TDNoticeList.aspx', '招标公告/建设工程', 0),
        ('http://www.cztb.xm.fj.cn/newasite/Project/IST_WBDClassList.aspx', '中标公告/建设工程', 1),
    ]

    link_extractors = (
        MetaLinkExtractor(css='#GridView1 tr > td:nth-child(2) > a[target=_blank]',
                          attrs_xpath={'text': './/text()', 'day': '../../td[3]//text()'}),
        MetaLinkExtractor(css='#GridView1 tr > td:nth-child(2) > a[target=_blank]',
                          attrs_xpath={'text': './/text()', 'budget': '../../td[4]//text()'})
    )

    def start_requests(self):
        for url, subject, extractor in self.start_urls:
            data = dict(subject=subject, extractor=extractor)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        extractor = self.link_extractors[response.meta['data']['extractor']]
        links = extractor.links(response)
        assert len(links)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#CopyShow') or response.css('body')

        day = FieldExtractor.date(data.get('day') or date.today())
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
        g.set(budget=data.get('budget') or FieldExtractor.money(body))
        return [g]
