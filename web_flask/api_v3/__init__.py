from flask import Blueprint, request, make_response

from database import Database, UserInfo
from .user import UserInfoApi, UserRuleApi, SuggestApi
from .web import DayTitlesApi, ContentApi


# API接口
api_v3 = Blueprint('api_v3', __name__, url_prefix='/api/v3')
api_v3.add_url_rule('/user', view_func=UserInfoApi.as_view('user'))                    # 用户界面初始化
api_v3.add_url_rule('/rule', view_func=UserRuleApi.as_view('rule'))                    # 设置筛选规则
api_v3.add_url_rule('/titles', view_func=DayTitlesApi.as_view('titles'))               # 获取招标信息
api_v3.add_url_rule('/content/<uuid>', view_func=ContentApi.as_view('content'))        # 招标信息详情
api_v3.add_url_rule('/suggest', view_func=SuggestApi.as_view('suggest'))               # 意见反馈


@api_v3.before_request
def before_api_request():
    """ 检查访问权限 """
    Database.connect()
    uid = request.cookies.get('uid')
    user = UserInfo.get_user(uid)
    if not user:
        return make_response('Invalid usage.')
