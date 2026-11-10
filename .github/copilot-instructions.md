# Instrucciones del agente

## Antes de empezar cualquier tarea
- Lee `PROJECT_LOG.md` (bloque "Contrato actual" y última entrada) y los archivos reales relacionados con la tarea: `models.py`, `urls.py`, `views.py`, `forms.py` y las plantillas de las apps afectadas.
- Usa solo nombres que existan en el código: modelos, campos, vistas, URLs y plantillas. No los supongas ni los recuerdes de memoria.
- Antes de escribir código nuevo, muéstrame una lista breve de los nombres que vas a usar, indicando en qué archivo has comprobado cada uno.
- Si vas a referenciar un campo o un método, ábrelo y verifica su nombre exacto y su tipo; no lo deduzcas por el nombre del modelo.
- Si falta algo que necesitas, no lo inventes: dime qué falta y lo creamos primero.
- Si lo que dice el log no coincide con el código, manda el código y avísame de la diferencia.
- Los cambios de modelo (añadir o modificar campos) van en un paso aparte, con su migración, antes de construir vistas o plantillas encima.
- Si dudas de la sintaxis de Django o Python, dímelo en lugar de adivinarla.
## 1. Contexto del proyecto
- Proyecto final de Python: aplicación web de torneo de videojuegos
- Stack: Python, Django, ORM de Django y SQLite.
- Soy principiante en la sintaxis de Python y Django. Quiero entender el código, no solo recibirlo.

## 2. Tecnologías y estándares de código
- Usa la última versión LTS de Django y una versión estable de Python compatible con ella.
- Consulta y aplica siempre patrones y sintaxis de la documentación oficial más reciente de Python y Django.
- Sigue estrictamente PEP 8 (nombres, sangría e importaciones).
- Usa codificación UTF-8 en todos los ficheros.
- Estándar de comentarios en el código: No satures el código con comentarios didácticos u obvios sobre la sintaxis básica de Python o Django (como explicar qué hace un CharField o un return). Utiliza únicamente docstrings descriptivos en clases y métodos, y comentarios breves y técnicos exclusivamente cuando sea necesario justificar decisiones de diseño o lógica de negocio compleja.
- Fechas y horas: usa siempre los campos de fecha de Django (`DateField`, `DateTimeField`) y `django.utils.timezone.now()` en lugar de `datetime.now()`. Configura `LANGUAGE_CODE = "es"`, `TIME_ZONE = "Europe/Madrid"` y `USE_TZ = True`. Muestra las fechas al usuario en formato día/mes/año (DD/MM/AAAA) y guárdalas siempre en la base de datos y en los fixtures en formato estándar (AAAA-MM-DD). En la bitácora y la documentación usa también DD/MM/AAAA.
- Configuración de aplicaciones: Cada vez que se cree una nueva app en el proyecto, asegúrate de registrarla inmediatamente en `INSTALLED_APPS` dentro de `settings.py` antes de avanzar a los modelos o rutas.
- No cambies la versión de Django ya instalada sin preguntarme. Usa solo APIs de esa versión.

## 3. Forma de explicar
- Explica brevemente cada bloque de código nuevo: qué hace y por qué se hace así.
- Usa un lenguaje sencillo y evita dar por hecho que conozco la sintaxis.
- No instales paquetes, no cambies la estructura del proyecto ni borres archivos sin preguntarme antes.

