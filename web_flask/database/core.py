import peewee
import json


class JSONField(peewee.CharField):
    """ JSON字段 """
    def db_value(self, value: dict):
        return value and json.dumps(value, ensure_ascii=False, sort_keys=True) or None

    def python_value(self, value) -> dict:
        return json.loads(value or '{}') or None
