from .common import MethodView, request, json_response, ServerError
from database import SysConfig, UserInfo, AnnualFee, FilterRule, GatherInfo, ContentInfo, UserFeature
from datetime import datetime, date, timedelta
import json
import re


class ContentInfoApi(MethodView):
    def get(self, uuid: str):
        rec = self.load_content(uuid)
        assert rec
        if not rec:
            raise ServerError('Content not found: ' + uuid)

        # contents 字体加粗
        contents = json.loads(rec.contents or '[]')
        if isinstance(contents, str):
            contents = [contents]
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
