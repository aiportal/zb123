from .common import MethodView, request, json_response
from database import SuggestInfo


class SuggestApi(MethodView):
    """ 意见反馈 """
    def post(self):
        uid = request.cookies.get('uid')
        data = request.json
        SuggestInfo.create(uid=uid, content=data['content'])
        self.notice_admin(data)
        return json_response({'success': True})

    @staticmethod
    def notice_admin(data):
        """ 通知管理员 """
        from weixin import wx_zb123
        msg = '来自 {0} 的消息：{1}'.format(data.get('tel'), data['content'])
        try:
            for openid in wx_zb123.admin:
                wx_zb123.custom_send_text(openid, msg)
        except Exception as ex:
            pass
