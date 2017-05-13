from .common import MethodView, request, json_response
from database import SysConfig, UserInfo, FilterRule, AnnualFee, SuggestInfo, UserFeature
from datetime import datetime, date, timedelta
import json, hashlib


class UserInfoApi(MethodView):
    """ 界面初始化信息 """
    def __init__(self):
        super().__init__()

        # 信息来源列表
        self.sources = SysConfig.get_items('source')
        # 信息类型列表
        self.subjects = SysConfig.get_items('subject')
        # 关键词建议列表
        self.suggests = SysConfig.get_items('suggest')

    def get(self):
        """ 获取界面初始化信息 """

        # 用户ID
        uid = request.cookies.get('uid')
        assert uid

        # 筛选规则
        rule = self.load_user_rule(uid)

        # 信息来源
        sources = [{'value': x.key, 'text': x.value, 'select': x.key in rule.sources} for x in self.sources]

        # 信息类型
        subjects = [{'text': x.key, 'select': x.key in rule.subjects} for x in self.subjects]

        # 关键词
        keys = [{'text': x, 'select': x in rule.keys} for x in rule.suggests]

        # 会员信息
        orders = AnnualFee.get_orders(uid)    # 付费信息列表
        if not orders:
            user = {'vip': False, 'pays': None, 'end': None}
        else:
            user = {'vip': True, 'end': str(orders[0].end),
                    'pays': [{'day': str(x.day), 'fee': x.amount, 'start': str(x.start), 'end': str(x.end),
                              'order': x.order_no} for x in orders]}

        # 日期列表（最近30天）
        days = [str(date.today() + timedelta(x)) for x in reversed(range(-30, 1))]

        # 缓存特征值
        cache = self.calculate_cache_key(uid, rule)

        # 返回信息
        return json_response({
            'rule': {
                'sources': sources,
                'subjects': subjects,
                'keys': keys,
            },
            'user': user,
            'days': days,
            'cache': cache,
        })

    def load_user_rule(self, uid: str) -> FilterRule:
        """ 获取用户的筛选规则 """
        rule = FilterRule.get_rule(uid)
        if rule:
            return rule

        # 如果没有设置，自动生成默认规则
        user = UserInfo.get_user(uid)
        province = user.info.get('province', '').lower()
        rule = {
            'sources': [x.key for x in self.sources if x.key == province],
            'subjects': [x.key for x in self.subjects if x.value != '0'],
            'keys': [],
            'suggests': [x.key for x in self.suggests if '*' in x.value or province in x.value]
        }
        self.save_user_rule(uid, rule)
        return FilterRule.get_rule(uid)

    @staticmethod
    def calculate_cache_key(uid: str, rule: FilterRule):
        """ 计算通用的缓存特征值 """
        user = UserInfo.get_user(uid)
        vip = AnnualFee.is_vip(uid)
        feature = UserFeature.get_feature(uid)
        feature = feature and feature.uuid or ''
        info = {'province': user.info.get('province'), 'vip': vip, 'feature': feature,
                'sources': rule.sources, 'subjects': rule.subjects, 'keys': rule.keys}
        bs = json.dumps(info, ensure_ascii=False, sort_keys=True).encode()
        return hashlib.md5(bs).hexdigest().lower()

    def post(self):
        """ 保存筛选规则 """
        uid = request.cookies.get('uid')
        assert uid

        # 保存筛选规则
        cache = self.save_user_rule(uid, request.json)

        return json_response({'success': True, 'cache': cache})

    @staticmethod
    def save_user_rule(uid: str, rule: dict):
        """ 保存用户的筛选规则 """
        assert 'sources' in rule and 'subjects' in rule and 'keys' in rule and 'suggests' in rule

        # 保存新记录的同时，保留旧记录，用MD5避免重复保存相同的内容
        info = json.dumps(rule, ensure_ascii=False, sort_keys=True)
        md5 = hashlib.md5(info.encode()).hexdigest().upper()

        FilterRule.update(active=False).where(FilterRule.uid == uid).execute()
        rec, is_new = FilterRule.get_or_create(uid=uid, uuid=md5, defaults={'filter': rule, 'active': True})
        if not is_new:
            rec.active = True,
            rec.time = datetime.now()
            rec.save()

        return UserInfoApi.calculate_cache_key(uid, rec)

