# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from database import JobIndex
from telephone.parsers import InfoDict
from telephone.items import TelephoneItem
import re
from urllib import parse
from datetime import datetime
import uuid
import json
import random
import sys
import logging
import time


class MinglujiSpider(scrapy.Spider):
    name = 'mingluji'
    custom_settings = {
        'COOKIES_ENABLED': True,
        'DOWNLOAD_DELAY': 0.1,
        # 'COOKIES_DEBUG': __debug__ and True or False,
        'DOWNLOADER_MIDDLEWARES': {
            'telephone.middlewares.DynamicDelayMiddleware': 200,
        }
    }

    area_items = {
        'beijing': 171800,
        'tianjin': 111800,
        'hebei': 633500,
        'neimenggu': 47600,
        'shanxi': 63800,
        'shanghai': 437980,
        'anhui': 277800,
        'jiangsu': 674580,
        'zhejiang': 1084880,
        'shandong': 583000,
        'jiangxi': 198550,
        'fujian': 320550,
        'guangdong': 1218880,
        'guangxi': 27050,
        'hainan': 15410,
        'henan': 363020,
        'hubei': 283980,
        'hunan': 375220,
        'heilongjiang': 90100,
        'jilin': 95360,
        'liaoning': 248680,
        'shaanxi': 132110,
        'gansu': 80880,
        'ningxia': 3450,
        'qinghai': 1220,
        'xinjiang': 9040,
        'chongqing': 164220,
        'sichuan': 221110,
        'yunnan': 117470,
        'guizhou': 45610,
        'xizang': 22
    }

    industry_list = [
        '五金', '仪器', '保险', '信贷', '储运', '农业', '冶金', '出版', '包装', '化工', '器材', '土产', '展览', '工程', '广告',
        '建筑', '房地产', '服装', '机械', '机电', '林业', '水产', '水利', '汽车', '烟草', '煤气', '煤炭', '电力', '电器', '电子',
        '畜产', '盐业', '石油', '矿产', '租赁', '纺织', '经济贸易', '自来水', '航空', '证券', '贸易', '轻工业', '运输', '造船',
        '金属', '铁路', '食品'
    ]

    login_accounts = {
        '可可粉': '111111',
        '阿斯顿': '111111',
        '嗖嗖嗖': '111111',
        '挑剔': '111111',
        '恰恰': '111111',
        '计划': '123123',
        '洪新': '123123',
        '尊胜': '123123',
        '播播': '123123',
        '王五': '111111',
        '亲亲': '123123',
        '寿司': '222222',
        '订单': '333333',
        '方法': '222222',
        '正则': '222222',
    }

    # 启动多个登录
    def start_requests(self):
        login_url = 'https://gongshang.mingluji.com/user'

        # 根据命令行参数选择要抓取的省
        items = [(k, v) for k, v in self.area_items.items() if k in sys.argv[1:]]
        assert 0 < len(items) <= len(self.login_accounts), '未设置抓取省份或登录账号数量不足'

        # 默认分行业抓取，如果有 -full 参数，直接按省抓取
        full = '-full' in sys.argv

        # 分别启动多个登录会话
        for area, amount in items:
            url = login_url + '?_={0}'.format(random.random())

            # 随机分配一个登录账号
            usr, pwd = random.choice(list(self.login_accounts.items()))
            del self.login_accounts[usr]

            # 启动会话
            meta = {'area': area, 'amount': amount, 'usr': usr, 'pwd': pwd, 'full': full}
            yield scrapy.Request(url, meta=meta, callback=self.auto_login)

    # 自动登录
    def auto_login(self, response):
        meta = response.meta
        form_data = {'name': meta['usr'], 'pass': meta['pwd']}
        yield scrapy.FormRequest.from_response(response, formdata=form_data, meta=response.meta, callback=self.start_area)

    # 从各省首页开始抓取
    def start_area(self, response):
        meta = response.meta
        if meta['full']:
            url = 'https://gongshang.mingluji.com/{0}/list'.format(meta['area'])
            yield scrapy.Request(url, meta=meta, callback=self.parse_index)
        else:
            for industry in self.industry_list:
                url = 'https://gongshang.mingluji.com/{0}/{1}'.format(meta['area'], industry)
                meta['industry'] = industry
                yield scrapy.Request(url, meta=meta, callback=self.parse_index)

    # 解析索引页
    def parse_index(self, response):
        link_extractor = LinkExtractor(restrict_css='#block-system-main div.view-content')
        meta = response.meta

        # 提取详情页链接
        link_count = 0
        links = link_extractor.extract_links(response)
        for link in links:
            url_hash = JobIndex.url_hash(link.url)
            if JobIndex.hash_exists(url_hash):
                continue
            link_count += 1
            yield scrapy.Request(link.url, meta=dict(meta, uuid=url_hash), callback=self.parse_item)

        # 翻页
        yield from self.next_page(response, link_count > 0)

    def next_page(self, response, has_link):
        """ 请求下一页 """
        page_num_regex = re.compile('\?page=(\d+)$')
        page_next_extractor = LinkExtractor(restrict_css='#block-system-main ul.pager > li.pager-next', allow=(page_num_regex,))
        page_count_extractor = LinkExtractor(restrict_css='#block-system-main ul.pager > li.pager-last', allow=(page_num_regex,))
        meta = response.meta

        # 总页数
        if not meta.get('page_count', None):
            pages = page_count_extractor.extract_links(response)
            if pages:
                meta['page_count'] = int(page_num_regex.search(pages[0].url).group(1))

        # 如果没有新链接，此索引页不再访问
        if not has_link:
            JobIndex.url_add(response.url, state=1)

        # 下一页链接
        page_next = page_next_extractor.extract_links(response)
        if page_next:
            page_num = int(page_num_regex.search(page_next[0].url).group(1))
            meta.update(page_num=page_num)
            url = page_next[0].url
            if not JobIndex.url_exists(url):
                yield scrapy.Request(page_next[0].url, meta=meta, callback=self.parse_index)
        else:
            # 没有下一页链接时，检查 page_count 是否达到
            num = meta.get('page_num', 0) + 1
            count = meta.get('page_count', 0)
            if num < count:
                url = parse.splitquery(response.url)[0] + '?page=' + str(num)
                meta.update(page_num=num)
                if not JobIndex.url_exists(url):
                    yield scrapy.Request(url, meta=meta, callback=self.parse_index)

    # 解析详情页
    def parse_item(self, response):
        meta = response.meta
        rows = response.css('div.content.clearfix').xpath('.//fieldset[1]//ul/li')
        info = InfoDict.from_selectors(rows, './span[1]//text()', './span[2]//text()')

        t = TelephoneItem()
        t['uuid'] = meta['uuid']
        t['source'] = self.name
        t['url'] = response.url

        t['area'] = meta.get('area')
        t['industry'] = meta.get('industry')
        t['city'] = info.get('地区')
        t['name'] = info.get('名称')
        t['tel'] = info.get('电话')
        if t['tel'] and '**' in t['tel']:
            msg = 'tel: {0}, url:{1}, meta: {2}'.format(t['tel'], response.url, json.dumps(response.meta))
            self.log(msg, logging.ERROR)

        if '获取详情' in info:
            del info['获取详情']
        t['info'] = json.dumps(info, ensure_ascii=False, sort_keys=True)
        return t
