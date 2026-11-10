# Memoria del proyecto

## Portada

- **Título:** Aplicación web para la gestión de un torneo de videojuegos
- **Propuesta:** C
- **Alumno/a:** [Nombre del alumno o alumna]
- **Profesor/a:** [Nombre del profesor o profesora]
- **Fecha:** 03/11/2026

## Índice

1. Descripción
2. Objetivos y alcance
3. Tecnologías y alternativas
4. Modelo de datos
5. Requisitos funcionales
6. Vistas y rutas
7. Criterios de acceso y visibilidad
8. Manual de instalación
9. Retos técnicos e incidencias

## Descripción

El proyecto es una aplicación web Django para organizar torneos de
videojuegos. Incluye modelos de juegos, participantes, torneos, inscripciones,
enfrentamientos y resultados, además de su gestión administrativa, el registro
y la autenticación de participantes. La zona privada permite consultar las
propias inscripciones y apuntarse o darse de baja de torneos que mantienen
abiertas sus inscripciones. El personal puede registrar resultados mediante
un formulario que aplica las validaciones del modelo. La Fase 8 incorpora una
gráfica pública de puntos y otra de victorias por participante para cada
torneo. La interfaz se presenta con un diseño responsive basado en Tailwind CSS.

## Objetivos y alcance

El objetivo es gestionar la información y el desarrollo de torneos de
videojuegos. Las Fases 1 a 6 prepararon el entorno, definieron los modelos,
añadieron cuentas y permisos, habilitaron la gestión administrativa y permitieron
a cada participante gestionar sus inscripciones. La Fase 7 incluye el modelo
`Resultado`, el registro web de resultados y la clasificación pública por
torneo. En la Fase 8 se añaden gráficas generales de puntos y victorias por
participante, seleccionables por torneo y calculadas con la misma clasificación,
sin guardar estadísticas. Las páginas principales usan una presentación
responsive con Tailwind CSS. La Fase 9 incorpora el comando de datos de
demostración. En la Fase 10, una suite de pruebas unitarias y de integración
basadas en `django.test.TestCase` verifica modelos, formularios, vistas públicas,
permisos, administración y gráficas. Queda pendiente la Fase 11 según el mapa
del proyecto.

## Tecnologías y alternativas

- **Python 3.14:** lenguaje de programación.
- **Django 5.2.18 LTS:** framework web con ORM, rutas y herramientas de
  administración integradas.
- **SQLite:** base de datos local incluida con Python, apropiada para iniciar el
  proyecto. PostgreSQL sería una alternativa para despliegues con mayor
  concurrencia.
- **Tailwind CSS por CDN:** utilidades de presentación para adaptar la interfaz
  a móviles y escritorios sin añadir dependencias de Python. Para producción
  conviene compilar el CSS en vez de cargar el CDN de desarrollo.
- **Matplotlib 3.11.2:** generación de gráficas PNG en servidor con el backend
  `Agg`; no se usa JavaScript para dibujar las estadísticas.
- **Comando de gestión de Django:** `python manage.py poblar_datos` crea datos
  repetibles de demostración después de migrar la base de datos.
- **Alternativa web considerada:** Flask ofrece una base más pequeña, mientras
  que Django incluye de serie más componentes necesarios para esta aplicación.

## Modelo de datos

La aplicación tiene seis modelos propios:

| Modelo | Campos principales | Relaciones y comportamiento |
|---|---|---|
| `Juego` | `nombre` único, `descripcion` y `reglas` opcionales | Un juego puede asociarse a varios enfrentamientos. |
| `Participante` | `nick` único y `nivel` (`amateur`, `normal` o `expert`; inicia en `amateur`) | Relación uno a uno con el usuario de Django; el email se guarda en la cuenta. Los puntos no se almacenan en el participante: se calculan desde `Resultado`. |
| `Torneo` | `nombre`, `descripcion` opcional e `inscripciones_abiertas` (inicia en verdadero) | El administrador puede abrir o cerrar las inscripciones. |
| `Inscripcion` | `fecha_inscripcion` automática | Relaciona un participante con un torneo; la base de datos impide duplicar la pareja. |
| `Enfrentamiento` | `fecha` automática y `finalizado` (inicia en falso) | Pertenece a un juego y tiene dos participantes; el ganador es opcional. |
| `Resultado` | `puntos_a`, `puntos_b`, `fecha` y `ronda` | Relaciona dos inscripciones de un torneo; valida que sean participantes distintos y pertenezcan al torneo. Calcula ganador y puntos de clasificación 3/1/0. |

