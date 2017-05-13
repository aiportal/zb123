"""
Store items to local SQLite db.
"""

import peewee
import uuid
from datetime import datetime, date, timedelta


db_jobs = peewee.SqliteDatabase('jobs.db')


class JobsModel(peewee.Model):
    class Meta:
        database = db_jobs


# 网址索引表
class JobIndex(JobsModel):
    class Meta:
        db_table = 'url_index'
    uuid = peewee.UUIDField(primary_key=True, help_text='hash code for url.')
    day = peewee.DateField(null=False, default=date.today, help_text='Item insert date.')

    @staticmethod
    def url_hash(url):
        return str(uuid.uuid3(uuid.NAMESPACE_URL, url)).replace('-', '')

    @staticmethod
    def url_exists(url):
        url_hash = JobIndex.url_hash(url)
        return JobIndex.select().where(JobIndex.uuid == url_hash).exists()

    @staticmethod
    def url_insert(url):
        url_hash = JobIndex.url_hash(url)
        JobIndex.get_or_create(uuid=url_hash)


db_jobs.create_tables([JobIndex], True)
