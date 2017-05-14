import json
import zipfile


class ZipPackagePipeline(object):
    def open_spider(self, spider):
        pass

    def process_item(self, item, spider):
        if not item.get('html'):
            return item
        zip_path = '{0}/{1}-{2}.zip'.format(spider.settings.get('PACKAGE_FOLDER'), item['source'], item['day'][0:4])
        file_path = '{0}/{1}/{2}'.format(item['source'], item['day'].replace('-', ''), item['uuid'])
        with zipfile.ZipFile(zip_path, 'a', zipfile.ZIP_DEFLATED) as z:
            z.writestr(file_path + '.html', item['html'])
            item['html'] = file_path + '.html'
            item['contents'] = None
            item['digest'] = None
            z.writestr(file_path + '.json', json.dumps(dict(item), ensure_ascii=False))
        return item
