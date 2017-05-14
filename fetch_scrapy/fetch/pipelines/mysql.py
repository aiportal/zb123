from fetch.items import GatherItem
from database import GatherInfo, ContentInfo, SysConfig
import json
from database import JobIndex
import peewee
import logging


class MysqlPipeline(object):
    def open_spider(self, spider):
        SysConfig.set_item(subject='source', key=spider.name, value=spider.alias)

    def process_item(self, item, spider):
        if not isinstance(item, GatherItem):
            return item

        obj = dict(item)

        try:
            # GatherInfo
            g = GatherInfo(**obj)
            g.extends = json.dumps(item.get('extends', {}), ensure_ascii=False)
            g.save(force_insert=True)

            # ContentInfo
            c = ContentInfo(**obj)
            c.html = None
            c.contents = json.dumps(item.get('contents', []), ensure_ascii=False)
            c.digest = item.get('digest') and json.dumps(item['digest'], ensure_ascii=False)
            c.attachments = item.get('attachments') and json.dumps(item['attachments'], ensure_ascii=False)
            c.save(force_insert=True)
        except peewee.IntegrityError as e:
            msg = 'uuid: {0}, url: {1}'.format(item['uuid'], item['url'])
            spider.log(msg, logging.ERROR)
            spider.log(str(e), logging.ERROR)

        # JobIndex
        assert JobIndex.url_hash(item['url']) == item['uuid']
        JobIndex.url_insert(url=item['url'])

        return item



