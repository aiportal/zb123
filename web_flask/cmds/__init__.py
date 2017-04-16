from flask import Blueprint
from .feature import UserFeatureApi
from .update import DataUpdateApi

cmd_v3 = Blueprint('cmd_v3', 'cmd_v3', url_prefix='/cmd/v3')
cmd_v3.add_url_rule('/feature/<period>', view_func=UserFeatureApi.as_view('feature'))
cmd_v3.add_url_rule('/feature/<period>/<uid>', view_func=UserFeatureApi.as_view('feature_user'))
cmd_v3.add_url_rule('/update/data', view_func=DataUpdateApi.as_view('update_data'))
cmd_v3.add_url_rule('/update/data/<day>', view_func=DataUpdateApi.as_view('update_data_day'))
