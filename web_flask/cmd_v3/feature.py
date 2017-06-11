from flask.views import MethodView
import peewee
from peewee import fn
from database import AccessLog, GatherInfo, UserFeature, SysConfig
from web_funcs import *
import jieba
from datetime import datetime, date, timedelta
from typing import Iterable, Dict
import json
import hashlib


"""
    遍历AccessLog中包含content的数据
    根据网址中的uuid提取title信息（GatherInfo）
    用结巴分词分解title信息
    分别以日、周、月为单位，按用户uid统计各个词汇的出现频率(权重)
    {day:{k1:2, k2:3, k3:1}, week:{k1:5, k2:3, k3:1}, month:{k1:3, k2:5, k3:4}}

    根据关键词在day,week,month,year中出现的频率，使用不同的权重乘数共同计算出综合权重
    day_n * 365 + week_n * 52 + month_n * 12 + year_n * 1
    权重乘数默认为360、52、12、1，但可以调整
"""


class UserFeatureApi(MethodView):
    def __init__(self):
        self.days = {'day': 1, 'week': 7, 'month': 30, 'year': 365}

        weights = SysConfig.get_items('weight')
        self.weights = {x.key: int(x.value) for x in weights} if len(weights) > 0 \
            else {'day': 365, 'week': 52, 'month': 12, 'year': 1}

        ignores = SysConfig.get_items('ignore')
        self.ignores = {x.key: x.value == '1' for x in ignores}

        self.feature_limit = int(SysConfig.get_item('limit', 'feature').value or 15)
        self.keys_limit = int(SysConfig.get_item('limit', 'keys').value or 200)

    def get(self, period: str, uid: str=None):
        """ 统计用户特征信息 """
        if period not in self.weights:
            raise ServerError()

        days = self.days.get(period, 0)
        users = self.stat_title_keys(timedelta(days=days), uid=uid, limit=self.keys_limit)
        for uid, words in users.items():
            if not words:
                continue
            f, _ = UserFeature.get_or_create(uid=uid, defaults={})      # type: UserFeature
            f.set_keys(period, words)
            f.feature = self.compute_user_feature(f, limit=self.feature_limit)
            feature_js = json.dumps(f.feature, ensure_ascii=False, sort_keys=True)
            f.uuid = hashlib.md5(feature_js.encode()).hexdigest().upper()
            f.time = datetime.now()
            f.save()

        return json_response({
            'success': True,
            'count': len(users),
        })

    def compute_user_feature(self, feature: UserFeature, limit: int=50) -> dict:
        """ 计算用户特征值 """
        words = {}
        for col, w in self.weights.items():
            for k, v in (feature.get_keys(col) or {}).items():
                words[k] = words.get(k, 0) + v * w
        keys = [(x, words[x]) for x in sorted(words, key=words.get, reverse=True)][:limit]
        return dict(keys)

    def stat_title_keys(self, period: timedelta, uid: str=None, limit: int=200)\
            -> Dict[str, Dict[str, int]]:
        """ 统计用户点击的标题关键词 """

        # select uid, mid(url, instr(url, '/content/') + 9) as uuid, date(time) as day from access_log
        # where url like '%/content/%' and uid <> ''
        # order by day desc, uuid
        # limit 300

        min_time = datetime.now() - period
        col_uuid = fn.mid(AccessLog.url, fn.instr(AccessLog.url, '/content/') + 9).alias('uuid')
        query_log = AccessLog.select(AccessLog.uid, col_uuid)\
            .where(AccessLog.time > min_time)\
            .where(AccessLog.url.contains('/content/'))     # type: peewee.SelectQuery

        if uid:
            query_log = query_log.where(AccessLog.uid == uid)
        else:
            query_log = query_log.where(AccessLog.uid != '')\

        users = {}      # type: Dict[str, Dict[str, int]]
        for records in self.paginate_records(query_log, 100):
            uuid_list = {x.uuid for x in records if x.uid}
            if not uuid_list:
                break

            query_title = GatherInfo.select(GatherInfo.uuid, GatherInfo.title)\
                .where(GatherInfo.uuid << uuid_list)
            titles = {x.uuid: x.title for x in query_title}

            for r in records:
                title = titles.get(r.uuid)
                if not title:
                    continue

                keys = users.get(r.uid, {})
                for w in jieba.lcut(title):
                    if len([c for c in w if ord(c) > 128]) < 2:     # 至少两个汉字
                        continue
                    if self.ignores.get(w):
                        continue
                    keys[w] = keys.get(w, 0) + 1
                users[r.uid] = keys

        # 限制关键词数量
        for uid in users:
            words = users[uid]
            keys = [(x, words[x]) for x in sorted(words, key=words.get, reverse=True)][:limit]
            users[uid] = dict(keys)
        return users

    @staticmethod
    def paginate_records(query, rows, count=100) -> Iterable[list]:
        """ 分页提取记录集 """
        for page in range(1, count):
            rs = [r for r in query.paginate(page, rows)]
            yield rs
            if len(rs) < rows:
                break

