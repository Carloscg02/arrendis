# Especificación F-05: Fotos de Propiedades y Rediseño de Tarjetas

## 1. Visión General

Añadir la posibilidad de subir una foto por propiedad y rediseñar las tarjetas del listado principal para que ocupen **una fila completa** con la foto integrada lateralmente mediante un gradiente de fusión (Opción A aprobada).

**Alcance:** Full-stack (Dominio → Persistencia → API → Frontend).

---

## 2. Lenguaje Ubicuo

| Término | Definición |
|---|---|
| **Image Upload** | Proceso de enviar un archivo JPG/PNG desde el frontend al backend mediante `multipart/form-data` |
| **Static File Serving** | Servir archivos de imagen almacenados en disco directamente por FastAPI, sin pasar por la lógica de negocio |
| **Gradient Bleed** | Técnica CSS donde un gradiente oscuro se superpone al borde de la foto para que se funda suavemente con el fondo de la tarjeta |
| **Property Card (Full-Width)** | Nueva tarjeta horizontal (1 por fila) que reemplaza la cuadrícula de 3 columnas |

---

## 3. Cambios en el Dominio

### 3.1 Entidad `Property` — Nuevo campo

```python
# backend/domain/entities.py
@dataclass
class Property:
    name: str
    address: Address
    property_type: PropertyType
    status: PropertyStatus = PropertyStatus.AVAILABLE
    image_filename: str | None = None          # ← NUEVO (opcional)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
```

- `image_filename` almacena solo el nombre del archivo (ej: `abc123.jpg`), NO la ruta completa.
- Es `None` si la propiedad no tiene foto.
- El campo NO participa en la igualdad de la entidad (basada solo en `id`).

### 3.2 Puerto `PropertyRepository` — Nuevo método

```python
# backend/domain/ports.py
class PropertyRepository(ABC):
    # ... métodos existentes ...
    
    @abstractmethod
    def update_image(self, property_id: str, image_filename: str | None) -> None:
        """Actualiza el nombre de archivo de imagen de una propiedad."""
```

---

## 4. Cambios en Persistencia

### 4.1 SQLite — Migración de esquema

Añadir columna a la tabla existente:

```sql
ALTER TABLE properties ADD COLUMN image_filename TEXT DEFAULT NULL;
```

Implementar en `_create_tables()` como migración segura:
```python
# Después de CREATE TABLE IF NOT EXISTS properties
try:
    cursor.execute("ALTER TABLE properties ADD COLUMN image_filename TEXT DEFAULT NULL")
except sqlite3.OperationalError:
    pass  # La columna ya existe
```

### 4.2 `SQLitePropertyRepository`

- **`save()`**: Incluir `image_filename` en el INSERT/REPLACE.
- **`_row_to_entity()`**: Leer `image_filename` de la fila.
- **`update_image()`**: Nuevo método — `UPDATE properties SET image_filename = ? WHERE id = ?`.

### 4.3 `InMemoryPropertyRepository` (tests)

- Actualizar para soportar el campo `image_filename` en la entidad.
- Implementar `update_image()`.

### 4.4 Almacenamiento de archivos

- Directorio: `data/images/`
- Nombre de archivo: `{property_id}.{extension}` (ej: `a1b2c3d4.jpg`)
- Extensiones permitidas: `.jpg`, `.jpeg`, `.png`
- Tamaño máximo: 5 MB
- Al eliminar una propiedad (`delete`), eliminar también su archivo de imagen si existe.

---

## 5. Cambios en la API

### 5.1 Nuevo Endpoint — Subir Imagen

```
POST /api/properties/{property_id}/image
Content-Type: multipart/form-data
Body: file (UploadFile)

Response 200: PropertyResponse (con image_url actualizado)
Response 404: Property not found
Response 400: Archivo no válido (tipo o tamaño)
```

**Lógica:**
1. Verificar que la propiedad existe.
2. Validar que el archivo es JPG/PNG y < 5 MB.
3. Si la propiedad ya tiene imagen, borrar el archivo anterior.
4. Guardar el archivo en `data/images/{property_id}.{ext}`.
5. Actualizar `image_filename` en la BD.
6. Retornar la propiedad actualizada.

