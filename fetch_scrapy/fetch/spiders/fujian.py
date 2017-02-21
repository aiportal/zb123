import scrapy
from . import JsonMetaSpider, GatherItem
from . import DateExtractor, HtmlContentExtractor, JsonLinkGenerator, JsonPageGenerator
import json


class FujianSpider(JsonMetaSpider):
    name = 'fujian'
    alias = '福建'
    allowed_domains = ["cz.fjzfcg.gov.cn"]
    start_referer = 'http://cz.fjzfcg.gov.cn/n/webfjs/secpag.do'
    start_urls = ['http://cz.fjzfcg.gov.cn/n/webfjs/queryPageData.do?']
    start_params = {
        'zs': 1,
        'sid': {
            '200100007': '预公告',
            '200100001': '招标公告',
            '200100002': '中标公告',
            '200100003': '其他公告/补充公告',
            '200100009': '其他公告/流标公告',
            '200100010': '其他公告/分散采购公告',
            # '200100008': '预审结果公告',
            # '200100015': '延期公告',
            # '200100016': '结果变更',
            # '200100017': '资格预审公告',
        },
        'level': {'province': '省级', 'city': '市级', 'county': '县级'},
        'page': 1,
        'rows': 20,
    }
    custom_settings = {'COOKIES_ENABLED': True, 'DOWNLOAD_DELAY': 3.0}

    def start_requests(self):
        url = self.start_urls[0]
        for lk, lv in self.start_params['level'].items():
            for sk, sv in self.start_params['sid'].items():
                form = {'zs': '1', 'sid': sk, 'level': lk, 'page': '1', 'rows': '20'}
                params = {'level': lv, 'sid': sv}
                yield scrapy.FormRequest(url, formdata=form, meta={'params': params, 'form': form}, dont_filter=True)

    link_generator = JsonLinkGenerator('/n/noticemgr/query-viewcontentfj.do?noticeId={0[noticeId]}',
                                       '/n/webfjs/article.do?noticeId={0[noticeId]}', lambda x: x['list'])

    def page_requests(self, response):
        res = json.loads(response.text)
        total = int(res['list1'][0]['TOTAL'])
        form = response.meta['form']
        page = int(form['page'])
        size = int(form['rows'])
        if (page * size) < total:
            form['page'] = str(page + 1)
            yield scrapy.FormRequest(self.start_urls[0], formdata=form, meta=response.meta)

    def parse_item(self, response):
        """ 解析详情页
        """
        self.logger.info('parse item: ' + response.url)
        data = response.meta['data']
        # 'areaCode' (2100655384112) = {str} '591'      （地区编码）
        # 'areaName' (2100655384176) = {str} '福建省'
        # 'author' (2100655324832) = {str} 'C025052BDB3740F89B7ED926C9A3DF79'   (招标单位？)
        # 'bidDate' (2100655324888) = {str} '20161020093000'
        # 'dictCode' (2100655384304) = {str} '200100001'
        # 'noticeId' (2100655384432) = {str} '2DC88C76265B4CA79AA4AB4F00C22C32'
        # 'proId' (2100655324944) = {str} 'FJXW2016065'
        # 'time' (2100655325000) = {str} '20160928145005'
        # 'title' (2100655325056) = {str} '卫生应急队伍装备建设项目项目招标公告'
        # 'type' (2100655325112) = {str} '招标公告'

        # GatherItem
        g = self.gather_item(response)

        g['day'] = DateExtractor.extract(data.get('time'))
        g['end'] = DateExtractor.extract(data.get('bidDate'))
        g['title'] = data.get('title')
        g['area'] = self.join_words(self.alias, data.get('level'), data.get('areaName'))
        g['subject'] = self.join_words(data.get('sid'), data.get('zzxs'), data.get('type'))
        g['industry'] = None

        content_extractor = HtmlContentExtractor(xpath='//body')
        g['contents'] = response.xpath('//body').extract()
        g['pid'] = data.get('proId')
        g['tender'] = self.join_words(data.get('author'))
        g['budget'] = None
        g['tels'] = None
        g['extends'] = data
        g['digest'] = content_extractor.extract_digest(response)

        yield g
