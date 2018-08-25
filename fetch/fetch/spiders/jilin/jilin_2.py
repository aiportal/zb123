import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class jilin_1Spider(scrapy.Spider):
    """
    @title: 吉林省公共资源首页
    @href: http://www.ggzyzx.jl.gov.cn/
    """
    name = 'jilin/2'
    alias = '吉林'
    allowed_domains = ['jlsggzyjy.gov.cn']
    start_urls = [
        # ('http://www.ggzyzx.jl.gov.cn/jyxx/005002/005002001/moreinfo.html', '招标公告/政府采购'),
        # ('http://www.ggzyzx.jl.gov.cn/jyxx/005002/005002004/moreinfo.html', '中标公告/政府采购'),
        # # ('http://www.ggzyzx.jl.gov.cn/jyxx/005002/005002007/moreinfo.html', '废标公告/政府采购'),
        # ('http://www.ggzyzx.jl.gov.cn/jyxx/005005/005005001/moreinfo.html', '招标公告/政府采购'),
        # ('http://www.ggzyzx.jl.gov.cn/jyxx/005005/005005004/moreinfo.html', '中标公告/政府采购'),
        # # ('http://www.ggzyzx.jl.gov.cn/jyxx/005005/005005006/moreinfo.html', '废标公告/政府采购'),
        # ('http://www.ggzyzx.jl.gov.cn/jyxx/005001/005001001/moreinfo.html', '招标公告/工程建设'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 5.88}

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_extractor = MetaLinkExtractor(css='#jt ul > li a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../../span//text()'})

    def parse(self, response):
        links = self.link_extractor.links(response)
        # assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.Section1')

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name,
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=[self.alias, data.get('area', '').strip('[]')])
        g.set(subject=[data.get('subject'), data.get('sub', '').strip('[]')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
