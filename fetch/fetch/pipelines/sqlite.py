from database.local import JobIndex, CacheItem, EventLog
from database.remote import db_fetch, GatherInfo, ContentInfo
from datetime import datetime, date, timedelta
import json
import peewee
import zlib


class SQLitePipeline(object):
    """
    Create a new SQLite db file for each startup.
    Add items to this independent db.
    Commit valid items to mysql in close_spider func.
    """
    def open_spider(self, spider):
        pass

    def process_item(self, item, spider):
        """
        Store items to SQLite db.
        """
        obj = dict(item)
        assert obj['uuid'] == JobIndex.url_hash(obj['url'])
        try:
            obj['html'] = None
            data = json.dumps(obj, ensure_ascii=False)

            o = CacheItem(**obj)
            o.source = spider.name
            o.data = zlib.compress(data.encode())

            o.save(force_insert=True)

        except peewee.IntegrityError as ex:
            EventLog.log_exception(spider.name, level='IntegrityError', url=obj['url'], addition={'uuid': obj['uuid']})
        except Exception as ex:
            EventLog.log_exception(spider.name, level='PIPELINE', url=obj['url'], exception=ex)
        finally:
            JobIndex.url_insert(obj['url'])

        return item

    def close_spider(self, spider):
        """
        Transfer items from SQLite to mysql
        """
        pass
        # top_source = spider.name.split('/')[0]

        # query = CacheItem.select()\
        #     .where(CacheItem.source == spider.name)\
        #     .where(CacheItem.day == date.today())
        #
        # for page in range(1, 10):
        #     page_query = query.paginate(page, 100)
        #     with db_fetch.atomic() as txn:
        #         for rec in page_query:
        #             try:
        #                 data = zlib.decompress(rec.data).decode()
        #                 obj = json.loads(data)
        #             except Exception as ex:
        #                 pass

        # delete completed items.
        # CacheItem.delete().where(CacheItem.source == spider.name).where(CacheItem.completed).execute()

