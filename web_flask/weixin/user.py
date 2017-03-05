from .app import WxAppCore


class WxTagManager(WxAppCore):
    """ 用户标签管理 """
    def tag_all(self):
        """ 获取全部标签
        :return: [{id, name, count},...]：标签ID，标签名称，用户数
        """
        url_tag_all = 'https://api.weixin.qq.com/cgi-bin/tags/get'
        return self.get(url_tag_all)['tags']

    @property
    def tags(self):
        """ 标签字典 """
        if not hasattr(self, '__tags'):
            setattr(self, '__tags', {})
        tags = getattr(self, '__tags')
        if not tags:
            tags.update({x['id']: x['name'] for x in self.tag_all()})
        return tags

    def tag_create(self, name):
        """ 创建标签
        一个公众号，最多可以创建100个标签。
        :param name: 标签名称
        :return: tag_id
        """
        url_tags_create = 'https://api.weixin.qq.com/cgi-bin/tags/create'
        data = {
            'tag': {'name': name}
        }
        tag_id = self.post(url_tags_create, data)['tag']['id']
        del self.tags
        return tag_id

    def tag_update(self, tag_id: int, name: str):
        """ 更新标签
        :param tag_id: 标签id
        :param name: 标签名称
        """
        url_tag_update = 'https://api.weixin.qq.com/cgi-bin/tags/update'
        data = {
            'tag': {'id': tag_id, 'name': name}
        }
        self.post(url_tag_update, data)
        del self.tags

    def tag_delete(self, tag_id):
        """ 删除标签
        :param tag_id: 标签id
        """
        url_tag_delete = 'https://api.weixin.qq.com/cgi-bin/tags/delete'
        data = {
            'tag': {'id': tag_id}
        }
        self.post(url_tag_delete, data)
        del self.tags

    def tag_users(self, tag_id):
        """ 获取此标签下的用户列表(openid) """
        url_tag_users = 'https://api.weixin.qq.com/cgi-bin/user/tag/get'
        data = {
            'tagid': tag_id,
            'next_openid': ''   # 第一个拉取的OPENID，不填默认从头开始拉取
        }
        return self.post(url_tag_users, data)['data']['openid']


class WxUserManager(WxTagManager):
    """ 微信用户管理 """
    def user_list(self):
        """ 获取用户列表，一次最多返回10000条
        :return: openid 列表
        """
        # 最多返回10000条记录，超出部分需要用next_openid继续获取
        url_user_get = 'https://api.weixin.qq.com/cgi-bin/user/get'
        res = self.get(url_user_get, {'next_openid': None})
        return res['data']['openid']

    def user_info(self, openid: str):
        """ 获取用户信息 """
        url_user_info = 'https://api.weixin.qq.com/cgi-bin/user/info'
        params = {'openid': openid, 'lang': 'zh_CN'}
        return self.get(url_user_info, params)

    def user_batch(self, users: list):
        """ 批量获取用户信息，最多支持一次拉取100条。
        :param users: openid 列表
        :return:
        """
        url_user_batch = 'https://api.weixin.qq.com/cgi-bin/user/info/batchget'
        data = {
            'user_list': [{'openid': x, 'lang': 'zh-CN'} for x in users]
        }
        return self.post(url_user_batch, data)['user_info_list']

    def user_blacklist(self):
        """ 获取公众号的黑名单列表 """
        # 当公众号黑名单列表数量超过 10000 时，可通过填写 next_openid 的值，从而多次拉取列表的方式来满足需求。
        url_blacklist = 'https://api.weixin.qq.com/cgi-bin/tags/members/getblacklist'
        data = {
            "begin_openid": None
        }
        return self.post(url_blacklist, data)['data']['openid']
