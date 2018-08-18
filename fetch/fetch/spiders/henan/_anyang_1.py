import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin


"""
<script>
function t3_ar_guard() {
    eval(
    function(p, a, c, k, e, d) {
        e = function(c) { return c };

        if (!''.replace(/^/, String)) {
            while (c--) {
                d[c] = k[c] || c
            }
            alert(d);
            k = [function(e) {
                return d[e]
            }];
            e = function() {
                return '\\w+'
            };
            c = 1
        };
        while (c--) {
            if (k[c]) {
                p = p.replace(new RegExp('\\b' + e(c) + '\\b', 'g'), k[c])
            }
        }
        alert(p);
        return p
    }
    ('0.3="4=7/6;5=/";0.2.1=0.2.1;', 8, 8, 'document|href|location|cookie|ant_stream_562f497bcd3d7|path|156792140|1494323099'.split('|'), 0, {}))
}
</script>
<a href="/stream_562f497bcd3d7_58d25ba0a0a2b?id=2" style="display:none">

"""

class anyang_1Spider(scrapy.Spider):
    """
    @title: 安阳市公共资源交易中心
    @href: http://www.ayggzy.cn/
    """
    name = 'henan/anyang/1'
    alias = '河南/安阳'
    allowed_domains = ['ayggzy.cn']
    start_urls = [
        # ('http://www.ayggzy.cn/xmlist.aspx?leiid=zfcg&isgg=1&sigle=yes', '预公告/政府采购'),
        # ('http://www.ayggzy.cn/xmlist.aspx?leiid=zfcg&isgg=0&sigle=yes', '招标公告/政府采购'),
        # ('http://www.ayggzy.cn/zbgslist.aspx?leiid=zfcg&sigle=yes', '中标公告/政府采购'),
        # ('http://www.ayggzy.cn/xmlist.aspx?leiid=jsgc&isgg=0&sigle=yes', '招标公告/建设工程'),
        # ('http://www.ayggzy.cn/zbgslist.aspx?leiid=jsgc&sigle=yes', '中标公告/建设工程'),
    ]
    custom_settings = {'DOWNLOAD_DELAY': 3.2, 'COOKIES_ENABLED': True}

    link_extractor = MetaLinkExtractor(css='div.page_right tr > td > a',
                                       attrs_xpath={'text': './/text()', 'day': '../../td[last()]//text()'})

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    def parse(self, response):
        # JAVASCRIPT 脚本设置cookie，然后脚location转向。
        links = self.link_extractor.links(response)
        assert links
        for lnk in links:
            lnk.meta.update(**response.meta['data'])
            yield scrapy.Request(lnk.url, meta={'data': lnk.meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('table.p_info, div.content')

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
