from sanic.views import HTTPMethodView
from sanic.request import Request
from sanic.exceptions import ServerError
from .core import json_response
from database import fetch, zb123, FilterRule
from datetime import datetime, date, timedelta
import json
import re


class DayTitlesApi(HTTPMethodView):

    """ 招标信息列表 """
    async def get(self, request: Request):

        # 用户ID
        uid = request.cookies.get('uid')
        assert uid

        # 请求参数
        day = request.args.get('day') and datetime.strptime(request.args.get('day'), '%Y-%m-%d').date() or date.today()
        page = int(request.args.get('page', '1'))
        size = min(int(request.args.get('size', 20)), 50)
        use_filter = request.args.get('filter') == 'true'

        # 只提供30天内的信息，超出范围时直接返回
        if day < (date.today() - timedelta(10)) or date.today() < day:
            return json_response({'params': {'day': str(day), 'filter': use_filter}, 'items': []})

        # 非VIP用户不显示最近三天的记录
        is_vip = (await zb123.get_orders(uid)) and True or False
        if is_vip:
            query_day = day
            tip_items = []
        else:
            query_day = min(day, date.today() - timedelta(3))
            tip_days = [day - timedelta(x) for x in range(0, (day - query_day).days)]
            tip_items = [{'day': str(x), 'vip': True, 'title': '开通VIP会员可查看近三天信息'} for x in tip_days]

        # 是否应用筛选规则
        rule = await zb123.get_rule(uid) or FilterRule()
        if use_filter:
            records = await fetch.query_filtered_gathers(
                query_day, page, size, sources=rule.sources, subjects=rule.subjects, keys=rule.keys)
        else:
            records = await fetch.query_sorted_gathers(
                query_day, page, size, sources=rule.sources, subjects=rule.subjects, keys=rule.keys)

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

    async def query_sorted_gathers(self):
        pass
        # select value, (116-x)*(116-x)+(40-y)*(40-y) as distance
        # from (
        # select *, info->'$.x' as x, info->'$.y' as y from sys_config
        # where subject = 'source'
        # ) T
        # order by distance


class ContentApi(HTTPMethodView):
    async def get(self, request: Request, uuid: str):
        rec = await fetch.get_content(uuid)
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
