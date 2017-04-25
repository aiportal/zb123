import scrapy
from fetch.extractors import MetaLinkExtractor, NodesExtractor, FieldExtractor
from fetch.tools import SpiderTool
from fetch.items import GatherItem
from urllib.parse import urljoin
import re


class JiangsuNantong1Spider(scrapy.Spider):
    """
    @title: 南通市政府采购网
    @href: http://zfcg.nantong.gov.cn/
    """
    name = 'jiangsu/nantong/1'
    alias = '江苏/南通'
    allowed_domains = ['nantong.gov.cn']
    start_urls = [
        ('http://zfcg.nantong.gov.cn/col/col31685/index.html', '预公告/网上询价'),
        ('http://zfcg.nantong.gov.cn/col/col31686/index.html', '预公告/其他询价'),
        ('http://zfcg.nantong.gov.cn/col/col30067/index.html', '招标公告/公开招标'),
        ('http://zfcg.nantong.gov.cn/col/col30069/index.html', '中标公告'),
        ('http://zfcg.nantong.gov.cn/col/col30070/index.html', '招标公告/县级'),
    ]

    def start_requests(self):
        for url, subject in self.start_urls:
            data = dict(subject=subject)
            yield scrapy.Request(url, meta={'data': data}, dont_filter=True)

    link_regex = "<tr><td .+<a href='(/art/.+\.html)' title='(.+)' target='_blank' .+\[(\d{4}-\d{2}-\d{2})\]</td></tr>"

    def parse(self, response):
        data = response.meta['data']
        links_body = ''.join(response.css('#80325').xpath('.//text()').extract())
        links = re.findall(self.link_regex, links_body)
        for href, title, day in links:
            url = urljoin(response.url, href)
            meta = dict(title=title, day=day, **data)
            yield scrapy.Request(url, meta={'data': meta}, callback=self.parse_item)

    def parse_item(self, response):
        """ 解析详情页 """
        data = response.meta['data']
        body = response.css('meta[name=ContentStart] ~ *')

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
        g.set(area=self.alias)
        g.set(subject=data.get('subject'))
        g.set(budget=FieldExtractor.money(body))
        return [g]

