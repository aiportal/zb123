from flask.views import MethodView
from web_funcs import json_response
from database import db_fetch, RuntimeEvent
from datetime import datetime, date, timedelta
import gevent


"""
从 gather_full 到 gather_new 搬运数据
"""


class DataUpdateApi(MethodView):
    """ 更新数据，从 Gather_full 到 Gather_new """

    def get(self, day: str=None):
        day = day and datetime.strptime(day, '%Y-%m-%d').date() or date.today()
        gevent.spawn(self.update_gather_data, day)
        return json_response({'state': 'started'})

    @staticmethod
    def update_gather_data(day: date):
        try:
            sql_update = """
                insert into gather_new(uuid, `day`, title, `subject`,
                    source, area, industry, pid, `end`, tender, budget, tels, `time`)
                select G.uuid, G.`day`, G.title, G.`subject`,
                    G.source, G.area, G.industry, G.pid, G.`end`, G.tender, G.budget, G.tels, G.time
                from gather_full G
                where day = %s
                    and G.uuid not in (select uuid from gather_new)
            """
            db_fetch.execute_sql(sql_update, day)
            print('gather updated for ', day)
        except Exception as ex:
            RuntimeEvent.log_event('exception', {'ex': str(ex)})
