from .app import WxAppCore
import os

class WxMediaManager(WxAppCore):
    """ 微信素材管理 """
    @staticmethod
    def article(title: str, image_id: str, content: str, author: str, digest: str, url: str, show_cover=False):
        """ 图文素材
        :param title: 标题
        :param image_id: 图文消息的封面图片素材id（必须是永久mediaID）
        :param content: 图文消息的具体内容，支持HTML标签，必须少于2万字符，小于1M，且此处会去除JS
        :param author: 作者
        :param digest: 图文消息的摘要，仅有单图文消息才有摘要，多图文此处为空
        :param url: 图文消息的原文地址，即点击“阅读原文”后的URL
        :param show_cover: 是否显示封面
        :return: dict
        """
        return {
            "title": title,
            "thumb_media_id": image_id,                 # 图文消息缩略图的media_id
            "content": content,                         # 图文消息的具体内容，支持HTML标签，必须少于2万字符，小于1M，会去除JS
            "content_source_url": url,                  # “阅读原文”的页面链接
            "author": author,
            "digest": digest,
            "show_cover_pic": show_cover and 1 or 0     # 是否显示封面
        }

    def add_news(self, *articles):
        """ 新增永久图文素材
        图文消息素材的上限为5000
        :param articles: 图文素材
        :return: media_id
        """
        url_add_news = 'https://api.weixin.qq.com/cgi-bin/material/add_news'
        data = {'articles': articles}
        return self.post(url_add_news, data)['media_id']

    def upload_material(self, file: str):
        """ 上传永久素材
        图片素材的上限为5000，其他类型为1000
        图片大小不超过2M，支持bmp/png/jpeg/jpg/gif格式，语音大小不超过5M，长度不超过60秒，支持mp3/wma/wav/amr格式
        :param file: 文件路径
        :return: media_id
        """
        url_material = 'https://api.weixin.qq.com/cgi-bin/material/add_material'
        ext = os.path.splitext(file)[1].lower()
        if ext in ['.bmp', '.png', '.jpeg', '.jpg', '.gif']:
            file_type = 'image'         # 2M
        elif ext in ['.mp3', '.wma', '.waw', '.amr']:
            file_type = 'voice'
        else:
            raise ValueError('unsupported file type')
        url = '{0}?type={1}'.format(url_material, file_type)
        files = {'media': open(file, 'rb')}
        return self.upload(url, files)['media_id']


class WxNewsManager(WxAppCore):
    """ 微信图文消息管理 """
    def publish_news(self, media_id):
        """ 发布图文消息
        :param media_id: 图文消息ID
        :return: msg_id
        """
        url_sendall = 'https://api.weixin.qq.com/cgi-bin/message/mass/sendall'
        data = {
            "filter": {
                "is_to_all": True
            },
            "msgtype": "mpnews",
            "mpnews": {
                "media_id": media_id
            }
        }
        return self.post(url_sendall, data).get('msg_id')

    def preview_news(self, media_id, openid):
        """ 预览图文消息
        :param media_id: 图文消息ID
        :param openid: 用户的微信ID
        :return: msg_id
        """
        url_preview = 'https://api.weixin.qq.com/cgi-bin/message/mass/preview'
        data = {
           "touser": openid,
           "msgtype": "mpnews",
           "mpnews": {
               "media_id": media_id
           }
        }
        return self.post(url_preview, data).get('msg_id')
