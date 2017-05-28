import peewee
import json


host = '127.0.0.1'
db_link = peewee.MySQLDatabase(host=host, database='link', user='root', password='Bayesian@2018', charset='utf8')


class LinkModel(peewee.Model):
    class Meta:
        database = db_link


class JSONObjectField(peewee.TextField):
    """ JSON对象 """
    def __init__(self, sort_keys: bool=False, indent: int=None, *args, **kwargs):
        self.sort_keys = sort_keys
        self.indent = indent
        super().__init__(*args, **kwargs)

    def db_value(self, value: dict):
        return value and json.dumps(value, ensure_ascii=False, sort_keys=self.sort_keys, indent=self.indent) or None

    def python_value(self, value) -> dict:
        return json.loads(value or '{}') or None


class JSONArrayField(peewee.TextField):
    """ JSON 数组 """
    def db_value(self, value: list):
        return value and json.dumps(value, ensure_ascii=False) or None

    def python_value(self, value) -> list:
        return json.loads(value or '[]') or None
