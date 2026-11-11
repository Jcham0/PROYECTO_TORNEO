# Torneo de videojuegos

## Requisitos previos

- Python 3.14.
- SQLite, incluido con Python.

## Entorno virtual

Si todavía no existe `.venv`, créalo desde la raíz del proyecto:

```bash
python3 -m venv .venv
```

Actívalo antes de ejecutar los comandos del proyecto:

```bash
source .venv/bin/activate
```

En Windows, usa:

```powershell
.\.venv\Scripts\activate
```

## Instalación

Con el entorno virtual activado, instala las dependencias registradas:

```bash
pip install -r requirements.txt
```

## Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

La migración añade el vínculo opcional entre `Enfrentamiento` y `Resultado`.
Los enfrentamientos anteriores quedan sin resultado; no se asignan resultados
existentes automáticamente.

## Datos de prueba

Después de aplicar las migraciones, crea o actualiza los datos de demostración
con:

```bash
python manage.py poblar_datos
```

El comando es seguro de repetir: no borra información y evita duplicar los
datos demo. Crea dos juegos, dos torneos, cuatro participantes inscritos en
ambos torneos y resultados variados de tres jornadas.

En una base de datos nueva, las cuentas de participante comparten esta
contraseña:

| Usuario | Nick |
|---|---|
| `demo_ana` | DemoAna |
| `demo_bruno` | DemoBruno |
| `demo_carla` | DemoCarla |
| `demo_diego` | DemoDiego |

Contraseña: `DemoTorneo2026!`. Solo se asigna al crear una cuenta demo nueva;
el comando no cambia la contraseña de cuentas que ya existan. Son credenciales
para desarrollo local: no las uses en producción. Para acceder al panel como
administrador, crea una cuenta independiente con `python manage.py createsuperuser`.

### Acceso del profesor al panel de administración

Panel: <http://127.0.0.1:8000/admin/>

- **Usuario:** `JuanAntonio`
- **Contraseña:** `Juanito7,.,.`

Estas credenciales corresponden al entorno de evaluación del curso. No las
reutilices en producción ni en otros servicios.

## Arranque del servidor

```bash
python manage.py runserver
```

Abre <http://127.0.0.1:8000/> para ver la página inicial del proyecto.