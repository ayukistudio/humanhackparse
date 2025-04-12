import re
from typing import Self

_url_regex = re.compile(
            r"^(https?://)?"                    # Протокол (http или https), может быть необязательным
            r"(([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})" # Доменное имя (например, example.com)
            r"(:\d+)?"                          # Порт (например, :80), необязательный
            r"(/[-a-zA-Z0-9@:%_+.~#?&/=]*)?$"   # Путь, параметры, якорь — необязательные
        )

class Url:
    def __init__(self, url: str | Self):
        if isinstance(url, str):
            match = Url._get_match_url(url)

            if match is None:
                raise ValueError("'url' parameter is invalid URL.")

            base_url = match[1] + match[2]

            self._base_url: str = base_url
            self._current_url: str = url
        if isinstance(url, Url):
            self._base_url = url._base_url
            self._current_url: str = url._current_url

    def join(self, path: str):
        if not isinstance(path, str):
            raise ValueError("'path' is invalid.")

        if path.startswith('/'):
            return self._base_url + path
        return self._base_url + '/' + path

    @property
    def full_url(self):
        return self._current_url

    @property
    def base_url(self):
        return self._base_url

    @staticmethod
    def check_url(url: str) -> bool:
        return _url_regex.match(url) is not None

    @staticmethod
    def get_base_url(url: str) -> str | None:
        m = _url_regex.match(url)
        if m is None:
            return None
        return m[2]

    @staticmethod
    def get_full_base_url(url: str) -> str | None:
        m = _url_regex.match(url)
        if m is None:
            return None
        return m[1] + m[2]

    @staticmethod
    def _get_match_url(url: str):
        return _url_regex.match(url)
