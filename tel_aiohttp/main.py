import asyncio
from mingluji_crawler import MinglujiCrawler


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    crawler = MinglujiCrawler(loop=loop)
    loop.run_until_complete(crawler.crawl())
    loop.close()

