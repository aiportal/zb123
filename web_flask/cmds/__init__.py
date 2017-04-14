from flask import Blueprint
from .feature import UserFeatureApi


cmd_v3 = Blueprint('cmd_v3', 'cmd_v3', url_prefix='/cmd/v3')
cmd_v3.add_url_rule('/feature/<period>', view_func=UserFeatureApi.as_view('feature'))   # 统计用户特征
cmd_v3.add_url_rule('/feature/<period>/<uid>', view_func=UserFeatureApi.as_view('feature_user'))   # 统计用户特征

