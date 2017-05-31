from .app import WxAppCore


class WxCustomManager(WxAppCore):
    """ 微信客服接口 """
    url_custom_send = 'https://api.weixin.qq.com/cgi-bin/message/custom/send'

    def custom_send_text(self, openid: str, content: str):
        param = {
            "touser": openid,
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        return self.post(self.url_custom_send, param)

    def custom_send_link_archive(self, openid: str, archive_list: list):
        param = {
            "touser": openid,
            "msgtype": "news",
            "news": {
                "articles": [x for x in archive_list]
            }
        }
        return self.post(self.url_custom_send, param)
