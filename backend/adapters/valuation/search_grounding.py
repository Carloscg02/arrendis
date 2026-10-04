import urllib.request
import urllib.error
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_NO_REDIRECT_OPENER = urllib.request.build_opener(_NoRedirectHandler)


def resolve_real_url(url: str, timeout: float = 2.0) -> str:
    """Resuelve redirecciones de Google Search Grounding a sus URLs finales de destino."""
    if not url or "grounding-api-redirect" not in url:
        return url
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with _NO_REDIRECT_OPENER.open(req, timeout=timeout) as resp:
            return resp.geturl()
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            loc = e.headers.get("Location")
            if loc:
                return urljoin(url, loc)
    except Exception:
        pass
    return url


def resolve_grounding_urls(raw_urls: list[str], max_workers: int = 5) -> list[str]:
    """Resuelve concurrentemente una lista de URLs de redirección de Google."""
    if not raw_urls:
        return []
    with ThreadPoolExecutor(max_workers=min(len(raw_urls), max_workers)) as executor:
        return list(executor.map(resolve_real_url, raw_urls))