## 4. Flujo de trabajo por fases
- Trabaja por fases pequeñas e iterativas.
- Antes de programar una funcionalidad importante, propón un plan breve paso a paso y espera mi validación.
- Verificación y pruebas: al terminar cada parte importante (modelos, permisos de acceso, CRUD, cálculo de rankings, gráficas), escribe automáticamente un test sencillo en `tests.py` con `django.test.TestCase`, sin esperar a que te lo pida. Después ejecútalo con `python manage.py test`, explícame cómo comprobarlo también a mano en el navegador y no des la fase por terminada hasta que ambas pruebas pasen.
- Sincronización de archivos: Cuando se escriban pruebas automatizadas (tests.py) que dependan de cambios en otras partes del código (como admin.py, views.py o forms.py), la IA debe entregar de forma obligatoria y simultánea el código completo de todos los archivos implicados ya sincronizados, para evitar que las pruebas fallen por código pendiente de implementar
- Al terminar cada fase, revisa y elimina imports sin usar, variables huérfanas, código muerto y comentarios desactualizados.
- **Integración obligatoria en menús (`base.html`):** Cada vez que se cree una nueva vista pública o protegida accesible mediante URL con nombre, la IA debe actualizar automáticamente la barra de navegación en `base.html` para incluir su correspondiente enlace (condicionando con `{% if user.is_authenticated %}` si es una zona privada), evitando que el usuario tenga que escribir la URL manualmente en el navegador.
- Fixtures: no los generes hasta que `models.py` esté totalmente definido y las migraciones aplicadas. Entonces crea un fixture JSON de datos de prueba y guárdalo como archivo permanente del proyecto cargable en otro equipo con `loaddata`, y regéneralo si cambian los modelos.
- Además de `python manage.py test`, ejecuta `python manage.py check` y `python manage.py makemigrations --check` al terminar cada fase.
- Si un test falla, corrige el código, no el test, salvo que me expliques por qué el test estaba mal.
- Numeración de fases: usa siempre este mapa, de 1 a 11, en el log, la
  memoria y los mensajes: 1 Entorno y esqueleto, 2 Modelos, 3 Cuentas y
  acceso, 4 Juegos (admin), 5 Participantes (admin), 6 Zona del participante,
  7 Resultados y rankings, 8 Gráficas, 9 Datos de prueba, 10 Pruebas y
  limpieza, 11 Documentación final. No uses otra numeración.
- Si una fase se divide en pedidos, etiquétalos como "Fase N, pedido X de Y".

## 5. Documentación del proyecto
Mantén estos archivos en la raíz del proyecto. Añade los cambios sin borrar el contenido anterior que siga siendo válido.

### README.md (manual técnico y de usuario)
Actualiza solo: requisitos previos, creación y activación del entorno virtual, instalación (`pip install -r requirements.txt`), migraciones (`makemigrations` / `migrate`) carga de datos de prueba (`loaddata`, indicando las credenciales de prueba)y arranque del servidor (`python manage.py runserver`).

### MEMORIA.md (explicación académica para el profesor)
- Documenta la lógica del proyecto paso a paso, el diseño de las tablas (modelos), las vistas y rutas, y la resolución de errores o retos técnicos.
- Sigue la estructura que pide el profesor: portada, índice, descripción, objetivos y alcance, stack y alternativas, modelo de datos y requisitos.
- Cada requisito funcional debe ser 100 % operativo e indicar: actor, acción y respuesta del sistema.
- Incluye una sección "Manual de instalación" basada en el README.md; mantenla coherente con él, sin duplicar el trabajo de redacción.
- Al cerrar cada fase, revisa que la Descripción, el índice, los requisitos y
  "Vistas y rutas" reflejen el estado real del proyecto y usen la numeración
  del mapa de fases.

### PROJECT_LOG.md (bitácora de desarrollo)
Añade entradas cronológicas, con fecha o hito, indicando: funcionalidades programadas, librerías añadidas e incidencias resueltas en cada sesión.
- Al principio del archivo mantén un bloque fijo "Contrato actual" con los modelos y sus campos, las URLs, las vistas y las plantillas vigentes. Actualízalo al terminar cada fase, comprobándolo contra el código real.
- Cada entrada debe terminar con "Siguiente paso pendiente".

## 6. Dependencias (requirements.txt)
- Este archivo lista solo las librerías de Python del proyecto, con nombre y versión.
- Cada vez que se instale un paquete nuevo, actualiza `requirements.txt` automáticamente, sin que yo te lo pida, y guárdalo en UTF-8.

