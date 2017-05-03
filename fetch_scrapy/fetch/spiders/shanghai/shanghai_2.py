import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import json


class Shanghai2Spider(scrapy.Spider):
    """
    @title: 上海市公共资源交易服务平台
    @href: http://222.66.64.149/publicResource/home.html
    """
    name = 'shanghai/2'
    alias = '上海'
    # allowed_domains = ['222.66.64.149']
    start_urls = [
        # ('http://222.66.64.149/publicResource/gp/searchGpBulletinByCriteria.ajax',
        #  'http://222.66.64.149/publicResource/gp/findGpBulletin.do?sourceId={[id]}',
        #  '招标公告/政府采购'),
        # ('http://222.66.64.149/publicResource/gp/searchGpResultByCriteria.ajax',
        #  'http://222.66.64.149/publicResource/gp/findGpWinnerBulletinDetail.do?sourceId={[id]}',
        #  '中标公告/政府采购'),
        ('http://222.66.64.149/publicResource/construction/listconstruction.ajax',
         'http://222.66.64.149/publicResource/construction/findConstructionBulletin.do?sourceId={[source_id]}',
         '招标公告/建设工程'),
        ('http://222.66.64.149/publicResource/construction/listconstructionresult.ajax',
         'http://222.66.64.149/publicResource/construction/findwinnerdetail.do?sourceid={[source_id]}',
         '中标公告/建设工程'),
    ]

    def start_requests(self):
        for url, detail, subject in self.start_urls:
            data = dict(detail=detail, subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        data = response.meta['data']
        pkg = json.loads(response.text)
        for row in pkg['pageBean']['dataList']:
            url = data['detail'].format(row)
            row.update(**data)
            yield scrapy.Request(url, meta={'data': row}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        """
        {
            "publicity_start_time": "2017/04/28",
            "publicity_name": "松江区玉阳大道（白苧路—车香路）新建工程",
            "project_name": "松江区玉阳大道（白苧路—车香路）新建工程",
            "sync_time": "2017-04-28 22:14:35",
            "publicity_content": "第一中标候选人：上海市凯达公路工程公司，投标价格：42588.1870，得分/投票：0；第二中标候选人：上海奉贤建设发展（集团）有限公司，投标价格：42900.8609，得分/投票：0；",
            "publicity_refer_time": "20170428000000",
            "source_id": "6979CBD4-92A6-420E-8327-846E7B49ADD1",
            "publicity_end_time": "20170504000000",
            "tender_project_code": "e3100000151008459002",
            "section_name": "松江区玉阳大道（白苧路—车香路）新建工程",
            "url": "http://www.ciac.sh.cn/XmZtbbaWeb/Gsqk/GsFb.aspx?zbdjid=58428&zbid=50558",
            "unified_deal_code": "A02-123100007847653857-20161012-000015-Q",
            "notice_media": "http://www.ciac.sh.cn",
            "bid_section_code": "e3100000151008459002001",
            "publicity_type": "1"
        },
        """
        data = response.meta['data']
        body = response.css('div.main_tb')

        day = FieldExtractor.date(*[data.get(k) for k in (
            'publishDate', 'publicity_start_time', 'notice_send_time', 'sync_time')])
        title = data.get('title') or data.get('project_name') or data.get('section_name')
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