#
# <datastore>
# <nextgroup><![CDATA[<a href="/module/jslib/jquery/jpage/dataproxy.jsp?page=1&appid=1&appid=1&webid=60&path='/'&columnid=31685&unitid=80325&webname='南通市政府采购网'&permissiontype=0"></a>]]></nextgroup>
# <recordset>
# <table cellpadding='0' cellspacing='0' border='0' width='95%' align=center style="vertical-align:middle"></table><record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/4/24/art_31685_2451995.html' title='南通市公安局交警支队空调设备询价2017XJ3018' target='_blank' style='font-size:10.5pt'>南通市公安局交警支队空调设备询价2017XJ301...</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-04-24]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/4/20/art_31685_2451309.html' title='2017XJ3017' target='_blank' style='font-size:10.5pt'>2017XJ3017</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-04-20]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/4/19/art_31685_2450790.html' title='南通市城市照明管理处市政道路及维护项目控制箱 2017XJ2002第三次' target='_blank' style='font-size:10.5pt'>南通市城市照明管理处市政道路及维护项目控制箱 20...</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-04-19]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/4/17/art_31685_2449766.html' title='南通市中级人民法院数据中心公文系统平台扩容项目(2017XJ5002)' target='_blank' style='font-size:10.5pt'>南通市中级人民法院数据中心公文系统平台扩容项目(2...</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-04-17]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/4/14/art_31685_2449241.html' title='2017XJ3016' target='_blank' style='font-size:10.5pt'>2017XJ3016</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-04-14]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/4/14/art_31685_2449219.html' title='南通市照明管理处道路照明工程主材采购（电缆）2017XJ2005' target='_blank' style='font-size:10.5pt'>南通市照明管理处道路照明工程主材采购（电缆）201...</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-04-14]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/4/14/art_31685_2449216.html' title='南通市城市照明管理处市政道路及维护项目控制箱 2017XJ2002重新' target='_blank' style='font-size:10.5pt'>南通市城市照明管理处市政道路及维护项目控制箱 20...</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-04-14]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/4/14/art_31685_2449195.html' title='2017XJ3015' target='_blank' style='font-size:10.5pt'>2017XJ3015</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-04-14]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/4/12/art_31685_2448511.html' title='2017XJ3014' target='_blank' style='font-size:10.5pt'>2017XJ3014</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-04-12]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/4/6/art_31685_2446879.html' title='2017XJ3013' target='_blank' style='font-size:10.5pt'>2017XJ3013</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-04-06]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/4/1/art_31685_2445624.html' title='南通市城市照明管理处市政道路及维护项目控制箱 2017XJ2002' target='_blank' style='font-size:10.5pt'>南通市城市照明管理处市政道路及维护项目控制箱 20...</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-04-01]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/3/29/art_31685_2444347.html' title='2017XJ1011' target='_blank' style='font-size:10.5pt'>2017XJ1011</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-03-29]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/3/23/art_31685_2442482.html' title='2017XJ4004' target='_blank' style='font-size:10.5pt'>2017XJ4004</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-03-23]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/3/22/art_31685_2442054.html' title='2017XJ1010' target='_blank' style='font-size:10.5pt'>2017XJ1010</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-03-22]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/3/22/art_31685_2441976.html' title='2017XJ4003' target='_blank' style='font-size:10.5pt'>2017XJ4003</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-03-22]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/3/16/art_31685_2440074.html' title='2017XJ3011' target='_blank' style='font-size:10.5pt'>2017XJ3011</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-03-16]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/3/16/art_31685_2440058.html' title='2017XJ3012' target='_blank' style='font-size:10.5pt'>2017XJ3012</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-03-16]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/3/13/art_31685_2438781.html' title='2017XJ3010' target='_blank' style='font-size:10.5pt'>2017XJ3010</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-03-13]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/3/10/art_31685_2438027.html' title='南通市通明投资实业有限公司110KV电缆迁移工程项目 2017XJ2004' target='_blank' style='font-size:10.5pt'>南通市通明投资实业有限公司110KV电缆迁移工程项...</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-03-10]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/3/9/art_31685_2437351.html' title='会议室无纸化办公改造项目(2017XJ4002)' target='_blank' style='font-size:10.5pt'>会议室无纸化办公改造项目(2017XJ4002)</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-03-09]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/3/8/art_31685_2436939.html' title='2017XJ3009' target='_blank' style='font-size:10.5pt'>2017XJ3009</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-03-08]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/3/8/art_31685_2436935.html' title='南通市电子政务外网DMZ区云平台计算及存储资源扩容项目2017XJ2003' target='_blank' style='font-size:10.5pt'>南通市电子政务外网DMZ区云平台计算及存储资源扩容...</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-03-08]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/3/7/art_31685_2436496.html' title='2017XJ1009' target='_blank' style='font-size:10.5pt'>2017XJ1009</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-03-07]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/3/6/art_31685_2435467.html' title='2017XJ3008' target='_blank' style='font-size:10.5pt'>2017XJ3008</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-03-06]</td></tr>]]></record>
# <record><![CDATA[
# <tr><td width=15 valign="middle" style="vertical-align:middle"><IMG src="http://daj.nantong.gov.cn/picture/0/090604143856634.gif" align=absMiddle></td><td style='border-bottom:1px dashed #999999;font-size:10.5pt;line-height: 30px;'><a href='/art/2017/2/27/art_31685_2432948.html' title='2017XJ1008' target='_blank' style='font-size:10.5pt'>2017XJ1008</a></td><td width='100' align='right' valign="middle" style='border-bottom:1px dashed #999999;color:#999999;font-size:10.5pt;vertical-align:middle'>[2017-02-27]</td></tr>]]></record>
# </recordset>
# </datastore>