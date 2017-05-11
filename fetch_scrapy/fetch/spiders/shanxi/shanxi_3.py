import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


class shanxi_3Spider(scrapy.Spider):
    """
    @title: 山西省公共资源交易服务中心
    @href: http://prec.sxzwfw.gov.cn/Home/IndexDefault
    """
    name = 'shanxi/3'
    alias = '山西'
    allowed_domains = ['sxzwfw.gov.cn']
    start_urls = ['http://prec.sxzwfw.gov.cn/TenderProject/ColTableInfo']
    start_params = [
        ('招标公告/政府采购', {'huanJie': 'NOTICE', 'projectType': 'zfcg'}),
        # ('中标公告/政府采购', {'huanJie': 'PUBLICITY', 'projectType': 'zfcg'}),
        # ('招标公告/建设工程', {'huanJie': 'NOTICE', 'projectType': 'gcjs'}),
        # ('中标公告/建设工程', {'huanJie': 'PUBLICITY', 'projectType': 'gcjs'}),
    ]
    default_param = {
        'projectName': '',
        'date': '1day',
        'area': '不限',
        'dataSource': '不限',
        'pageIndex': '1',
    }

    link_extractor = MetaLinkExtractor(css='ul > li a[target=_blank]',
                                       attrs_xpath={'text': './/text()', 'day': '../span//text()'})

    def start_requests(self):
        url = self.start_urls[0]
        for subject, param in self.start_params:
            param.update(**self.default_param)
            data = dict(subject=subject)
            yield scrapy.FormRequest(url, formdata=param, meta={'data': data, 'form': param}, dont_filter=True)

    def parse(self, response):
        links = self.link_extractor.links(response)
        # assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

        if links:
            form = response.meta['form']
            form['pageIndex'] = str(int(form['pageIndex']) + 1)
            yield scrapy.FormRequest(response.url, formdata=form, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('div.notice_content')

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
