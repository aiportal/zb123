from flask import request
from flask.views import MethodView
from web_funcs import json_response, ServerError
from database import SysConfig, UserInfo, AnnualFee, FilterRule, BidGather as GatherInfo, UserFeature
from datetime import datetime, date, timedelta
from peewee import fn, Func
import json
from typing import List


class RangeTitlesApi(MethodView):
    """ 招标信息列表 """

    sources = SysConfig.get_items('source')
    columns = (GatherInfo.uuid, GatherInfo.day, GatherInfo.source, GatherInfo.subject, GatherInfo.title)

    def get(self):
        # 请求参数
        day, page, size, do_filter, key = [request.args.get(x) for x in ('day', 'page', 'size', 'filter', 'key')]
        day = day and datetime.strptime(day, '%Y-%m-%d').date() or (date.today() - timedelta(days=6))
        page = int(page or 1)
        size = min(int(size or 20), 50)
        do_filter = (do_filter == 'true')           # 是否应用筛选规则
        is_first = not request.args.get('day')      # 是否首次请求

        # 用户ID
        uid = request.cookies.get('uid')
        assert uid
        is_vip = AnnualFee.is_vip(uid)

        # 限制查询天数
        days_limit = is_vip and 90 or 6
        day = min(day, date.today() - timedelta(days_limit))

        # 非VIP用户不显示最近三天
        if is_first and not is_vip:
            tip_days = [date.today() - timedelta(x) for x in range(0, 3)]
            tip_counts = self.query_days_count(tip_days, (do_filter and uid or None), key)
            tip_items = [{'day': str(x), 'vip': True, 'title': '开通VIP会员可查看近三天信息',
                          'count': tip_counts.get(str(x), 0)} for x in tip_days]
            # 首次请求时直接返回
            result = {
                'items': tip_items,
                'params': {'day': str(day), 'page': page, 'size': size, 'filter': do_filter, 'key': key},
                'next': {'day': str(day), 'page': 1, 'size': size, 'filter': do_filter, 'key': key}
            }
            return json_response(result)

        max_day = (not is_vip) and date.today() - timedelta(3) or None

        # 是否应用筛选规则
        if do_filter:
            records = self.query_filtered_gathers(uid, day, max_day, page, size)
        elif key:
            records = self.query_search_gathers(uid, key, day, max_day, page, size)
            self.add_rule_key(uid, key)
        else:
            records = self.query_global_gathers(uid, day, max_day, page, size)
        items = [{'uuid': x.uuid, 'day': str(x.day), 'source': x.source, 'subject': x.subject, 'title': x.title}
                 for x in records]

        # 当前请求参数
        cur_params = {'day': str(day), 'page': page, 'size': size, 'filter': do_filter, 'key': key}

        # 下一页请求参数
        if len(records) == size:
            next_params = {'day': str(day), 'page': page + 1, 'size': size, 'filter': do_filter, 'key': key}
        else:
            next_params = None

        # 返回查询结果
        return json_response({
            'items': items,
            'params': cur_params,
            'next': next_params
        })

    @staticmethod
    def query_days_count(days: List[date], uid: str=None, key=None):
        """ 查询每天的信息总数
        全国信息: uid==None, key==None
        关键词搜索：uid==None, key="..."
        筛选定制：uid="...", key=None
        """
        if len(days) < 1:
            return {}

        query = GatherInfo.select(GatherInfo.day, fn.COUNT(GatherInfo.uuid).alias('count'))\
            .where(GatherInfo.day << days)

        if key:
            query = query.where(GatherInfo.title.contains(key))
        elif uid:
            rule = FilterRule.get_rule(uid) or FilterRule()
            if rule.sources:
                query = query.where(GatherInfo.source << rule.sources)
            if rule.subjects:
                exp = False
                for subject in rule.subjects:
                    exp = exp | GatherInfo.subject.startswith(subject)
                query = query.where(exp)
            if rule.keys:
                exp = False
                for key in rule.keys:
                    exp = exp | GatherInfo.title.contains(key)
                query = query.where(exp)

        query = query.group_by(GatherInfo.day)
        return {str(x.day): x.count for x in query}

    def query_filtered_gathers(self, uid: str, min_day: date, max_day: date=None, page: int=1, size: int=20):
        """ 查询招标信息，按筛选条件进行筛选 """
        assert size < 100

        rule = FilterRule.get_rule(uid) or FilterRule()
        feature = UserFeature.get_feature(uid) or UserFeature()
        query = GatherInfo.select(*self.columns)

        # 日期区间
        if max_day:
            query = query.where(GatherInfo.day.between(min_day, max_day))
        else:
            query = query.where(GatherInfo.day > min_day)

        # 条件筛选
        if rule.sources:
            query = query.where(GatherInfo.source << rule.sources)
        if rule.subjects:
            exp = False
            for subject in rule.subjects:
                exp = exp | GatherInfo.subject.startswith(subject)
            query = query.where(exp)
        if rule.keys:
            exp = False
            for key in rule.keys:
                exp = exp | GatherInfo.title.contains(key)
            query = query.where(exp)

        # 关键词匹配度
        col_key_match = fn.IF(True, 0, 0)
        for i, key in enumerate(rule.keys):
            col_key_match += fn.IF(GatherInfo.title.contains(key), 0, 100 - i)

        # 用户特征匹配度
        col_feature_match = fn.IF(True, 0, 0)
        for k, v in feature.feature.items():
            col_feature_match += fn.IF(GatherInfo.title.contains(k), int(v), 0)

        # 招标来源顺序
        source_ordered = ','.join(self.get_sources_by_distance(uid))
        distance = Func('find_in_set', GatherInfo.source, source_ordered)

        query = query.order_by(col_key_match, -col_feature_match, distance,
                               -GatherInfo.day, GatherInfo.subject, GatherInfo.title)
        query = query.paginate(page, size)
        return [x for x in query]

    def query_search_gathers(self, uid: str, key: str, min_day: date, max_day: date=None, page: int=1, size: int=20):
        """ 搜索招标信息 """
        assert size < 100

        rule = FilterRule.get_rule(uid) or FilterRule()
        feature = UserFeature.get_feature(uid) or UserFeature()
        query = GatherInfo.select(*self.columns)

        # 日期区间
        if max_day:
            query = query.where(GatherInfo.day.between(min_day, max_day))
        else:
            query = query.where(GatherInfo.day > min_day)

        # 全国信息的查询，只提供预公告和招标公告
        if AnnualFee.is_vip(uid):
            query = query.where(GatherInfo.subject.startswith('预公告') | GatherInfo.subject.startswith('招标公告'))
        else:
            query = query.where(GatherInfo.subject.startswith('招标公告'))

        # 关键词
        query = query.where(GatherInfo.title.contains(key))

        # 招标来源匹配度
        source_ordered = ','.join(self.get_sources_by_distance(uid))
        distance = Func('find_in_set', GatherInfo.source, source_ordered)
        order_col_source = fn.IF(GatherInfo.source << rule.sources, distance, 10000 + distance)

        # 招标类型匹配度
        col_subject_match = fn.IF(True, 0, 0)
        for i, subject in enumerate(rule.subjects):
            col_subject_match += fn.IF(GatherInfo.subject.startswith(subject), 0, 1000 * (i+1))

        # 关键词匹配度
        col_key_match = fn.IF(True, 0, 0)
        for i, k in enumerate(rule.keys):
            col_key_match += fn.IF(GatherInfo.title.contains(k), 0, 100 - i)

        # 用户特征匹配度
        col_feature_match = fn.IF(True, 0, 0)
        for k, v in feature.feature.items():
            col_feature_match += fn.IF(GatherInfo.title.contains(k), int(v), 0)

        query = query.order_by(col_key_match, -col_feature_match, -GatherInfo.day, col_subject_match, order_col_source)
        query = query.paginate(page, size)
        return [x for x in query]

    def query_global_gathers(self, uid: str, min_day: date, max_day: date=None, page: int=1, size: int=20):
        """ 全国招标信息 """
        assert size < 100

        # select uuid, source, subject, title,
        # 	if(source in ("qinghai", "tianjin"), 2000, 1000) as v_source,
        # 	if(subject like '预公告%', 90, 0) + if(subject like '招标公告%', 89, 0) as v_subject,
        # 	if(title like '%工程%', 100, 0) + if(title like '%电子%', 99, 0) + if(title like '%软件%', 99, 0) as v_key
        # from gather_full where day='2017-02-20'
        # order by v_source desc, source, v_subject + v_key, title desc

        rule = FilterRule.get_rule(uid) or FilterRule()
        feature = UserFeature.get_feature(uid) or UserFeature()
        query = GatherInfo.select(*self.columns)

        # 日期区间
        if max_day:
            query = query.where(GatherInfo.day.between(min_day, max_day))
        else:
            query = query.where(GatherInfo.day > min_day)

        # 全国信息的查询，只提供预公告和招标公告
        if AnnualFee.is_vip(uid):
            query = query.where(GatherInfo.subject.startswith('预公告') | GatherInfo.subject.startswith('招标公告'))
        else:
            query = query.where(GatherInfo.subject.startswith('招标公告'))

        # 招标来源匹配度
        source_ordered = ','.join(self.get_sources_by_distance(uid))
        distance = Func('find_in_set', GatherInfo.source, source_ordered)
        order_col_source = fn.IF(GatherInfo.source << rule.sources, distance, 10000 + distance)

        # 招标类型匹配度
        col_subject_match = fn.IF(True, 0, 0)
        for i, subject in enumerate(rule.subjects):
            col_subject_match += fn.IF(GatherInfo.subject.startswith(subject), 0, 1000 * (i+1))

        # 关键词匹配度
        col_key_match = fn.IF(True, 0, 0)
        for i, key in enumerate(rule.keys):
            col_key_match += fn.IF(GatherInfo.title.contains(key), 0, 100 - i)

        # 用户特征匹配度
        col_feature_match = fn.IF(True, 0, 0)
        for k, v in feature.feature.items():
            col_feature_match += fn.IF(GatherInfo.title.contains(k), int(v), 0)

        # 查询
        query = query.order_by(col_key_match, -col_feature_match, -GatherInfo.day, col_subject_match, order_col_source)
        query = query.paginate(page, size)
        return [x for x in query]

    def get_sources_by_distance(self, uid: str):
        """ 根据用户所在省份/选中省份，获取按距离排序的其他省份列表 """

        # select `key`, `value`, round(power(116 - info->'$.x', 2) + power(40 - info->'$.y', 2)) as distance
        # from sys_config
        # where subject = 'source'
        # order by distance

        center = self.get_user_center(uid)
        x = Func('json_extract', SysConfig.info, '$.x')
        y = Func('json_extract', SysConfig.info, '$.y')
        distance = fn.Power(center['x'] - x, 2) + fn.Power(center['y'] - y, 2)
        query = SysConfig.select().where(SysConfig.subject == 'source').order_by(fn.Round(distance))
        return [x.key for x in query]

    def get_user_center(self, uid: str):
        """ 获取用户中心点 """

        # 查询个人信息中的省份名称，获取中心位置
        user = UserInfo.get_user(uid)   # type: UserInfo
        province = user.info.get('province', '').lower()
        matches = [x for x in self.sources if x.key == province]
        if matches:
            return json.loads(matches[0].info)

        # 查询rule设置中的省份名称，计算中心位置
        rule = FilterRule.get_rule(uid)     # type: FilterRue
        if rule and rule.sources:
            coords = [json.loads(x.info) for x in self.sources if x.key in rule.sources]
            if coords:
                return {
                    'x': sum([c['x'] for c in coords]) / len(coords),
                    'y': sum([c['y'] for c in coords]) / len(coords)
                }

        # 默认以北京为中心点
        beijing = [x for x in self.sources if x.key == 'beijing']
        default = next(iter(beijing + self.sources))
        return json.loads(default.info)

    @staticmethod
    def add_rule_key(uid: str, key: str):
        try:
            rule = FilterRule.get_rule(uid) or FilterRule()
            if key not in rule.suggests:
                rule.suggests.insert(0, key)
                rule.save()
        except Exception as ex:
            print(ex)
