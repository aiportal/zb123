import peewee
from playhouse.hybrid import *
from .zb123 import db_zb123, BaseModel
from datetime import datetime
import uuid
import json


class JSONField(peewee.Field):
    """ JSON字段 """
    db_field = 'json'

    def __init__(self, sort_keys=False, **kwargs):
        super().__init__(**kwargs)
        self._sort_keys = sort_keys

    def db_value(self, value: dict):
        return value and json.dumps(value, ensure_ascii=False, sort_keys=self._sort_keys) or None

    def python_value(self, value) -> dict:
        return value and json.loads(value) or None


# 用户特征
class UserFeature(BaseModel):
    class Meta:
        db_table = 'feature'
    uid = peewee.CharField(primary_key=True, max_length=50, help_text='union_id')
    uuid = peewee.CharField(max_length=50, default=str(uuid.uuid4()).replace('-', ''), help_text='feature字段的md5')
    feature = JSONField(null=True, default='{}', help_text='用户特征词：{key1:n1, key2:n2, ...}')
    day_keys = JSONField(null=True)
    week_keys = JSONField(null=True)
    month_keys = JSONField(null=True)
    year_keys = JSONField(null=True)
    time = peewee.DateTimeField(default=datetime.now, help_text='时间戳')

    def get_keys(self, name):
        return {
            'day': self.day_keys,
            'week': self.week_keys,
            'month': self.month_keys,
            'year': self.year_keys,
        }.get(name)

    def set_keys(self, name: str, value: dict):
        if name == 'day':
            self.day_keys = value
        elif name == 'week':
            self.week_keys = value
        elif name == 'month':
            self.month_keys = value
        elif name == 'year':
            self.year_keys = value

    @staticmethod
    def get_feature(uid: str):
        try:
            return UserFeature.get(uid=uid)
        except:
            return None

peewee.create_model_tables([UserFeature], fail_silently=True)