Las claves foráneas de juego y participantes eliminan sus enfrentamientos
relacionados cuando se elimina el registro correspondiente. Si se elimina solo
el ganador, el enfrentamiento se conserva sin ganador. Al borrar un torneo o
participante también se eliminan sus inscripciones relacionadas. Django
mantiene además sus modelos internos de administración, usuarios y sesiones.

## Requisitos funcionales

| Actor | Acción | Respuesta del sistema | Estado |
|---|---|---|---|
| Visitante | Accede a la ruta `/` | La aplicación muestra la página inicial y responde correctamente | Operativo en Fase 1 |
| Visitante | Se registra con nombre de usuario, email válido, nick, nivel y una contraseña válida repetida correctamente | El sistema guarda el email en la cuenta de Django, crea el participante con el nivel elegido, muestra una confirmación y redirige al inicio de sesión | Operativo en Fase 3 |
| Visitante | Envía un registro incompleto o inválido, un usuario, nick o email duplicado, o contraseñas distintas | El formulario muestra los errores y no crea una cuenta | Operativo en Fase 3 |
| Visitante | Envía credenciales válidas desde `/login/` | Django inicia su sesión y redirige al inicio configurado | Operativo en Fase 3 |
| Participante o administrador | Cierra sesión mediante el formulario de navegación | Django procesa el cierre por POST y redirige al inicio | Operativo en Fase 3 |
| Visitante o participante | Accede a `/admin/` o a una lista de gestión del panel | Django lo redirige al inicio de sesión del panel sin mostrar datos de gestión | Operativo en Fase 3 |
| Administrador | Accede a `/admin/` y a las listas de gestión | Django permite el acceso conforme a sus permisos administrativos | Operativo en Fase 3 |
| Administrador | Gestiona cuentas de usuario | La gestión de cuentas se realiza únicamente desde `/admin/`; no existe una pantalla pública para ellas | Criterio de acceso aplicado |
| Visitante | Consulta `/clasificacion/` | El sistema muestra por torneo nick, jugados, ganados, perdidos, empatados y puntos; jugados coincide con la suma de resultados y los puntos son 3 por victoria, 1 por empate y 0 por derrota | Operativo en Fase 7 y corrección verificada |
| Visitante | Consulta `/graficas/` y elige un torneo | El sistema muestra gráficas públicas de puntos y victorias por participante, reutilizando la clasificación; si no hay resultados, muestra avisos claros | Operativo en Fase 8, pedidos 1 y 2 |
| Desarrollador | Ejecuta `python manage.py poblar_datos` después de las migraciones | El comando crea dos torneos, participantes con inscripciones compartidas y resultados variados; puede repetirse sin duplicar ni borrar datos | Operativo en Fase 9 |
| Administrador | Crea un juego desde el panel con nombre, descripción y reglas | El sistema guarda el juego y lo muestra en el listado administrativo | Operativo en Fase 4 |
| Administrador | Consulta, busca y ordena los juegos en el panel | El listado muestra los juegos ordenados por nombre y permite buscarlos por nombre | Operativo en Fase 4 |
| Administrador | Edita los datos de un juego | El sistema guarda los cambios y refleja la información actualizada | Operativo en Fase 4 |
| Administrador | Intenta crear un juego con un nombre ya utilizado | El formulario rechaza el duplicado y conserva un único juego con ese nombre | Operativo en Fase 4 |
| Administrador | Elimina un juego desde el panel | El juego se elimina y, por la relación en cascada, también sus enfrentamientos asociados | Operativo en Fase 4 |
| Visitante o participante | Intenta consultar o modificar juegos mediante la gestión administrativa | Django redirige al login del panel y no permite listar, crear, editar ni eliminar juegos | Operativo en Fase 4 |
| Administrador | Consulta la lista de participantes en el panel | El sistema muestra usuario, nick, nivel y email de la cuenta vinculada, ordenados por nick | Actualizado |
| Administrador | Busca participantes por nick o nombre de usuario | El panel muestra los perfiles que coinciden con la búsqueda | Operativo en Fase 5 |
| Administrador | Edita el nick, nivel o email de un participante | El sistema guarda el nivel en el participante y el email en la cuenta de Django, rechazando emails duplicados | Actualizado |
| Visitante o participante | Envía una solicitud directa para crear, editar o eliminar participantes | Django responde con redirección 302 al login del panel y los datos permanecen sin cambios | Operativo en Fase 5 |
| Visitante | Accede a `/zona/` sin iniciar sesión | Django redirige al formulario de inicio de sesión | Operativo en Fase 6 |
| Participante | Consulta su zona privada | El sistema muestra sus inscripciones y los torneos abiertos disponibles, sin exponer inscripciones de otras personas | Operativo en Fase 6 |
| Participante | Se apunta a un torneo abierto | El sistema crea su inscripción y evita duplicados | Operativo en Fase 6 |
| Participante | Se da de baja de un torneo abierto | El sistema elimina su inscripción | Operativo en Fase 6 |
| Participante | Intenta apuntarse o darse de baja de un torneo cerrado | El sistema conserva los datos y comunica que las inscripciones están cerradas | Operativo en Fase 6 |
| Cuenta autenticada sin perfil de participante | Intenta gestionar inscripciones | El sistema muestra un aviso y rechaza las solicitudes POST con HTTP 403 | Operativo en Fase 6 |
| Personal del sitio | Registra un resultado con torneo, dos inscripciones, marcadores y ronda | El `ModelForm` valida los datos mediante `Resultado.clean()`, guarda el resultado y muestra una confirmación; la fecha usa el valor predeterminado del modelo | Operativo en Fase 7 |
| Personal del sitio | Envía un resultado inválido, con participantes repetidos o una inscripción de otro torneo | El formulario conserva los datos, muestra el error en el campo correspondiente y no guarda el resultado | Operativo en Fase 7 |
| Visitante o participante | Intenta acceder a `/resultados/nuevo/` | La vista redirige al inicio de sesión del panel y no permite crear resultados | Operativo en Fase 7 |
| Cualquier visitante | Consulta la clasificación de torneos | El sistema calcula las estadísticas en memoria a partir de resultados, usa las properties del modelo y no persiste cambios | Operativo en Fase 7 |

