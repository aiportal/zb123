from flask import Blueprint, request
from database import UserInfo
from .common import text_response
from .user import UserInfoApi
from .titles import DayTitlesApi
from .content import ContentInfoApi
from .suggest import SuggestApi


api_v3_1 = Blueprint('api_v3_1', __name__, url_prefix='/api/v3_1')
api_v3_1.add_url_rule('/user', view_func=UserInfoApi.as_view('user'))                       # 用户信息查询/保存
api_v3_1.add_url_rule('/titles', view_func=DayTitlesApi.as_view('titles'))                  # 每日信息查询
api_v3_1.add_url_rule('/content/<uuid>', view_func=ContentInfoApi.as_view('content'))       # 详情信息查询
api_v3_1.add_url_rule('/suggest', view_func=SuggestApi.as_view('suggest'))                  # 意见反馈


@api_v3_1.before_request
def before_api_request():
    """ 检查访问权限 """
    # Database.connect()
    uid = request.cookies.get('uid')
    if not UserInfo.user_exists(uid):
        return text_response('Invalid usage.')
