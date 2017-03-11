import scrapy
from database.telephone import IndexInfo, IndexUrls


class IndexSpider(scrapy.Spider):
    name = 'mingluji_index'

    province_list = [
        ('beijing', 171687),
        ('tianjin', 111767), ('hebei', 659880), ('neimenggu', 50686), ('shanxi', 63784), ('shanghai', 437888),
        ('anhui', 284364), ('jiangsu', 674434), ('zhejiang', 1101332), ('shandong', 581626), ('jiangxi', 198528),
        ('fujian', 326675), ('guangdong', 1218709), ('guangxi', 26906), ('hainan', 15403), ('henan', 367400),
        ('hubei', 263745), ('hunan', 377253), ('heilongjiang', 98591), ('jilin', 97864), ('liaoning', 237335),
        ('shaanxi', 138053), ('gansu', 80866), ('ningxia', 5732), ('qinghai', 1217), ('xinjiang', 11031),
        ('chongqing', 164209), ('sichuan', 221072), ('yunnan', 117452), ('guizhou', 51572), ('xizang', 18)
    ]

    page_count = {k: int(v/100) for k, v in province_list}

    custom_settings = {
        'COOKIES_ENABLED': False,
        'DOWNLOAD_DELAY': 0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 32,
        'CONCURRENT_REQUESTS_PER_IP': 32,
    }

    def start_requests(self):
        for province in self.province_list:
            url = 'https://gongshang.mingluji.com/{0}/list'.format(province[0])
            yield scrapy.Request(url, meta={'province': province[0], 'page_count': str(int(province[1]/100))})

    def parse(self, response):
        # 存储
        if not IndexUrls.url_exists(response.url):
            rows = []
            for link in response.css('li.views-row a'):
                row = {
                    'index': response.url,
                    'name': link.xpath('./text()')[0].extract(),
                    'url': link.xpath('./@href')[0].extract()
                }
                rows.append(row)

            IndexInfo.insert_many(rows)
            IndexUrls.url_add(response.url)

        # 翻页
        province = response.meta['province']
        page_count = int(response.meta['page_count'])
        add_count = 3
        for page in range(1, page_count + 1):
            url = 'https://gongshang.mingluji.com/{0}/list?page={1}'.format(province, page)
            if add_count < 1:
                break
            if not IndexUrls.url_exists(url):
                add_count -= 1
                yield scrapy.Request(url, meta=response.meta)
