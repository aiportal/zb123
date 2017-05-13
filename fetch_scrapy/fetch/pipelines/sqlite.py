from database.local import JobIndex, GatherTemp, ContentTemp, EventLog
import json
import peewee


class SQLitePipeline(object):
    """
    Create a new SQLite db file for each startup.
    Add items to this independent db.
    Commit valid items to mysql in close_spider func.
    """
    def open_spider(self, spider):
        pass

    def process_item(self, item, spider):
        obj = dict(item)
        assert obj['uuid'] == JobIndex.url_hash(obj['url'])
        try:
            g = GatherTemp(**obj)
            g.save(force_insert=True)

            c = ContentTemp(**obj)
            c.html = None
            c.save(force_insert=True)
        except peewee.IntegrityError:
            EventLog.log_exception(spider.name, level='IntegrityError', url=obj['url'], info={'uuid': obj['uuid']})
        except Exception as ex:
            EventLog.log_exception(spider.name, level='PIPELINE', url=obj['url'], exception=ex)
        finally:
            JobIndex.url_insert(obj['url'])

        return item

    def close_spider(self, spider):
        pass

