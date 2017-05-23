import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class xilinguole_1Spider(scrapy.Spider):
    """
    @title: 锡林郭勒盟公共资源交易中心
    @href: http://www.xmzwggzy.com/xmweb/default.aspx
    """
    name = 'neimenggu/xilinguole/1'
    alias = '内蒙古/锡林郭勒盟'
    allowed_domains = ['xmzwggzy.com']
    start_urls = [
        ('http://www.xmzwggzy.com/xmweb/showinfo/zbgg_moreNew.aspx?'
         'categoryNum=009001005001&categoryNum2=009002006001&categoryNum3=009003003001&categoryNum4=009004003001'
         '&categoryNum5=009002008', '招标公告/盟本级'),
        ('http://www.xmzwggzy.com/xmweb/showinfo/zbgg_more.aspx?'
         'categoryNum=009001006001&categoryNum2=009002007001&categoryNum3=009003004001&categoryNum4=009004004001',
         '招标公告/旗县市级'),
        ('http://www.xmzwggzy.com/xmweb/showinfo/zbgg_more.aspx?'
         'categoryNum=009001005005&categoryNum2=009002006004&categoryNum3=009003003004&categoryNum4=009004003004',
         '更正公告/盟本级'),
        ('http://www.xmzwggzy.com/xmweb/showinfo/zbgg_more.aspx?'
         'categoryNum=009001006005&categoryNum2=009002007004&categoryNum3=009003004004&categoryNum4=009004004004',
         '更正公告/旗县市级'),
        ('http://www.xmzwggzy.com/xmweb/showinfo/zbgg_more.aspx?'
         'categoryNum=009001005004&categoryNum2=009002006002&categoryNum3=009003003002&categoryNum4=009004003002',
         '中标公告/盟本级'),
        ('http://www.xmzwggzy.com/xmweb/showinfo/zbgg_more.aspx?'
         'categoryNum=009001006004&categoryNum2=009002007002&categoryNum3=009003004002&categoryNum4=009004004002',
         '中标公告/旗县市级'),
    ]

    link_extractor = MetaLinkExtractor(css='a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

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
        body = response.css('#TDContent, #trAttach') \
            or response.xpath('//span[@id="lblProjectName"]/../../../../../../../*')

        day = FieldExtractor.date(data.get('day'))
        title = data.get('title') or data.get('text')
        if title.endswith('...'):
            title1 = FieldExtractor.text(response.css('#tdTitle b'))
            if len(title)-3 < len(title1) < 200:
                title = title1 or title
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
