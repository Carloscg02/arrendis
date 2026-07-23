"""
Router de Properties — endpoints CRUD para propiedades.

Traduce peticiones HTTP a llamadas de Casos de Uso (CreateProperty, ListProperties)
y formatea las respuestas como PropertyResponse.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from backend.adapters.sqlite_adapter import SQLiteConnection, SQLitePropertyRepository
from backend.api.dependencies import get_db, get_property_repo
from backend.api.schemas import AddressSchema, PropertyCreate, PropertyResponse
from backend.application.use_cases import CreatePropertyUseCase, ListPropertiesUseCase
from backend.domain.entities import Property

router = APIRouter(prefix="/api/properties", tags=["properties"])


def _entity_to_response(prop: Property) -> PropertyResponse:
    """Convierte una entidad Property del dominio a un schema de respuesta."""
    image_url = f"/api/images/{prop.image_filename}" if prop.image_filename else None
    return PropertyResponse(
        id=prop.id,
        name=prop.name,
        address=AddressSchema(
            street=prop.address.street,
            city=prop.address.city,
            postal_code=prop.address.postal_code,
            country=prop.address.country,
        ),
        property_type=prop.property_type.value,
        status=prop.status.value,
        image_url=image_url,
    )


@router.post("", response_model=PropertyResponse, status_code=201)
def create_property(
    body: PropertyCreate,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
) -> PropertyResponse:
    """Crea una nueva propiedad."""
    try:
        use_case = CreatePropertyUseCase(property_repo)
        prop = use_case.execute(
            name=body.name,
            street=body.address.street,
            city=body.address.city,
            postal_code=body.address.postal_code,
            country=body.address.country,
            property_type=body.property_type,
        )
        return _entity_to_response(prop)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[PropertyResponse])
def list_properties(
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
) -> list[PropertyResponse]:
    """Lista todas las propiedades registradas."""
    use_case = ListPropertiesUseCase(property_repo)
    properties = use_case.execute()
    return [_entity_to_response(p) for p in properties]


@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(
    property_id: str,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
) -> PropertyResponse:
    """Obtiene una propiedad por su ID."""
    prop = property_repo.find_by_id(property_id)
    if prop is None:
        raise HTTPException(
            status_code=404,
            detail=f"Property '{property_id}' not found",
        )
    return _entity_to_response(prop)


@router.delete("/{property_id}")
def delete_property(
    property_id: str,
    property_repo: SQLitePropertyRepository = Depends(get_property_repo),
) -> dict[str, str]:
    """Elimina una propiedad por su ID."""
    property_repo.delete(property_id)
    return {"detail": f"Property '{property_id}' deleted"}


@router.post("/{property_id}/image", response_model=PropertyResponse)
async def upload_property_image(
    property_id: str,
    file: UploadFile = File(...),
    db: SQLiteConnection = Depends(get_db),
) -> PropertyResponse:
    """Sube o actualiza la foto de una propiedad."""
    prop_repo = SQLitePropertyRepository(db)
    prop = prop_repo.find_by_id(property_id)
    if not prop:
        raise HTTPException(status_code=404, detail=f"Property '{property_id}' not found")
    
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Solo se permiten archivos JPG o PNG")
    
    # Validate file size (5MB max)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo no puede superar 5 MB")
    
    # Determine extension
    ext = "jpg" if file.content_type == "image/jpeg" else "png"
    filename = f"{property_id}.{ext}"
    
    # Delete old image if exists
    if prop.image_filename:
        old_path = Path("data/images") / prop.image_filename
        if old_path.exists():
            old_path.unlink()
            
    # Save file
    images_dir = Path("data/images")
    images_dir.mkdir(parents=True, exist_ok=True)
    (images_dir / filename).write_bytes(contents)
    
    # Update database
    prop_repo.update_image(property_id, filename)
    
    # Return updated property
    updated = prop_repo.find_by_id(property_id)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Property '{property_id}' not found after update")
    return _entity_to_response(updated)
