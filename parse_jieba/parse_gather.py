import jieba
import peewee
from database import GatherInfo, ContentInfo, Statistic
from datetime import date
import json
import itertools


def gather_title_stat(start: date, end: date, source: str=None):
    """ 统计标题中的词频 """

    query = GatherInfo.select(GatherInfo.title).where(GatherInfo.day.between(start, end))
    if source:
        query = query.where(GatherInfo.source == source)

    words = {}
    count = query.count()
    size = 1000
    for offset in range(0, count, size):
        for rec in query.offset(offset).limit(size):
            for w in jieba.lcut(rec.title):
                if len([c for c in w if ord(c) > 128]) < 2:
                    continue
                words[w] = words.get(w, 0) + 1

    return [(x, words[x]) for x in sorted(words, key=words.get, reverse=True)]


def gather_content_stat(start: date, end: date, source: str=None):
    """ 统计招标信息中的词频 """
    query_count = GatherInfo.select().where(GatherInfo.day.between(start, end))
    if source:
        query_count = query_count.where(GatherInfo.source == source)
    count = query_count.count()

    query = ContentInfo.select(ContentInfo.contents).where(ContentInfo.day.between(start, end))
    if source:
        query = query.where(ContentInfo.source == source)

    words = {}
    size = 1000
    for offset in range(0, count, size):
        for rec in query.offset(offset).limit(size):
            if not rec.contents:
                continue
            contents = [x for x in json.loads(rec.contents)]
            ws = itertools.chain(*[jieba.lcut(x) for x in contents])
            for w in ws:
                if len([c for c in w if ord(c) > 128]) < 2:
                    continue
                words[w] = words.get(w, 0) + 1

    return [(x, words[x]) for x in sorted(words, key=words.get, reverse=True)]


def statistic_rows(words: list, defaults: dict):
    for k, v in words:
        defaults.update(word=k, count=v)
        yield defaults


def stat_gather_words(stat_content=False):
    """ 按年度和来源统计内容词频 """
    sources = GatherInfo.select(GatherInfo.source).distinct().tuples()
    params = [(year, source[0])
              for year in range(2015, 2013, -1)
              for source in sources]
    for year, source in params:
        start = date(year, 1, 1)
        end = date(year + 1, 1, 1)

        # 检查数据表，避免重复统计
        query_exists = Statistic.select().where(Statistic.tab == 'gather').where(Statistic.col == source)\
            .where(Statistic.tags == str(year))     # type: peewee.SelectQuery
        if query_exists.exists():
            continue

        words = gather_title_stat(start, end, source)
        rows = statistic_rows(words, dict(tab='gather', col=source, tags=str(year), info={}))
        Statistic.insert_many(rows).execute()
        if stat_content:
            words = gather_content_stat(start, end, source)
            rows = statistic_rows(words, dict(tab='content', col=source, tags=str(year), info={}))
            Statistic.insert_many(rows).execute()
        print(source, year)

if __name__ == '__main__':
    stat_gather_words(True)
