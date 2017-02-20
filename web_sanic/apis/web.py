from sanic.views import HTTPMethodView
from sanic.request import Request
from .core import json_response
from database import GatherInfo, ContentInfo, FilterRule, AnnualFee
from datetime import datetime, date, timedelta
import json
import re


class DayTitlesApi(HTTPMethodView):
    """ 招标信息列表 """
    def get(self, request: Request):

        # 用户ID
        uid = request.cookies.get('uid')
        assert uid

        # 请求参数
        day = datetime.strptime(request.args.get('day', str(date.today())), '%Y-%m-%d').date()
        page = int(request.get('page', '1'))
        size = min(int(request.get('size', 20)), 50)
        use_rule = request.get('rule') == 'true'

        # 只提供最近30天的信息
        min_day = date.today() - timedelta(30)
        if day < min_day:
            day = date.today()

        # 非VIP用户不显示最近三天的记录
        pre_items = []
        if not AnnualFee.is_vip(uid):
            if (date.today() - day).days < 3:
                day = date.today() - timedelta(3)
                pre_items = [{'day': str(date.today()-timedelta(x)), 'vip': True, 'title': '开通VIP服务可以查看'}
                             for x in range(0, 3)]

        columns = [GatherInfo.uuid, GatherInfo.day, GatherInfo.source, GatherInfo.subject, GatherInfo.title]
        query = GatherInfo.select(*columns)\
            .where(GatherInfo.day == day)\
            .order_by(-GatherInfo.day, +GatherInfo.source, +GatherInfo.subject, -GatherInfo.title)

        if use_rule:    # 使用自定义规则进行筛选
            rule = FilterRule.get_rule(uid) or FilterRule()
            # 来源筛选
            if rule.sources:
                query = query.where(GatherInfo.source << rule.sources)
            # 分类搜索
            if rule.subjects:
                exp = None
                for subject in rule.subjects:
                    exp = exp | GatherInfo.subject.startswith(subject)
                query = query.where(exp)
            # 关键词搜索
            if rule.keys:
                exp = None
                for key in rule.keys:
                    exp = exp | GatherInfo.title.contains(key)
                query = query.where(exp)

        records = [x for x in query.paginate(page, size)]
        result = {
            # 当前请求的参数
            'params': {'day': request.args.get('day'), 'page': page, 'size': size},
            # 查询结果
            'items': pre_items + [
                {'uuid': x.uuid, 'day': str(x.day), 'source': x.source, 'subject': x.subject, 'title': x.title}
                for x in records
            ]
        }

        # 下次请求的参数（下一页或前一天）
        if len(records) == size:
            result['next'] = {'day': str(day), 'page': page + 1, 'size': size}
        elif min_day < day:
            result['next'] = {'day': str(day - timedelta(1)), 'page': 1, 'size': size}

        return json_response(result)


class ContentApi(HTTPMethodView):
    def get(self, request, uuid):
        rec = (ContentInfo.select().where(ContentInfo.uuid == uuid)).get()

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

        # uid = request.cookies.get('uid')
        # self.record_access(request, uuid)
        return json_response({
            'uuid': uuid,
            'source': rec.source,
            'day': str(rec.day),
            'url': rec.top_url or rec.real_url,
            'contents': contents,
            'attachments': json.loads(rec.attachments or '[]'),
        })
