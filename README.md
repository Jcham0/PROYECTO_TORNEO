# 🎮 Torneo de videojuegos

Aplicación web desarrollada con **Django** para organizar torneos de videojuegos: inscripciones de participantes, registro de resultados, clasificación pública y gráficas estadísticas.

![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2%20LTS-092E20?logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-06B6D4?logo=tailwindcss&logoColor=white)
![Tests](https://img.shields.io/badge/tests-82%20passing-brightgreen)

---

## 📑 Índice

- [Descripción](#-descripción)
- [Funcionalidades](#-funcionalidades)
- [Tecnologías](#-tecnologías)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Cuentas de demostración](#-cuentas-de-demostración)
- [Rutas principales](#-rutas-principales)
- [Modelo de datos](#-modelo-de-datos)
- [Pruebas](#-pruebas)
- [Notas importantes](#-notas-importantes)
- [Documentación](#-documentación)
- [Autor](#-autor)

---

## 📌 Descripción

El proyecto permite gestionar el ciclo completo de un torneo: los participantes se registran, se inscriben en los torneos que tienen las inscripciones abiertas, el personal registra los resultados y cualquier visitante puede consultar la clasificación y las gráficas de cada torneo.

La clasificación y las estadísticas **se calculan en memoria a partir de los resultados**; no se guardan datos duplicados en la base de datos.

## ✨ Funcionalidades

| Rol | Qué puede hacer |
|---|---|
| **Visitante** | Registrarse, iniciar sesión, consultar la clasificación pública y las gráficas de puntos y victorias por torneo. |
| **Participante** | Acceder a su zona privada, ver sus inscripciones, apuntarse o darse de baja de torneos con inscripciones abiertas. Solo ve y modifica sus propios datos. |
| **Personal del sitio** | Registrar resultados mediante un formulario que aplica las validaciones del modelo. |
| **Administrador** | Gestionar juegos, participantes, torneos, inscripciones y resultados desde el panel `/admin/`, incluido abrir o cerrar las inscripciones de cada torneo. |

**Reglas de clasificación:** 3 puntos por victoria, 1 por empate y 0 por derrota. Se ordena por puntos, después por victorias y después por nick.

## 🛠️ Tecnologías

| Tecnología | Uso |
|---|---|
| **Python 3.14** | Lenguaje de programación. |
| **Django 5.2 LTS** | Framework web: ORM, rutas, autenticación y panel de administración. |
| **SQLite** | Base de datos local incluida con Python. |
| **Matplotlib 3.11.2** | Gráficas PNG generadas en el servidor (backend `Agg`), sin JavaScript. |
| **Tailwind CSS (CDN)** | Diseño responsive para móvil y escritorio. |

## 📋 Requisitos

- Python 3.14 (versión con la que se ha desarrollado y probado el proyecto).
- SQLite, incluido con Python.
- Conexión a internet al usar la web, porque Tailwind CSS se carga por CDN.

## 🚀 Instalación

**1. Clona el repositorio**

```bash
git clone https://github.com/Jcham0/PROYECTO_TORNEO.git
cd PROYECTO_TORNEO
```

**2. Crea y activa el entorno virtual**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

En Windows (PowerShell):

```powershell
.\.venv\Scripts\activate
```

**3. Instala las dependencias**

```bash
pip install -r requirements.txt
```

**4. Aplica las migraciones**

```bash
python manage.py migrate
```

**5. (Opcional) Carga datos de demostración**

```bash
python manage.py poblar_datos
```

El comando es seguro de repetir: no borra información ni duplica los datos. Crea dos juegos, dos torneos, cuatro participantes inscritos en ambos torneos y resultados variados de tres jornadas.

**6. Crea una cuenta de administrador**

```bash
python manage.py createsuperuser
```

**7. Arranca el servidor**

```bash
python manage.py runserver
```

Abre <http://127.0.0.1:8000/> en el navegador.

## 👤 Cuentas de demostración

Si has ejecutado `poblar_datos` en una base de datos nueva, se crean estas cuentas de participante:

| Usuario | Nick |
|---|---|
| `demo_ana` | DemoAna |
| `demo_bruno` | DemoBruno |
| `demo_carla` | DemoCarla |
| `demo_diego` | DemoDiego |

**Contraseña:** `DemoTorneo2026!`

> ⚠️ Solo se asigna al crear una cuenta demo nueva (el comando no cambia contraseñas de cuentas existentes). Son credenciales para desarrollo local: no las uses en producción ni las reutilices en otros servicios.

## 🧭 Rutas principales

| Ruta | Acceso | Descripción |
|---|---|---|
| `/` | Público | Página de inicio. |
| `/registro/` | Público | Registro de nuevos participantes. |
| `/login/` · `/logout/` | Público / sesión | Inicio y cierre de sesión. |
| `/clasificacion/` | Público | Clasificación por torneo. |
| `/graficas/` | Público | Gráficas de puntos y victorias por torneo. |
| `/zona/` | Participante | Inscripciones propias y torneos abiertos. |
| `/resultados/nuevo/` | Personal | Formulario para registrar resultados. |
| `/admin/` | Administrador | Panel de administración de Django. |

## 🗄️ Modelo de datos

La aplicación tiene seis modelos propios:

| Modelo | Descripción |
|---|---|
| `Juego` | Videojuego del torneo (nombre único, descripción y reglas). |
| `Participante` | Perfil del jugador: nick único y nivel (`amateur`, `normal`, `expert`). Relación uno a uno con el usuario de Django. |
| `Torneo` | Torneo con descripción y estado de inscripciones (abiertas o cerradas). |
| `Inscripcion` | Relaciona un participante con un torneo; no permite duplicados. |
| `Enfrentamiento` | Partida entre dos participantes de un juego, con ganador opcional y vínculo opcional con un `Resultado`. |
| `Resultado` | Marcador entre dos inscripciones de un torneo; calcula el ganador y los puntos de clasificación. |

El diagrama entidad-relación completo y el detalle de cada relación están en la [memoria del proyecto](MEMORIA.md).

## ✅ Pruebas

El proyecto incluye **82 pruebas** (unitarias y de integración) que cubren modelos, formularios, vistas públicas, permisos, administración y gráficas.

```bash
python manage.py test
```

Comprobaciones adicionales:

```bash
python manage.py check
python manage.py makemigrations --check
```

## ⚠️ Notas importantes

- **Entorno de desarrollo:** la configuración por defecto está pensada para `localhost` y `127.0.0.1`, sin HTTPS forzado.
- **Producción:** `SECRET_KEY` y `ALLOWED_HOSTS` deben definirse como variables de entorno. Con `DEBUG=False` se exige una clave fuerte y hosts explícitos, y se activan la redirección a HTTPS y las cookies seguras. HSTS se habilita aparte con `SECURE_HSTS_SECONDS`, solo cuando el sitio se sirva siempre por HTTPS.
- **Tailwind CSS por CDN:** válido para desarrollo; para producción conviene compilar el CSS.
- **Base de datos:** SQLite es suficiente para uso local; PostgreSQL sería la alternativa para despliegues con mucha concurrencia.

<!--
## 📸 Capturas de pantalla

Sube las imágenes a una carpeta docs/img/ y quita las marcas de comentario de esta sección:

| Clasificación | Gráficas |
|---|---|
| ![Clasificación](docs/img/clasificacion.png) | ![Gráficas](docs/img/graficas.png) |

| Zona del participante | Panel de administración |
|---|---|
| ![Zona](docs/img/zona.png) | ![Admin](docs/img/admin.png) |
-->

## 📚 Documentación

La [memoria del proyecto](MEMORIA.md) recoge el modelo de datos, los requisitos funcionales, las rutas, los criterios de acceso y los retos técnicos resueltos.

## ✍️ Autor

Desarrollado por **[Jcham0](https://github.com/Jcham0)** como proyecto del curso de Python y Django.
