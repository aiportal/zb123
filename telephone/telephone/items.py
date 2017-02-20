# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TelephoneItem(scrapy.Item):
    # 企业名称 :
    # 山东百朋机械设备有限公司
    # 地址 :
    # 山东省临沂经济技术开发区临沂北方国际家居建材城A区3幢013a号3层
    # 法人 :
    # 张淑敏
    # 电话 :
    # 18615391573
    # 注册日期 :
    # 2015-02-04
    # 企业类型 :
    # 有限责任公司(自然人独资)
    # 注册资金 :
    # 300
    # 地区 :
    # 临沂
    uuid = scrapy.Field()
    source = scrapy.Field()
    area = scrapy.Field()
    city = scrapy.Field()
    industry = scrapy.Field()
    name = scrapy.Field()
    tel = scrapy.Field()
    url = scrapy.Field()
    info = scrapy.Field()
