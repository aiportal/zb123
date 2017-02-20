
class InfoDict(dict):
    @classmethod
    def from_selectors(cls, selectors, key_xpath: str, value_xpath: str) -> dict:
        info = InfoDict()
        for row in selectors:
            key = cls._join(row.xpath(key_xpath).extract())
            value = cls._join(row.xpath(value_xpath).extract())
            info[key] = value
        return info

    @staticmethod
    def _join(values: list):
        return ''.join([s.strip() for s in values])

    def get(self, name, default=None):
        keys = [k for k in self.keys() if name in k]
        if keys:
            return self[keys[0]]
        else:
            return default