### 5.2 Servir Imágenes Estáticas

En `main.py`, montar un directorio estático:
```python
from fastapi.staticfiles import StaticFiles

# Después de incluir routers
app.mount("/api/images", StaticFiles(directory="data/images"), name="images")
```

### 5.3 Modificar `PropertyResponse`

```python
class PropertyResponse(BaseModel):
    id: str
    name: str
    address: AddressSchema
    property_type: str
    status: str
    image_url: str | None = None    # ← NUEVO: "/api/images/abc123.jpg" o None
```

### 5.4 Modificar conversión Entity → Response

En las rutas de properties, al construir `PropertyResponse`, generar `image_url`:
```python
image_url = f"/api/images/{prop.image_filename}" if prop.image_filename else None
```

---

## 6. Cambios en el Frontend

### 6.1 Tipo `Property` — Nuevo campo

```typescript
// types/index.ts
export interface Property {
  id: string;
  name: string;
  address: Address;
  property_type: string;
  status: string;
  image_url: string | null;     // ← NUEVO
}
```

### 6.2 Servicio API — Nuevo método

```typescript
// services/api.ts
export async function uploadPropertyImage(propertyId: string, file: File): Promise<Property> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/properties/${propertyId}/image`, {
    method: "POST",
    body: formData,     // NO poner Content-Type header — fetch lo genera con boundary
  });
  return handleResponse<Property>(res);
}
```

### 6.3 Rediseño de `PropertyCard` — Layout Full-Width con Foto

**Estructura HTML:**
```
┌─────────────────────────────────────────────────────────────┐
│ ┌──────────────┐                                            │
│ │              │   Piso Centro Madrid          [Disponible] │
│ │    FOTO      │   📍 Calle Gran Vía 42, Madrid             │
│ │  (gradiente) │   [🏢 Apartamento]                         │
│ │              │                                            │
│ └──────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

- La tarjeta usa `display: flex` horizontal.
- Zona de foto: `width: 280px` fija, `height: 160px`, `overflow: hidden`, `border-radius` solo esquinas izquierdas.
- Sobre la foto: un pseudo-elemento `::after` con `background: linear-gradient(to right, transparent 40%, var(--bg-secondary) 100%)` para el efecto de fusión (gradient bleed).
- Sin foto: se muestra un fondo `var(--bg-primary)` con el emoji del tipo de propiedad centrado en grande.
- Zona de contenido: `flex: 1`, `padding: 1.5rem`, información vertical.
- La foto se carga como `background-image` con `background-size: cover` y `background-position: center`.

### 6.4 `PropertyList` — Grid de 1 Columna

```css
.property-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
```

### 6.5 `PropertyDetail` — Botón de Subir Foto

- Añadir un botón "📷 Subir Foto" en la cabecera (junto a "Eliminar Propiedad").
- Al hacer clic, abre un `<input type="file" accept="image/jpeg,image/png">` oculto.
- Preview opcional antes de confirmar.
- Al seleccionar archivo, llama a `uploadPropertyImage()` y recarga los datos.
- Feedback con toast: "Foto subida correctamente" / error.

### 6.6 Responsive (< 768px)

- La tarjeta cambia a layout vertical: foto arriba (full-width, altura fija 120px), contenido debajo.
- El gradiente cambia a vertical (de abajo hacia arriba).

---

## 7. Especificación de Tests

### Tests Unitarios Nuevos

| ID | Qué Verifica |
|---|---|
| **T-01** | La entidad Property se crea correctamente con `image_filename=None` por defecto |
| **T-02** | La entidad Property acepta `image_filename="test.jpg"` |
| **T-03** | `InMemoryPropertyRepository.update_image()` actualiza el campo correctamente |

### Tests de Integración Nuevos