Los requisitos de las demás funcionalidades del torneo se incorporarán cuando
se definan y verifiquen en sus fases.

## Vistas y rutas

- `/`: la vista `torneo.views.inicio` muestra la página inicial a cualquier
  visitante, participante o administrador.
- `/clasificacion/`: la vista pública `torneo.views.clasificacion` calcula y
  muestra una clasificación independiente por torneo a partir de los
  resultados existentes. Ordena por puntos descendentes, victorias
  descendentes y nick ascendente, sin guardar estadísticas.
- `/graficas/`: la vista pública `torneo.views.graficas` permite elegir un
  torneo y muestra sus puntos por participante. Al abrir la página, selecciona
  el primer torneo por nombre.
- `/graficas/torneo/<int:torneo_id>.png`: la vista pública
  `torneo.views.grafica_torneo` genera la imagen PNG de barras del torneo
  seleccionado. La plantilla la muestra mediante `<img>`; si no hay resultados,
  la página explica esa situación y la ruta de imagen también responde con un
  PNG informativo.
- `/graficas/torneo/<int:torneo_id>/victorias.png`: la vista pública
  `torneo.views.grafica_victorias_torneo` genera la gráfica comparativa de
  victorias por participante, reutilizando el resultado calculado en la
  clasificación. La plantilla la enlaza mediante `<img>` y avisa cuando el
  torneo aún no tiene resultados.
- `/registro/`: la vista `torneo.views.registro_participante` no exige iniciar
  sesión. Valida los datos, crea la cuenta y su participante asociados,
  muestra un mensaje de confirmación y redirige al login.
- `/login/`: la vista `django.contrib.auth.views.LoginView` muestra el
  formulario de acceso y autentica a quien presenta credenciales válidas.
- `/logout/`: la vista `django.contrib.auth.views.LogoutView` cierra la sesión
  mediante una solicitud POST y redirige al inicio. La navegación ofrece este
  formulario a usuarios con sesión.
