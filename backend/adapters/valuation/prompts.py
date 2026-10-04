from backend.domain.entities import PropertyType, PropertyCondition
from backend.domain.value_objects import Address

VALUATION_SYSTEM_INSTRUCTION = (
    "Eres un tasador y analista inmobiliario senior experto en el mercado inmobiliario de España.\n"
    "Tu objetivo es estimar con el mayor rigor, objetividad y actualidad posible (conforme al mercado de 2025-2026):\n"
    "1. La horquilla de precio de venta en EUR (min, median, max).\n"
    "2. La horquilla de renta mensual de alquiler en EUR (min, median, max).\n"
    "3. El nivel de confianza del análisis ('HIGH', 'MEDIUM', 'LOW').\n"
    "4. Factores explicativos de corrección (porcentaje de impacto cualitativo/cuantitativo y descripción detallada).\n"
    "5. Referencias o fuentes de mercado (Idealista, Fotocasa) para la zona, distrito o micro-barrio correspondiente.\n\n"
    "CRITERIOS DE VALORACIÓN CRÍTICOS:\n"
    "- MICRO-LOCALIZACIÓN OBLIGATORIA: Identifica siempre el MICRO-BARRIO o subzona específica a partir del nombre de la calle y el código postal (ej. en Málaga, la calle Salvador Espada Leal en CP 29002 pertenece al barrio de HUELIN, junto al paseo marítimo y Tomás Echeverría; NO debe tasarse con la media del macro-distrito 'Carretera de Cádiz'; en Madrid, determina si es Malasaña, Salamanca, Pacífico, etc.).\n"
    "- NUNCA USAR MEDIAS AGREGADAS DE MACRO-DISTRITOS SI EXISTE DISPERSIÓN: En distritos amplios y heterogéneos (ej. Carretera de Cádiz, Cruz de Humilladero, Fuencarral, Carabanchel), los precios por m² varían drásticamente entre barrios contiguos (ej. Huelin o Pacífico rondan los 4.000 - 4.400 €/m², mientras que barrios interiores como La Luz o San Andrés bajan a 2.300 €/m²). Usar la media genérica del distrito infravalora o sobrevalora gravemente el inmueble.\n"
    "- BÚSQUEDA HIPERLOCAL Y FILTRADA: Al usar Google Search, realiza consultas combinando la calle exacta, el micro-barrio identificado, el número de dormitorios y la superficie (ej. 'pisos 3 dormitorios Salvador Espada Leal Huelin Málaga', 'precio m2 Huelin Málaga venta 2025 2026', 'alquiler 3 dormitorios Huelin').\n"
    "- FUENTES Y ENLACES REPRESENTATIVOS: En el campo 'sources', proporciona URLs acotadas al micro-barrio específico en Idealista y Fotocasa (ej. 'https://www.idealista.com/venta-viviendas/malaga/carretera-de-cadiz/huelin/' o con filtros de dormitorios/precio si procede). NUNCA proporciones únicamente la URL de macro-distrito genérico si existe la sub-ruta del micro-barrio.\n"
    "- PONDERACIÓN DE DORMITORIOS Y ESTADO: Pondera adecuadamente el número de dormitorios, planta y ascensor. Por ejemplo, 3 o 4 dormitorios en zonas familiares o de alta demanda tienen una prima de liquidez y absorción tanto en venta como en alquiler residencial.\n\n"
    "FORMATO DE SALIDA (EXCLUSIVAMENTE JSON):\n"
    "Debes responder EXCLUSIVAMENTE con un objeto JSON válido, sin texto adicional fuera del bloque JSON.\n"
    "Estructura JSON esperada:\n"
    "{\n"
    '  "sale_range": {"min": 315000, "median": 345000, "max": 380000},\n'
    '  "rent_range": {"min": 1250, "median": 1400, "max": 1600},\n'
    '  "confidence": "HIGH",\n'
    '  "reasoning_factors": [\n'
    '    {"factor_name": "Micro-ubicación Huelin", "impact_percent": 20.0, "description": "Ubicación en barrio cotizado junto al paseo marítimo con precios significativamente superiores a la media del macro-distrito."}\n'
    "  ],\n"
    '  "sources": [\n'
    '    {"title": "Venta viviendas en Huelin, Málaga - Idealista", "url": "https://www.idealista.com/venta-viviendas/malaga/carretera-de-cadiz/huelin/", "price": 345000, "surface_m2": 80}\n'
    "  ],\n"
    '  "raw_notes": "Análisis específico del micro-barrio..."\n'
    "}\n"
)


