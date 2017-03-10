import peewee
from peewee_async import MySQLDatabase, PooledMySQLDatabase, Manager
import uuid
from datetime import datetime


db_tel = PooledMySQLDatabase(host='127.0.0.1', user='root', password='lq1990', port=3306, database='telephone', charset='utf8')


class IndexInfo(peewee.Model):
    class Meta:
        database = db_tel
        db_table = 'mingluji_index'
    id = peewee.PrimaryKeyField()
    index = peewee.CharField(max_length=255, help_text='索引页网址')
    name = peewee.CharField(max_length=255, help_text='公司名称')
    url = peewee.CharField(max_length=255, help_text='详情页网址')
    time = peewee.DateTimeField(default=datetime.now)


class IndexUrls(peewee.Model):
    class Meta:
        database = db_tel
        db_table = 'mingluji_index_urls'
    uuid = peewee.FixedCharField(primary_key=True, max_length=32, help_text='URL的HASH值')
    state = peewee.IntegerField(default=0, help_text='Url的状态或分类')

    @staticmethod
    def url_hash(url):
        return str(uuid.uuid3(uuid.NAMESPACE_URL, url)).replace('-', '')

    @staticmethod
    async def url_exists(url):
        url_hash = IndexUrls.url_hash(url)
        q = IndexUrls.select().where(IndexUrls.uuid == url_hash).limit(1)
        return len(await tel.execute(q))

    @staticmethod
    async def url_add(url, state=0):
        url_hash = IndexUrls.url_hash(url)
        q = IndexUrls.insert(uuid=url_hash, state=state)
        return await tel.execute(q)


IndexInfo.create_table(True)
IndexUrls.create_table(True)
# db_tel.close()

# Create async models manager:
tel = Manager(db_tel)

# No need for sync anymore!
db_tel.set_allow_sync(False)


# async def handler():
#     await objects.create(TestModel, text="Not bad. Watch this, I'm async!")
#     all_objects = await objects.execute(TestModel.select())
#     for obj in all_objects:
#         print(obj.text)
#
# loop = asyncio.get_event_loop()
# loop.run_until_complete(handler())
# loop.close()
#
# # Clean up, can do it sync again:
# with objects.allow_sync():
#     TestModel.drop_table(True)