- `/zona/`: la vista protegida `torneo.views.zona_participante` muestra las
  inscripciones del participante autenticado y los torneos disponibles. Sus
  formularios POST permiten apuntarse o darse de baja mientras el torneo tenga
  abiertas sus inscripciones.
- `/resultados/nuevo/`: la vista `torneo.views.registrar_resultado`, protegida
  para el personal del sitio, muestra `ResultadoForm`. Al enviarlo, el
  `ModelForm` ejecuta la validación del modelo `Resultado`, muestra los errores
  junto a sus campos o guarda el resultado y confirma la operación.
- `/admin/`: `django.contrib.admin.site.urls` atiende el panel de Django.
  Las cuentas anónimas y las cuentas sin acceso administrativo son enviadas
  al login del panel; el personal con los permisos requeridos puede consultar
  y gestionar los modelos autorizados.
- `/admin/auth/user/`: la lista de cuentas de usuario del panel; requiere
  iniciar sesión en el admin y tener los permisos correspondientes. La gestión
  de cuentas se realiza únicamente desde aquí.
- `/admin/torneo/juego/` y sus rutas de alta, edición y borrado: las atiende
  `JuegoAdmin` del panel. Requieren acceso administrativo y permiten listar,
  buscar por nombre, ordenar, crear, editar y eliminar juegos; borrar uno
  elimina también sus enfrentamientos asociados.
- `/admin/torneo/participante/` y sus rutas de alta, edición y borrado: las
  atiende `ParticipanteAdmin` del panel. Requieren permisos administrativos y
  permiten listar usuario, nick y puntos, buscar por nick o nombre de usuario,
  ordenar por nick y editar el perfil.
- `/admin/torneo/torneo/`: la vista `TorneoAdmin` permite crear y editar torneos
  y abrir o cerrar sus inscripciones.
- `/admin/torneo/inscripcion/`: la vista `InscripcionAdmin` permite consultar
  las inscripciones registradas.
- `/admin/torneo/resultado/`: la vista `ResultadoAdmin` permite consultar,
  buscar y ordenar resultados.

## Criterios de acceso y visibilidad

El panel `/admin/` utiliza la autenticación y los permisos integrados de
Django. Las personas anónimas y las cuentas de participante sin permisos
administrativos no acceden a sus pantallas de gestión. El personal puede
gestionar en el admin el nivel y el email vinculado a cada participante; el
email se guarda en la cuenta de Django y no forma parte del modelo
`Participante`. La navegación solo muestra el enlace «Administración» a
cuentas con acceso administrativo.

Las cuentas de usuario solo se gestionan en `/admin/`. La zona privada requiere
autenticación y cada participante solo consulta y modifica sus propias
inscripciones. Las altas y bajas se aceptan únicamente mientras el torneo está
abierto. El registro web de resultados está reservado al personal del sitio.
La clasificación es pública y solo expone nick, partidos jugados, ganados,
perdidos, empatados y puntos. Los resultados se recorren considerando las dos
inscripciones de cada partido. Así, cada partido suma una victoria, una derrota
o un empate para cada participante y los puntos respetan la regla 3/1/0. La
página de gráficas también es pública y sus visualizaciones solo presentan nick
con puntos o victorias; Matplotlib genera las imágenes en el servidor con el
backend `Agg`, sin JavaScript ni persistencia de estadísticas.
Las plantillas principales comparten una navegación y un diseño responsive con
Tailwind CSS; su presentación no modifica las rutas ni el procesamiento de los
formularios.

En desarrollo local, Django se configura para `localhost` y `127.0.0.1` sin
forzar HTTPS ni HSTS. Para producción, `SECRET_KEY` y `ALLOWED_HOSTS` deben
definirse en el entorno; el modo `DEBUG=False` requiere una clave fuerte y
hosts explícitos y habilita la redirección HTTPS, las cookies seguras y la
protección `SECURE_CONTENT_TYPE_NOSNIFF`. HSTS se habilita aparte mediante
`SECURE_HSTS_SECONDS` solo cuando el sitio esté servido permanentemente por
HTTPS. `SECURE_BROWSER_XSS_FILTER` no está disponible en la versión instalada
de Django 5.2.18.

## Manual de instalación

