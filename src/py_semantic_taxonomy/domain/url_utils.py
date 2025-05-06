from typing import Any
from urllib.parse import quote

from py_semantic_taxonomy.domain.constants import API_VERSION_PREFIX, APIPaths


# Custom class to allow FastAPI URL patterns like `/foo/{iri:path}` to be
# interpolated without access to the FastAPI app.
class URLComponent:
    def __init__(self, string):
        self.string = string

    def __str__(self) -> str:
        return self.string

    def __format__(self, format_spec: str) -> str:
        if not format_spec:
            return self.string
        elif format_spec == "path":
            return quote(self.string)
        else:
            raise ValueError(f"Invalid format spec `{format_spec}`")


def get_full_api_path(api_path: str, **kwargs: dict[str, Any]) -> str:
    """
    Easier access to API paths including prefix for use in templates, etc.

    Uses string concatenation because `urljoin` wants complete URLs, and using path join operations
    just feels dirty.
    """
    url = API_VERSION_PREFIX + getattr(APIPaths, api_path)
    if kwargs:
        url = url.format(**{key: URLComponent(value) for key, value in kwargs.items()})
    return url
