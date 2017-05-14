import csv
import os


class CsvFilePipeline(object):
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
