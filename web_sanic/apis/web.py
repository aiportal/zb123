from sanic.views import HTTPMethodView
from sanic.request import Request
from sanic.exceptions import ServerError
from .core import json_response
from database import AnnualFee, FilterRule, GatherInfo, ContentInfo
from datetime import datetime, date, timedelta
from peewee import fn
import json
import re


class DayTitlesApi(HTTPMethodView):

    """ 招标信息列表 """
    def get(self, request: Request):

        # 用户ID
        uid = request.cookies.get('uid')
        assert uid

        # 请求参数
        day = request.args.get('day') and datetime.strptime(request.args.get('day'), '%Y-%m-%d').date() or date.today()
        page = int(request.args.get('page', '1'))
        size = min(int(request.args.get('size', 20)), 50)
        use_filter = request.args.get('filter') == 'true'

        # 只提供30天内的信息，超出范围时直接返回
        if day < (date.today() - timedelta(30)) or date.today() < day:
            return json_response({'params': {'day': str(day), 'filter': use_filter}, 'items': []})

        # 非VIP用户不显示最近三天的记录
        is_vip = (AnnualFee.get_orders(uid)) and True or False
        if is_vip:
            query_day = day
            tip_items = []
        else:
            query_day = min(day, date.today() - timedelta(3))
            tip_days = [day - timedelta(x) for x in range(0, (day - query_day).days)]
            tip_items = [{'day': str(x), 'vip': True, 'title': '开通VIP会员可查看近三天信息'} for x in tip_days]

        # 是否应用筛选规则
        rule = FilterRule.get_rule(uid) or FilterRule()
        if use_filter:
            records = self.query_filtered_gathers(query_day, page, size,
                                                  sources=rule.sources, subjects=rule.subjects, keys=rule.keys)
        else:
            records = self.query_sorted_gathers(query_day, page, size,
                                                sources=rule.sources, subjects=rule.subjects, keys=rule.keys)

        # 返回查询结果
        result = {
            'params': {'day': str(day), 'page': page, 'size': size, 'filter': use_filter},    # 当前请求的参数
            'items':
                (len(records) > 0) and
                tip_items + [
                    {'uuid': x.uuid, 'day': str(x.day), 'source': x.source, 'subject': x.subject, 'title': x.title}
                    for x in records] or
                tip_items + [{'day': str(query_day), 'title': '当日无符合筛选条件的信息'}],
            'next':
                (len(records) == size) and
                {'day': str(query_day), 'page': page + 1, 'size': size, 'filter': use_filter} or
                {'day': str(query_day - timedelta(1)), 'page': 1, 'size': size, 'filter': use_filter}
        }
        return json_response(result)

    @staticmethod
    def query_filtered_gathers(day: date, page: int=1, size: int=20, sources=(), subjects=(), keys=()):
        """ 查询信息列表：只显示符合条件的记录 """
        assert size < 100

        # 按天查询
        query = GatherInfo.select().where(GatherInfo.day == day)

        # 筛选条件
        if sources:
            query = query.where(GatherInfo.source << sources)
        if subjects:
            exp = False
            for subject in subjects:
                exp = exp | GatherInfo.subject.startswith(subject)
            query = query.where(exp)
        if keys:
            exp = False
            for key in keys:
                exp = exp | GatherInfo.title.contains(key)
            query = query.where(exp)

        # 排序和分页
        query = query.order_by(+GatherInfo.source, +GatherInfo.subject, -GatherInfo.title)
        query = query.limit(size).offset((page - 1) * size)
        return [x for x in query]

    @staticmethod
    def query_sorted_gathers(day: date, page: int=1, size: int=20, sources=(), subjects=(), keys=()):
        """ 查询信息列表：按条件排序"""
        # sql example:
        # select uuid, source, subject, title,
        # 	if(source in ("qinghai", "tianjin"), 2000, 1000) as v_source,
        # 	if(subject like '预公告%', 90, 0) + if(subject like '招标公告%', 89, 0) as v_subject,
        # 	if(title like '%工程%', 100, 0) + if(title like '%电子%', 99, 0) + if(title like '%软件%', 99, 0) as v_key
        # from gather_full where day='2017-02-20'
        # order by v_source desc, source, v_subject + v_key, title desc
        assert size < 100

        # 招标来源匹配度
        col_source_match = fn.IF(True, 0, 0)
        if sources:
            col_source_match += fn.IF(GatherInfo.source << sources, 2000, 1000)

        # 招标类型匹配度
        col_subject_match = fn.IF(True, 0, 0)
        for i, subject in enumerate(subjects):
            col_subject_match += fn.IF(GatherInfo.subject.startswith(subject), (90 - i), 0)

        # 关键词匹配度
        col_key_match = fn.IF(True, 0, 0)
        for i, key in enumerate(keys):
            col_key_match += fn.IF(GatherInfo.title.contains(key), (100 - i), 0)

        # 查询
        query = GatherInfo.select().where(GatherInfo.day == day).order_by(
            -col_source_match, GatherInfo.source, -col_subject_match, -col_key_match
        )
        query = query.limit(size).offset((page - 1) * size)
        return [x for x in query]

    def query_order_gathers(self):
        pass
        # select value, (116-x)*(116-x)+(40-y)*(40-y) as distance
        # from (
        # select *, info->'$.x' as x, info->'$.y' as y from sys_config
        # where subject = 'source'
        # ) T
        # order by distance

    @staticmethod
    def get_user_center():
        """ 获取用户中心点 """

        # 个人信息中有省份的，使用省份中心点
        # Rule中有来源设置的，使用多个来源的平均中心
        # 以上都没有的，返回北京的中心点。
        # fn.find_in_set
        pass


class ContentApi(HTTPMethodView):
    def get(self, request: Request, uuid: str):
        rec = self.load_content(uuid)
        assert rec
        if not rec:
            raise ServerError('Content not found: ' + uuid)

        # contents 字体加粗
        contents = json.loads(rec.contents or '[]')
        for i, ln in enumerate(contents):
            ln = re.sub('^(.{2,30}?：)', '<b>\g<1></b>', ln)
            # 从开头到中文冒号，有2~30个字符的内容标题
            ln = re.sub('(\d{5,8}\.00|[￥\d,.]+\s*万元?|[￥\d,]+\s*元)',
                        '<span style="background-color:#FFD700;">\g<1></span>', ln)
            # 长度5~8，带.00的数字 | 以“万”字结尾的数字串 | 以“元”结尾的数字串
            contents[i] = ln
            # ￥6,790.00元    未能识别

        return json_response({
            'uuid': uuid,
            'source': rec.source,
            'day': str(rec.day),
            'url': rec.top_url or rec.real_url,
            'contents': contents,
            'attachments': json.loads(rec.attachments or '[]'),
        })

    @staticmethod
    def load_content(uuid: str):
        """ 获取详情页信息 """
        query = ContentInfo.select().where(ContentInfo.uuid == uuid)
        return query[0] if len(query) > 0 else None
