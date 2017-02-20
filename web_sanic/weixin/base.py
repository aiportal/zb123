from .app import WxAppCore


class WxArchive(WxAppCore):
    @staticmethod
    def link_archive(title: str, description: str, url: str, picurl: str) -> dict:
        """ 图文消息（点击跳转到外链）
        :param title: 标题
        :param description: 描述
        :param url: 链接
        :param picurl: 封面图片
        :return:
        """
        return {
            "title": title,
            "description": description,
            "url": url,
            "picurl": picurl
        }

    @staticmethod
    def media_article(title: str, image_id: str, content: str, author: str, digest: str, url: str, show_cover=False):
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
