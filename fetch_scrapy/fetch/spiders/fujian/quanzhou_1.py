import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class quanzhou_1Spider(scrapy.Spider):
    """
    @title: 泉州市公共资源交易平台
    @href: http://www.qzcgzb.com/
    """
    name = 'fujian/quanzhou/1'
    alias = '福建/泉州'
    allowed_domains = ['qzcgzb.com']
    start_urls = [
        ('http://www.qzcgzb.com/BulletinInfoList.aspx?type=%E5%B7%A5%E7%A8%8B%E5%BB%BA%E8%AE%BE&flag=0&navId=4',
         [('#div1 > ul > li > a', '招标公告/建设工程'),
          ('#div2 > ul > li > a', '中标公告/建设工程'),
          ]),
        ('http://www.qzcgzb.com/BulletinInfoList.aspx?type=%E9%87%87%E8%B4%AD%E6%8B%9B%E6%A0%87&flag=0&navId=3',
         [('#div1 > ul > li > a', '招标公告/政府采购'),
          ('#div2 > ul > li > a', '中标公告/政府采购'),
          ])
    ]

    def start_requests(self):
        for url, subjects in self.start_urls:
            data = dict(subjects=subjects)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        data = response.meta['data']
        for css, subject in data['subjects']:
            extractor = MetaLinkExtractor(css=css, attrs_xpath={'text': './/text()', 'day': '../span//text()'})
            links = extractor.links(response)
            assert len(links) > 0
            for lnk in links:
                lnk.meta.update(**response.meta['data'])
                yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.content')

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
