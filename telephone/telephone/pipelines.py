# -*- coding: utf-8 -*-
from database import CompanyInfo, JobIndex

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class TelephonePipeline(object):
    @staticmethod
    def process_item(item, spider):
        obj = dict(item)

        CompanyInfo(**obj).save()
        JobIndex.hash_add(obj['uuid'])

        return item
