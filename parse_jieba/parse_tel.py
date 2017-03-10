import jieba
from database import CompanyInfo, StatInfo


def company_name_stat():
    area_list = CompanyInfo.select(CompanyInfo.area).distinct().execute()
    for area in [x.area for x in area_list]:
        query = CompanyInfo.select(CompanyInfo.name).where(CompanyInfo.area == area)

        words = {}
        for row in query:
            for w in jieba.lcut(row.name):
                if len([c for c in w if ord(c) > 128]) < 2:
                    continue
                words[w] = words.get(w, 0) + 1

        stat = [(x, words[x]) for x in sorted(words, key=words.get, reverse=True) if words[x] > 1]

        def rows(ws: list):
            for k, v in ws:
                yield dict(area=area, word=k, count=v)
        StatInfo.insert_many(rows(stat)).execute()

if __name__ == '__main__':
    company_name_stat()
