import re
from urllib.parse import urlparse, urlunparse
from backend.domain.value_objects import ValuationSource
from backend.adapters.valuation.schemas import _SourcePayload


def sanitize_property_url(url: str) -> str:
    """Corrige slugs de Idealista alucinados por el LLM hacia rutas canónicas y activas."""
    if not url:
        return url
    clean = url.strip()
    if "idealista.com" in clean:
        clean = clean.replace("/teatinos-universidad/", "/teatinos/")
        clean = clean.replace("/hacienda-bizcochero/", "/el-tejar-hacienda-bizcochero/")
        clean = clean.replace("/carretera-de-cadiz-huelin/", "/carretera-de-cadiz/huelin/")

        clean = re.sub(r"/con-de-(?:cuatro|4)-dormitorios?/?", "/con-de-cuatro-cinco-habitaciones-o-mas/", clean)
        clean = re.sub(r"/con-de-(?:tres|3)-dormitorios?/?", "/con-de-tres-dormitorios/", clean)
        clean = re.sub(r"/con-de-(?:dos|2)-dormitorios?/?", "/con-de-dos-dormitorios/", clean)
        clean = re.sub(r"/con-de-(?:un|1)-dormitorios?/?", "/con-de-un-dormitorio/", clean)

        clean = re.sub(r"/con-precio-hasta_[0-9]+/?", "/", clean)

        # Si se concatenó el slug de una calle dentro de la jerarquía regional (lo que provoca 404 en Idealista)
        # ej. /venta-viviendas/malaga/teatinos/avenida-doctor-manuel-dominguez/ -> /venta-viviendas/malaga/teatinos/
        street_pattern = r"/(?:avenida|avda|calle|paseo|plaza|camino|carrer|via)-[^/]+/?$"
        if re.search(street_pattern, clean) and "/geo/" not in clean:
            clean = re.sub(street_pattern, "/", clean)

        parsed = urlparse(clean)
        clean_path = re.sub(r"/+", "/", parsed.path)
        if not clean_path.endswith("/"):
            clean_path += "/"
        clean = urlunparse(parsed._replace(path=clean_path))

    return clean


def format_source_title(raw_title: str | None, url: str) -> str:
    """Genera un título legible y representativo para los enlaces de Idealista y Fotocasa."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")

        if raw_title:
            stripped = raw_title.strip()
            if (
                stripped.lower() not in (domain.lower(), "idealista.com", "fotocasa.es", "habitaclia.com")
                and len(stripped) > 8
            ):
                return stripped

        parts = [p for p in parsed.path.strip("/").split("/") if p]
        if "idealista.com" in domain and parts:
            is_alquiler = any("alquiler" in p for p in parts)
            is_venta = any("venta" in p for p in parts)
            action = "Alquiler" if is_alquiler else ("Venta" if is_venta else "Inmuebles")
            loc_parts = [
                p for p in parts
                if p not in (
                    "geo", "venta-viviendas", "alquiler-viviendas", "con-pisos",
                    "inmuebles", "areas", "con-de-cuatro-cinco-habitaciones-o-mas",
                    "con-de-tres-dormitorios", "con-de-dos-dormitorios", "con-de-un-dormitorio",
                )
            ]
            clean_zone = ", ".join([p.replace("-", " ").title() for p in loc_parts])
            return f"{action} de pisos en {clean_zone} — Idealista" if clean_zone else f"{action} de viviendas — Idealista"
        elif "fotocasa.es" in domain and parts:
            is_alquiler = "alquiler" in parts
            action = "Alquiler" if is_alquiler else "Venta"
            loc_parts = [
                p for p in parts
                if p not in ("es", "comprar", "alquiler", "viviendas", "vivienda", "area", "maps", "l", "d")
            ]
            clean_zone = ", ".join([p.replace("-", " ").title() for p in loc_parts if not p.isdigit() and len(p) > 2])
            return f"{action} en {clean_zone} — Fotocasa" if clean_zone else f"{action} de viviendas — Fotocasa"
    except Exception:
        pass
    return raw_title or url


def assemble_sources(
    payload_sources: list[_SourcePayload],
    resolved_grounding: list[tuple[str, str]],
) -> list[ValuationSource]:
    """Combina fuentes del payload del modelo con URLs reales resueltas desde Google Search Grounding."""
    sources: list[ValuationSource] = []
    used_grounding_indices: set[int] = set()
    seen_urls: set[str] = set()

    for s in payload_sources:
        s_url = sanitize_property_url(s.url.strip())
        if not (s_url.startswith("http://") or s_url.startswith("https://")):
            continue

        matched_idx = None
        # 1. Coincidencia exacta de URL
        for idx, (g_url, _) in enumerate(resolved_grounding):
            if g_url.rstrip("/") == s_url.rstrip("/"):
                matched_idx = idx
                break

        # 2. Coincidencia por portal y modalidad (venta/alquiler) si no hubo match exacto
        if matched_idx is None and resolved_grounding:
            s_domain = urlparse(s_url).netloc.replace("www.", "")
            s_is_alquiler = "alquiler" in s_url.lower()
            for idx, (g_url, _) in enumerate(resolved_grounding):
                if idx in used_grounding_indices:
                    continue
                g_domain = urlparse(g_url).netloc.replace("www.", "")
                g_is_alquiler = "alquiler" in g_url.lower()
                if s_domain and s_domain == g_domain and s_is_alquiler == g_is_alquiler:
                    matched_idx = idx
                    break

        if matched_idx is not None:
            used_grounding_indices.add(matched_idx)
            g_url, g_title = resolved_grounding[matched_idx]
            final_url = g_url
            final_title = format_source_title(g_title or s.title, g_url)
        else:
            final_url = s_url
            final_title = format_source_title(s.title, s_url)

        norm = final_url.rstrip("/")
        if norm not in seen_urls:
            seen_urls.add(norm)
            sources.append(
                ValuationSource(
                    title=final_title,
                    url=final_url,
                    price=s.price,
                    surface_m2=s.surface_m2,
                )
            )

    # Añadir fuentes restantes de búsqueda no emparejadas con el payload
    for idx, (g_url, g_title) in enumerate(resolved_grounding):
        if idx in used_grounding_indices:
            continue
        norm = g_url.rstrip("/")
        if norm not in seen_urls:
            seen_urls.add(norm)
            sources.append(
                ValuationSource(
                    title=format_source_title(g_title, g_url),
                    url=g_url,
                )
            )

    return sources
