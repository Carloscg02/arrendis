# Aprendizaje 02: Fundamentos de Bases de Datos y SQLite

Esta guía explica de forma sencilla qué es una base de datos, cómo se estructura y cómo funciona la implementación con **SQLite** en nuestro proyecto de Gestión de Alquileres.

---

## 1. ¿Qué es una Base de Datos y por qué la necesitamos?

Imagínate que para guardar las propiedades de nuestra aplicación usáramos un archivo de texto común (`propiedades.txt`). Cada vez que añadimos una propiedad, escribimos una línea:

```text
id: 1, nombre: Piso Centro, precio: 800
id: 2, nombre: Chalet Playa, precio: 1200
```

Esto funciona al principio, pero rápidamente surgen problemas graves:
1. **Búsquedas Lentas**: Si tenemos 10,000 propiedades y queremos buscar una por su código postal, tendríamos que leer el archivo línea por línea de arriba a abajo.
2. **Concurrencia (Choques)**: Si dos usuarios intentan guardar una propiedad al mismo tiempo, uno podría sobrescribir el archivo del otro y perder los datos.
3. **Relaciones Complejas**: ¿Cómo asociamos los cobros de alquiler (ingresos) a cada propiedad sin duplicar datos?

Una **Base de Datos** es un software optimizado para resolver todos estos problemas. Permite almacenar millones de datos de forma segura, rápida y con relaciones lógicas entre ellos.

---

## 2. Bases de Datos Relacionales

Nuestra aplicación utiliza una **Base de Datos Relacional**. Este modelo organiza la información en **Tablas**, parecidas a hojas de cálculo de Excel.

### Componentes de una Tabla:
*   **Columnas (Campos / Fields)**: Definen el tipo de dato que se guardará (ej: texto, fecha, número).
*   **Filas (Registros / Rows)**: Cada uno de los elementos individuales guardados (ej: una propiedad concreta).

```
Tabla: properties
┌──────────────────────────────┬───────────────┬────────────────────────┐
│ id (Columna)                 │ name          │ property_type          │
├──────────────────────────────┼───────────────┼────────────────────────┤
│ 4a7d... (Fila / Registro)    │ Piso Centro   │ apartment              │
│ 8b2c...                      │ Chalet Playa  │ house                  │
└──────────────────────────────┴───────────────┴────────────────────────┘
```

---

## 3. Las Dos Llaves Maestras: Primary Key y Foreign Key

Para conectar los datos y asegurar que no haya errores, usamos dos conceptos fundamentales:

### A. Llave Primaria (Primary Key - PK)
Es el identificador único de cada registro en una tabla. **No se puede repetir**.
*   En nuestra tabla de propiedades, la PK es la columna `id` (usamos UUIDs como `ef8e67a3-5f4f...` para asegurar que cada propiedad del universo tenga un ID diferente).

### B. Llave Foránea (Foreign Key - FK)
Es una columna en una tabla que hace referencia a la Llave Primaria de **otra tabla**. Así es como "relacionamos" las tablas.

```
 Tabla: properties (Padre)
 ┌──────────────────────┐
 │ PK: id (ej: "PROP-1")│ <────────┐
 └──────────────────────┘          │ (Relación)
                                   │
 Tabla: incomes (Hijo)             │
 ┌──────────────────────┐          │
 │ PK: id               │          │
 │ FK: property_id ─────┼──────────┘ (Apunta a "PROP-1")
 │ amount: 750.00       │
 └──────────────────────┘
```

*   **¿Por qué es útil?** Gracias a la Foreign Key, la base de datos no nos dejará registrar un ingreso para una propiedad que no existe. Esto se llama **Integridad Referencial**.

---

## 4. SQL (Structured Query Language)

Para hablar con la base de datos, usamos un lenguaje universal llamado **SQL**. Hay 4 operaciones básicas (conocidas como **CRUD**: Create, Read, Update, Delete):

1.  **INSERT (Crear)**:
    ```sql
    INSERT INTO properties (id, name, status) VALUES ('1', 'Piso Centro', 'available');
    ```
2.  **SELECT (Leer)**:
    ```sql
    SELECT * FROM properties WHERE status = 'available';
    ```
3.  **UPDATE (Actualizar)**:
    ```sql
    UPDATE properties SET status = 'rented' WHERE id = '1';
    ```
4.  **DELETE (Borrar)**:
    ```sql
    DELETE FROM properties WHERE id = '1';
    ```

---

## 5. Nuestra Implementación con SQLite

En este proyecto, hemos implementado una base de datos relacional usando **SQLite** dentro del archivo `backend/adapters/sqlite_adapter.py`.

### ¿Qué hace especial a SQLite?
A diferencia de bases de datos como PostgreSQL o MySQL, que requieren instalar un servidor complejo en tu ordenador, SQLite es **serverless** (sin servidor). 
*   Todo el motor de base de datos se ejecuta dentro de nuestro propio proceso de Python.
*   Toda la base de datos se guarda en un único archivo local: `data/rental.db`.

### Analizando nuestro código de creación de tablas:

Si miramos el método `_create_tables` de nuestro `SQLiteConnection`, verás cómo se aplica la teoría:

```python
# Tabla de propiedades (properties)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS properties (
        id TEXT PRIMARY KEY,          -- Llave Primaria (PK)
        name TEXT NOT NULL,
        street TEXT NOT NULL,
        city TEXT NOT NULL,
        postal_code TEXT NOT NULL,
        country TEXT NOT NULL,
        property_type TEXT NOT NULL,
        status TEXT NOT NULL
    )
""")

# Tabla de ingresos (incomes)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS incomes (
        id TEXT PRIMARY KEY,          -- Llave Primaria (PK)
        property_id TEXT NOT NULL,    -- Será nuestra Llave Foránea
        amount TEXT NOT NULL,         
        currency TEXT NOT NULL,
        date TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        -- Aquí creamos la relación lógica (FK) hacia la tabla properties:
        FOREIGN KEY (property_id) REFERENCES properties(id)
    )
""")
```

### Un Detalle Técnico Importante de nuestro proyecto:
En SQLite, los números decimales (`float`) pueden perder precisión (ej: `19.99` podría convertirse internamente en `19.9899999999`). Para una aplicación financiera donde gestionamos dinero, esto es inaceptable.

Por eso, verás en nuestro código que guardamos el dinero (`amount`) como **`TEXT`** en SQLite, y cuando lo leemos en Python, lo transformamos a la clase `Decimal` de Python. Así nos aseguramos de que no se pierda ni un céntimo en los redondeos.
