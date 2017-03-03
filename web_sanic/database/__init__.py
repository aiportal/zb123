from .fetch import GatherInfo, ContentInfo, EventLog
from .fetch import AsyncManager as FetchManager
from .zb123 import UserInfo, FilterRule, AnnualFee, SysConfig, SuggestInfo, RuntimeEvent, AccessLog
from .zb123 import AsyncManager as Zb123Manager

from .fetch import db_fetch
from .zb123 import db_zb123

fetch = FetchManager()
zb123 = Zb123Manager()
