from .items import GatherItem
from database import GatherInfo, ContentInfo, SysConfig, db_mysql
import json
import zipfile
import csv
import os
from database import JobIndex
import peewee
import logging


class MysqlPipeline(object):
    def open_spider(self, spider):
        SysConfig.set_item(subject='source', key=spider.name, value=spider.alias)

    def process_item(self, item, spider):
        if not isinstance(item, GatherItem):
            return item

        obj = dict(item)

        try:
            # GatherInfo
            g = GatherInfo(**obj)
            g.extends = json.dumps(item['extends'], ensure_ascii=False)
            g.save(force_insert=True)

            # ContentInfo
            c = ContentInfo(**obj)
            c.html = None
            c.contents = json.dumps(item['contents'], ensure_ascii=False)
            c.digest = item.get('digest') and json.dumps(item['digest'], ensure_ascii=False)
            c.attachments = item.get('attachments') and json.dumps(item['attachments'], ensure_ascii=False)
            c.save(force_insert=True)
        except peewee.IntegrityError as e:
            msg = 'uuid: {0}, url: {1}'.format(item['uuid'], item['url'])
            spider.log(msg, logging.ERROR)
            spider.log(str(e), logging.ERROR)

        # JobIndex
        assert JobIndex.url_hash(item['url']) == item['uuid']
        JobIndex.url_insert(url=item['url'])

        return item


class ZipPackagePipeline(object):
    def open_spider(self, spider):
        # 创建文件夹
        base_folder = spider.settings.get('PACKAGE_FOLDER')
        spider.zip_folder = '{0}/{1}'.format(base_folder, spider.name)
        os.makedirs(spider.zip_folder, exist_ok=True)

    def process_item(self, item, spider):
        if 'html' not in item or not item['item']:
            return item
        zip_path = '{0}/{1}-{2}.zip'.format(spider.zip_folder, item['source'], item['day'][0:4])
        file_path = '/'.join(filter(None, [
            item['source'], item['area'], item['subject'], item['day'].replace('-', ''), item['uuid']
        ]))
        with zipfile.ZipFile(zip_path, 'a', zipfile.ZIP_DEFLATED) as z:
            z.writestr(file_path + '.html', item['html'])
            item['html'] = file_path + '.html'
            item['contents'] = None
            z.writestr(file_path + '.json', json.dumps(dict(item), ensure_ascii=False))
        return item


class CsvPipeline(object):
    def open_spider(self, spider):
        # 创建文件夹
        base_folder = spider.settings.get('PACKAGE_FOLDER')
        spider.csv_folder = '{0}/{1}'.format(base_folder, spider.name)
        os.makedirs(spider.csv_folder, exist_ok=True)

    def process_item(self, item, spider):
        file_path = '{0}/{1}-{2}.csv'.format(spider.csv_folder, item['source'], item['day'][0:4])
        data = dict(item)
        del data['contents']
        del data['top_url']
        del data['real_url']
        del data['index_url']
        del data['digest']
        keys = sorted(data.keys())
        values = [data[k] for k in keys]
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                csv.writer(f, lineterminator='\n').writerow(keys)
        with open(file_path, 'a+', encoding='utf-8') as f:
            csv.writer(f, lineterminator='\n').writerow(values)
        return item


# class AttachmentsPipeline(object):
#     def process_item(self, item, spider):
#         # 如果有附件属性，记录附件下载后的本地网址
#         if isinstance(item, GatherItem) and item.get('attachments'):
#             attachments = item.get('attachments') or []
#             files = item.get('files') or []
#             for a in attachments:
#                 fs = [f for f in files if f['url'] == a['url']]
#                 a['file'] = fs and next(iter(fs))['path'] or None
#         if 'file_urls' in item:
#             del item['file_urls']
#         if 'files' in item:
#             del item['files']
#         return item
