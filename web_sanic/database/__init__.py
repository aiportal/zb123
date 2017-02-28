from .fetch import GatherInfo, ContentInfo, EventLog
from .fetch import AsyncManager as FetchManager
from .zb123 import UserInfo, FilterRule, AnnualFee, SysConfig, SuggestInfo, RuntimeEvent, AccessLog
from .zb123 import AsyncManager as Zb123Manager


fetch = FetchManager()
zb123 = Zb123Manager()
