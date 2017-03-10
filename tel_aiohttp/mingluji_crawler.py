import asyncio
from asyncio import Queue
import async_timeout
import aiohttp
from aiohttp import ClientSession, ClientResponse
import lxml.html.soupparser as parser
from database import tel, IndexInfo, IndexUrls


class Crawler:
    def __init__(self, session: ClientSession, max_tasks=10):
        self._session = session
        self.max_tasks = max_tasks
        self._queue = Queue()
        for url in self.start_urls:
            self._queue.put_nowait(url)

    @property
    def start_urls(self):
        raise NotImplemented

    async def crawl(self):
        workers = [asyncio.Task(self.work()) for _ in range(self.max_tasks)]

        # wait
        await self._queue.join()
        print('work done.')
        for w in workers:
            w.cancel()

    async def work(self):
        while True:
            url = await self._queue.get()
            # Download page and add new links to self.q.
            await self.fetch(url)
            self._queue.task_done()

    async def fetch(self, url):
        with async_timeout.timeout(30):
            response = await self._session.get(url)
        try:
            links = await self.parse_links(response)
            for link in links:
                self._queue.put_nowait(link)
        except Exception as ex:
            print('fetch:', ex)
        finally:
            # Return connection to pool.
            await response.release()

    async def parse_links(self, response: ClientResponse):
        raise NotImplemented


class MinglujiCrawler(Crawler):
    province_list = [
        ('beijing', 171687),
        ('tianjin', 111767), ('hebei', 659880), ('neimenggu', 50686), ('shanxi', 63784), ('shanghai', 437888),
        ('anhui', 284364), ('jiangsu', 674434), ('zhejiang', 1101332), ('shandong', 581626), ('jiangxi', 198528),
        ('fujian', 326675), ('guangdong', 1218709), ('guangxi', 26906), ('hainan', 15403), ('henan', 367400),
        ('hubei', 263745), ('hunan', 377253), ('heilongjiang', 98591), ('jilin', 97864), ('liaoning', 237335),
        ('shaanxi', 138053), ('gansu', 80866), ('ningxia', 5732), ('qinghai', 1217), ('xinjiang', 11031),
        ('chongqing', 164209), ('sichuan', 221072), ('yunnan', 117452), ('guizhou', 51572), ('xizang', 18)
    ]
    province_count = {k: int(v/100) for k, v in province_list}

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko'
    }

    def __init__(self, loop):
        session = aiohttp.ClientSession(loop=loop, headers=self.headers)
        super().__init__(session, max_tasks=30)

    @property
    def start_urls(self):
        for k, v in self.province_list:
            yield 'https://gongshang.mingluji.com/{0}/list'.format(k)

    async def parse_links(self, response: ClientResponse):
        link_urls = set()
        try:
            url = str(response.url_obj)
            text = await response.text()
            print(url, len(text), self._queue.qsize())

            # 记录当前页，避免重入
            try:
                await IndexUrls.url_add(url)
            except Exception as ex:
                print('add_url: ', ex)

            # 提取详情页链接
            dom = parser.fromstring(text)
            links = dom.cssselect('li.views-row a')
            rows = [{'index': url, 'name': x.text, 'url': x.attrib.get('href')} for x in links]
            async with tel.atomic():
                for row in rows:
                    await tel.create(IndexInfo, **row)

            # 翻页
            page = int(response.url_obj.query.get('page', 1))
            page_count = self.province_count.get(response.url_obj.parts[1], 2000)
            link_count = self._queue.qsize() < 1000 and 9 or 3
            for page_current in range(page, page_count + 1):
                url = str(response.url_obj.with_query(page=page_current))
                if await IndexUrls.url_exists(url):
                    continue
                link_urls.add(url)
                if len(link_urls) > link_count:
                    break

        except Exception as ex:
            print('parse_links: ', ex)
        finally:
            return link_urls