| ID | Qué Verifica |
|---|---|
| **T-04** | `POST /api/properties/{id}/image` con JPG válido → 200, response incluye `image_url` |
| **T-05** | `POST /api/properties/{id}/image` con propiedad inexistente → 404 |
| **T-06** | `POST /api/properties/{id}/image` con archivo no imagen → 400 |
| **T-07** | `GET /api/properties` → response incluye campo `image_url` (null para propiedades sin foto) |
| **T-08** | `DELETE /api/properties/{id}` elimina también el archivo de imagen del disco |

### Verificaciones de Regresión

| ID | Qué Verifica |
|---|---|
| **V-01** | `npm run build` en frontend → exit 0 |
| **V-02** | `pytest tests/ -v` → todos los tests (existentes + nuevos) pasan |
| **V-03** | La UI sigue completamente en español |

### Comandos de Verificación

```bash
# V-01: Build frontend
cd /home/carlos/rental-handler/frontend && npm run build

# V-02: Tests completos
cd /home/carlos/rental-handler && venv/bin/python -m pytest tests/ -v

# V-03: Verificación idioma (manual)
```

---

## 8. Requisitos No Funcionales

- **RN-01:** Las imágenes NO se almacenan en la base de datos (solo el nombre de archivo).
- **RN-02:** Al borrar una propiedad, su imagen se borra del disco.
- **RN-03:** Se aceptan solo JPG/PNG de máximo 5 MB.
- **RN-04:** La subida no bloquea la UI (feedback con toast).
- **RN-05:** La API de imágenes NO requiere modificar `services/api.ts` existente (solo añadir función nueva).

---

## 📚 El Rincón del Estudiante

### ¿Qué es `multipart/form-data` y por qué no podemos enviar una imagen como JSON?

**Analogía:** Imagina que quieres enviar una carta (texto) y una caja (imagen) por correo. JSON es como un sobre: perfecto para la carta, pero intentar meter la caja dentro del sobre la destruiría. `multipart/form-data` es como un paquete: permite enviar la carta Y la caja juntas, cada una empaquetada de forma diferente.

En términos técnicos, JSON codifica todo como texto (strings, números). Para enviar un archivo binario (una imagen de 2 MB) como JSON, tendrías que convertirla a Base64, lo que la haría un 33% más grande y mucho más lenta de procesar. `multipart/form-data` envía el archivo en su formato binario original, separando cada parte del formulario con un "boundary" (un separador único).

### Comparativa: Almacenamiento de imágenes

| Estrategia | Pros | Contras | Nuestro caso |
|---|---|---|---|
| **En la BD (BLOB)** | Todo en un solo lugar | BD crece mucho, backups pesados, lento | ❌ No |
| **En disco + ruta en BD** | Rápido, BD ligera, fácil servir estáticos | Hay que sincronizar borrado | ✅ Elegimos esta |
| **Servicio externo (S3, Cloudinary)** | Escalable, CDN, transformaciones | Dependencia externa, coste | Overkill para nuestro caso |

### ¿Por qué el gradiente y no simplemente recortar la foto?

La técnica de "gradient bleed" (fusión con gradiente) viene del diseño editorial. En vez de tener un borde duro donde la foto termina y el fondo empieza (que se siente como dos piezas pegadas), el gradiente crea una transición imperceptible. Esto hace que la foto se sienta integrada en la tarjeta, no pegada encima.

```css
/* La magia del gradient bleed */
.property-card-image::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(to right, transparent 40%, var(--bg-secondary) 100%);
}
```

El `::after` es un pseudo-elemento invisible que se coloca encima de la foto. Su fondo es un gradiente que va de transparente (deja ver la foto) a oscuro (se funde con la tarjeta). El resultado: una transición orgánica que da sensación de profundidad.

### Ejemplo de código: Entity antes vs. después

| Antes (F-03) | Después (F-05) |
|---|---|
| `Property(name, address, property_type, status, id)` | `Property(name, address, property_type, status, image_filename, id)` |
| El campo `image_filename` no existía | `image_filename: str \| None = None` — opcional, no rompe nada existente |

El `None` por defecto es clave: todas las propiedades existentes en la BD siguen funcionando sin cambios. Esto se llama **retrocompatibilidad** (backward compatibility) y es fundamental cuando modificas entidades en un sistema que ya tiene datos en producción.
