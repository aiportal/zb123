import aiohttp
import asyncio
import async_timeout
from lxml import etree
import lxml.html.soupparser as parser
import re


def mingluji_index_urls(province: str, count: int) -> str:
    for page in range(1, count + 1, step=10):
        yield 'https://gongshang.mingluji.com/{0}/list?page={1}'.format(province)


async def fetch(session, url):
    with async_timeout.timeout(10):
        async with session.get(url) as response:
            return await response.text()

async def main(loop):
    url_base = 'https://gongshang.mingluji.com'
    url = 'https://gongshang.mingluji.com/beijing/list'
    async with aiohttp.ClientSession(loop=loop) as session:
        html = await fetch(session, url)
        dom = parser.fromstring(html)

        # 全部链接保存到数据表
        links = dom.cssselect('li.views-row a')
        for link in links:
            data = {
                'name': link.text,
                'url': url_base + link.attrib['href']
            }


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