El [README](README.md) contiene los requisitos y comandos actualizados. En
resumen: activar el entorno virtual, instalar `requirements.txt`, ejecutar las
migraciones, poblar la base con `python manage.py poblar_datos` y arrancar con
`python manage.py runserver`. El README documenta las cuentas y la contraseña
de demostración; estas credenciales son solo para desarrollo local.

## Retos técnicos e incidencias

- Se detectó que Django 6.1.2 no era una versión LTS. Se sustituyó por Django
  5.2.18 LTS, cuyo soporte de Python 3.14 está indicado desde Django 5.2.8.
- La configuración inicial no registraba la app `torneo` ni definía una vista
  para la ruta raíz. En la Fase 1 se registró la app y se añadió una página
  inicial.
- En la Fase 2 se generó y aplicó la migración inicial de los modelos propios.
  Los tres modelos también se registraron en el panel de administración.
- En la Fase 3 se incorporaron la plantilla base, el inicio y cierre de
  sesión, el registro asociado a `Participante` y la navegación común. También
  se verificó que el panel de administración limita el acceso a cuentas con
  permisos administrativos.
- En la Fase 6 se añadieron `Torneo` e `Inscripcion`, con una restricción de
  unicidad para evitar altas duplicadas, y se implementaron las operaciones
  propias del participante mediante solicitudes POST protegidas con CSRF.
- En la Fase 7 se conectó `ResultadoForm` con el modelo `Resultado`. La
  validación existente del modelo se refleja en errores de campo en la
  plantilla y el acceso de escritura se limita al personal del sitio.
- La clasificación de la Fase 7 agrupa los resultados por torneo y calcula sus
  estadísticas en memoria, reutilizando `Resultado.ganador` y
  `puntos_clasificacion_a`/`puntos_clasificacion_b`. No se modifica ni se
  persiste ningún dato del modelo.
- En la Fase 8, la tabla de clasificación y la gráfica comparten la misma
  función de cálculo. La vista gráfica devuelve PNG con Matplotlib y backend
  `Agg`, cierra la figura tras generarla y muestra solo nick y puntos.
- Matplotlib 3.10.0 no pudo cargarse correctamente en el entorno Python 3.14;
  se fijó Matplotlib 3.11.2, cuya instalación permite ejecutar las pruebas.
- El segundo gráfico de la Fase 8 compara las victorias por participante a
  partir del campo `ganados` que ya produce el cálculo común, sin repetir la
  lógica de puntuación.
- El refinamiento visual aplica a ambas gráficas barras índigo minimalistas,
  elimina tres bordes y conserva una línea inferior sutil con cuadrícula
  horizontal clara. Tailwind CSS por CDN aporta estilos responsive a la
  navegación, clasificación, gráficas, zona del participante y formularios,
  sin cambiar sus vistas ni datos.
- El comando de datos de prueba de la Fase 9 es transaccional e idempotente:
  crea usuarios, perfiles, juegos, torneos, inscripciones y resultados con
  claves estables, sin borrar datos ni cambiar contraseñas de cuentas existentes.
- La clasificación contabiliza explícitamente los empates para que
  `jugados = ganados + perdidos + empatados`. El queryset carga las dos rutas
  reales de `Resultado` (`inscripcion_a` e `inscripcion_b`) con `select_related`;
  pruebas cubren al participante apareciendo en ambos lados y verifican
  `puntos = 3 × ganados + empatados`.
- La suite de la Fase 10 comprueba directamente los errores de campo de
  `Resultado.clean()` para participantes repetidos e inscripciones de otro
  torneo, y valida la asociación de campos y errores de `ResultadoForm`.
  También comprueba la clasificación pública, respuestas PNG `image/png`,
  escenarios sin resultados, permisos, registro y administración. La ejecución
  completa registra 76 pruebas correctas; las comprobaciones de Django y
  migraciones también finalizan sin incidencias.
- Para reducir consultas N+1, `ResultadoForm` selecciona las relaciones
  `torneo` y `participante` de sus opciones; los listados del admin cargan las
  relaciones visibles con `list_select_related`. Se probaron los números de
  consultas de clasificación, zona del participante, formulario y listados.
- `settings.py` admite la configuración de producción mediante variables de
  entorno. `check --deploy` en modo local conserva advertencias de desarrollo;
  en una configuración de producción simulada queda la advertencia HSTS
  intencional mientras no se confirme su alcance. No se fuerza HTTPS en local.