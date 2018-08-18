import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class xiantao_1Spider(scrapy.Spider):
    """
    @title: 仙桃市公共资源交易信息网
    @href: http://www.xtggzy.com/
    """
    name = 'hubei/xiantao/1'
    alias = '湖北/仙桃'
    allowed_domains = ['xtggzy.com']
    start_urls = ['http://www.xtggzy.com/Article/SearchArticle']
    start_params = [
        ('招标公告', {'categoryId': '676'}),
    ]
    default_param = {
        'pageNum': '1',
        'pageSize': '10',
        'search': 'false',
    }

    link_extractor = MetaLinkExtractor(css='#listCon ul > li > a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

    def start_requests(self):
        url = self.start_urls[0]
        for subject, param in self.start_params:
            param.update(**self.default_param)
            data = dict(subject=subject)
            yield scrapy.FormRequest(url, formdata=param, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('table.table_detail, div.content_box') or response.css('#content')

        day = FieldExtractor.date(data.get('day'), response.css('div.news_time'))
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