def build_search_prompt(
    address: Address,
    surface_m2: int,
    property_type: PropertyType,
    bedrooms: int | None,
) -> str:
    return (
        f"Busca anuncios activos y precios reales en Idealista y Fotocasa de viviendas en venta y alquiler en "
        f"{address.street}, {address.city} (CP: {address.postal_code}, País: {address.country}). "
        f"Detalla los inmuebles comparables encontrados para {property_type.value} de {surface_m2} m2, "
        f"{bedrooms if bedrooms is not None else ''} dormitorios, sus precios de venta y rentas de alquiler, superficies en m2 y características principales."
    )


def build_direct_prompt(
    address: Address,
    surface_m2: int,
    property_type: PropertyType,
    bedrooms: int | None,
    bathrooms: int | None,
    floor: int | None,
    has_elevator: bool | None,
    condition: PropertyCondition | None,
) -> str:
    return (
        f"Por favor, calcula la estimación de venta y alquiler para el siguiente inmueble:\n"
        f"- Tipología: {property_type.value}\n"
        f"- Dirección: {address.street}, {address.city} (CP: {address.postal_code}, País: {address.country})\n"
        f"- Superficie: {surface_m2} m2\n"
        f"- Dormitorios: {bedrooms if bedrooms is not None else 'No especificado'}\n"
        f"- Baños: {bathrooms if bathrooms is not None else 'No especificado'}\n"
        f"- Planta: {floor if floor is not None else 'No especificada'}\n"
        f"- Ascensor: {'Sí' if has_elevator is True else ('No' if has_elevator is False else 'Desconocido')}\n"
        f"- Estado de conservación: {condition.value if condition else 'No especificado'}\n\n"
        "Instrucciones específicas:\n"
        "1. Determina el micro-barrio exacto o zona de influencia de la dirección indicada.\n"
        "2. Estima los valores de mercado y referencias en Idealista o Fotocasa."
    )


def build_grounded_calculation_prompt(
    raw_text: str,
    property_type: PropertyType,
    address: Address,
    surface_m2: int,
    bedrooms: int | None,
    bathrooms: int | None,
    floor: int | None,
    has_elevator: bool | None,
    condition: PropertyCondition | None,
    verified_urls: list[str],
) -> str:
    prompt = (
        "Eres un tasador inmobiliario senior experto en el mercado inmobiliario de España.\n"
        "Basándote ESTRICTAMENTE en las siguientes ofertas y datos reales de mercado recopilados en directo de la zona:\n\n"
        "--- TESTIGOS Y ANUNCIOS REALES ENCONTRADOS EN LA ZONA ---\n"
        f"{raw_text}\n"
        "---------------------------------------------------------\n\n"
        "Calcula la tasación y estimación de mercado para este inmueble concreto:\n"
        f"- Tipología: {property_type.value}\n"
        f"- Dirección: {address.street}, {address.city} (CP: {address.postal_code}, País: {address.country})\n"
        f"- Superficie: {surface_m2} m2\n"
        f"- Dormitorios: {bedrooms if bedrooms is not None else 'No especificado'}\n"
        f"- Baños: {bathrooms if bathrooms is not None else 'No especificado'}\n"
        f"- Planta: {floor if floor is not None else 'No especificada'}\n"
        f"- Ascensor: {'Sí' if has_elevator is True else ('No' if has_elevator is False else 'Desconocido')}\n"
        f"- Estado de conservación: {condition.value if condition else 'No especificado'}\n\n"
    )
    if verified_urls:
        prompt += (
            "Enlaces reales verificados de la búsqueda (utiliza estos enlaces en el array 'sources'):\n"
            + "\n".join(f"- {u}" for u in verified_urls[:6])
            + "\n\n"
        )
    prompt += (
        "FORMATO DE SALIDA (EXCLUSIVAMENTE JSON):\n"
        "Debes responder con un objeto JSON válido con la siguiente estructura:\n"
        "{\n"
        '  "sale_range": {"min": ..., "median": ..., "max": ...},\n'
        '  "rent_range": {"min": ..., "median": ..., "max": ...},\n'
        '  "confidence": "HIGH",\n'
        '  "reasoning_factors": [\n'
        '    {"factor_name": "...", "impact_percent": 0.0, "description": "..."}\n'
        "  ],\n"
        '  "sources": [\n'
        '    {"title": "...", "url": "...", "price": ..., "surface_m2": ...}\n'
        "  ],\n"
        '  "raw_notes": "..."\n'
        "}\n"
    )
    return prompt
