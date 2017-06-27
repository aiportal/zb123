import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class datangSpider(scrapy.Spider):
    """
    @title: 大唐集团集采平台
    @href: http://jc.cdtbid.cn/html/index.html
    """
    name = 'other/datang/1'
    alias = '其他/大唐'
    allowed_domains = ['cdtbid.cn']
    start_urls = [
        ('http://jc.cdtbid.cn/project_list.jsp?site=global&column_code=014001001&project_type=1&is_reply=0', '招标公告'),
    ]

    link_extractor = NodesExtractor(css='div.contentRight tr > td > a',
                                    attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        rows = self.link_extractor.extract_nodes(response)
        assert rows
        for row in rows:
            col, no = SpiderTool.re_text("showProjectDetail\('(\d+)','(\d+)'\);", row['onclick'])
            url = urljoin(response.url, '/html/project/{0}/{1}.html'.format(col, no))
            row.update(**response.meta['data'])
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.article')

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
        g.set(area=[self.alias])
        g.set(subject=[data.get('subject')])
        g.set(budget=FieldExtractor.money(body))
        return [g]
