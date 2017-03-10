import asyncio
from asyncio import Queue
import aiohttp


class Crawler:
    def __init__(self, root_url: str, loop):
        self.max_tasks = 10
        self.seen_urls = set()
        self.session = aiohttp.ClientSession(loop=loop)
        self.q = Queue()
        self.q.put(root_url)

    async def crawl(self):
        """Run the crawler until all work is done."""
        workers = [asyncio.Task(self.work()) for _ in range(self.max_tasks)]

        # When all work is done, exit.
        await self.q.join()
        for w in workers:
            w.cancel()

    async def work(self):
        while True:
            url = await self.q.get()
            # Download page and add new links to self.q.
            await self.fetch(url)
            self.q.task_done()

    async def fetch(self, url):
        response = await self.session.get(url)
        try:
            links = await self.parse_links(response)
            # Python set-logic:
            for link in links.difference(self.seen_urls):
                self.q.put_nowait(link)
            self.seen_urls.update(links)
        finally:
            # Return connection to pool.
            await response.release()

    async def parse_links(self, response):
        pass

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    crawler = Crawler('http://gongshang.mingluji.com/beijing/list', loop=loop)
    loop.run_until_complete(crawler.crawl())
