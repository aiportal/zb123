import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class jiangyin_1Spider(scrapy.Spider):
    """
    @title: 江阴市公共资源服务中心
    @href: http://www.ggzy.com.cn/jyweb/Default.aspx
    """
    name = 'jiangsu/jiangyin/1'
    alias = '江苏/江阴'
    allowed_domains = ['ggzy.com.cn']
    start_urls = [
        ('http://www.ggzy.com.cn/jyweb/ShowInfo/Moreinfo.aspx?CategoryNum=003001001', '招标公告/建设工程'),
        ('http://www.ggzy.com.cn/jyweb/ShowInfo/Moreinfo.aspx?CategoryNum=003002002', '预公告/政府采购'),
        ('http://www.ggzy.com.cn/jyweb/ShowInfo/Moreinfo.aspx?CategoryNum=003002001', '招标公告/政府采购'),
    ]

    link_extractor = MetaLinkExtractor(css='#MoreInfoList1_DataGrid1 tr > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('#TDContent, .infodetail') or response.css('span#spnShow') or response.css('#tblInfo')

        day = FieldExtractor.date(data.get('day'), response.css('#tdTitle'))
        title = data.get('title') or data.get('text')
        contents = body.extract()
        g = GatherItem.create(
            response,
            source=self.name.split('/')[0],
            day=day,
            title=title,
            contents=contents
        )
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]
