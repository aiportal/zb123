from flask.views import MethodView, request
from web_funcs import json_response, ServerError
from database import ContentInfo
import json
import re
from urllib.parse import urljoin
from typing import List


class ContentApi(MethodView):
    """ 获取招标信息详情 """
    columns = (ContentInfo.uuid, ContentInfo.contents, ContentInfo.top_url, ContentInfo.real_url)

    def get(self, uuid: str):
        query = ContentInfo.select(*self.columns).where(ContentInfo.uuid == uuid)
        if len(query) < 1:
            return json_response({
                'uuid': uuid,
                'contents': [],
            })

        assert len(query) > 0
        rec = query[0]

        contents = json.loads(rec.contents or '[]')
        if isinstance(contents, str):
            contents = [contents]
        contents = self.origin_links(rec.real_url, contents)
        contents = self.highlight(contents)

        return json_response({
            'uuid': uuid,
            # 'day': str(rec.day),
            'url': rec.top_url or rec.real_url,
            # 'title': rec.title,
            'contents': contents,
        })

    @staticmethod
    def highlight(contents: List[str]):
        """ 高亮显示重点信息 """
        for i, ln in enumerate(contents):

            # 从行首到中文冒号，有2~30个字符的内容标题
            ln = re.sub('^(.{2,30}?：)', '<b>\g<1></b>', ln)

            # 长度5~8，带.00的数字 | 以“万”字结尾的数字串 | 以“元”结尾的数字串
            ln = re.sub('(\d{5,8}\.00|[￥\d,.]+\s*万元?|[￥\d,]+\s*元)',
                        '<span style="background-color:#FFD700;">\g<1></span>', ln)
            # ￥6,790.00元    未能识别

            contents[i] = ln
        return contents

    @staticmethod
    def origin_links(url: str, contents: List[str]):
        """ 完善链接网址 """
        root = urljoin(url, '/')
        parent = urljoin(url, '.')

        for i, ln in enumerate(contents):

            # 绝对路径网址
            ln = re.sub(r'( href=")/([^"]+")', '\g<1>{0}\g<2>'.format(root), ln)
            # 相对路径网址
            ln = re.sub('( href=")(?!http://|https://|/)([^"]+")', '\g<1>{0}\g<2>'.format(parent), ln)

            # iframe 绝对路径
            ln = re.sub(r'( src=")/([^"]+")', '\g<1>{0}\g<2>'.format(root), ln)
            # iframe 相对路径
            ln = re.sub('( src=")(?!http://|https://|/)([^"]+")', '\g<1>{0}\g<2>'.format(parent), ln)

            contents[i] = ln

        return contents
