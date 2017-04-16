from flask import Blueprint, request
from .titles import RangeTitlesApi
from .user import UserInfoApi
from .content import ContentApi

from database import Database, UserInfo
from web_funcs import text_response


api_v4 = Blueprint('api_v4', 'api_v4', url_prefix='/api/v4')
api_v4.add_url_rule('/titles', view_func=RangeTitlesApi.as_view('titles'))          # 招标信息查询
api_v4.add_url_rule('/user', view_func=UserInfoApi.as_view('user'))                 # 用户信息查询/保存
api_v4.add_url_rule('/content/<uuid>', view_func=ContentApi.as_view('content'))     # 详情信息查询


@api_v4.before_request
def before_api_request():
    """ 检查访问权限 """
    # Database.connect()
    uid = request.cookies.get('uid')
    if not UserInfo.user_exists(uid):
        return text_response('Invalid usage.')
