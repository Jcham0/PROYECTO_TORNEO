# Bitácora de desarrollo

## Contrato actual

- **Modelos:** `Juego` (`nombre`, `descripcion`, `reglas`);
  `Participante` (`usuario`, relación OneToOne con el usuario de Django,
  `nick`, `nivel`); `Torneo` (`nombre`, `descripcion`,
  `inscripciones_abiertas`); `Inscripcion` (`torneo`, `participante`,
  `fecha_inscripcion`), con unicidad por pareja torneo-participante;
  `Resultado` (`torneo`, `inscripcion_a`, `inscripcion_b`, `puntos_a`,
  `puntos_b`, `fecha`, `ronda`), valida las inscripciones y calcula el
  ganador y los puntos de clasificación; `Enfrentamiento` (`juego`,
  `jugador_1`, `jugador_2`, `ganador`, `fecha`, `finalizado`,
  `resultado`), con `resultado` opcional y OneToOne hacia `Resultado`
  mediante `SET_NULL`; valida la coincidencia de participantes y ganador.
- **URLs:** `/admin/`; `torneo:inicio` (`/`); `torneo:zona_participante`
  (`/zona/`); `torneo:login` (`/login/`); `torneo:logout` (`/logout/`);
  `torneo:registro` (`/registro/`); `torneo:registrar_resultado`
  (`/resultados/nuevo/`, solo personal del sitio);
  `torneo:clasificacion` (`/clasificacion/`, público);
  `torneo:graficas` (`/graficas/`, público);
  `torneo:grafica_torneo` (`/graficas/torneo/<int:torneo_id>.png`, público);
  `torneo:grafica_victorias_torneo`
  (`/graficas/torneo/<int:torneo_id>/victorias.png`, público).
- **Vistas:** `admin.site.urls`; `torneo.views.inicio`;
  `torneo.views.zona_participante`;
  `torneo.views.registro_participante`; `torneo.views.registrar_resultado`;
  `torneo.views.clasificacion`; `torneo.views.graficas`;
  `torneo.views.grafica_torneo`; `torneo.views.grafica_victorias_torneo`;
  `django.contrib.auth.views.LoginView` y `LogoutView`.
- **Plantillas de la app:** `torneo/base.html`, `torneo/inicio.html`,
  `torneo/zona_participante.html`, `torneo/login.html` y
  `torneo/registro.html`, `torneo/registrar_resultado.html`,
  `torneo/clasificacion.html` y `torneo/graficas.html`. El admin utiliza las
  plantillas incluidas en Django.
- **Formularios:** `RegistroParticipanteForm` solicita email y nivel, y
  `ResultadoForm` es un `ModelForm` de `Resultado` que muestra los errores de
  validación del modelo en sus campos.
- **Administración:** `JuegoAdmin`, `ParticipanteAdmin`,
  `EnfrentamientoAdmin`, `TorneoAdmin`, `InscripcionAdmin` y `ResultadoAdmin`
  registran los seis modelos. `JuegoAdmin` muestra nombre y descripción, busca
  por nombre, ordena por nombre y edita nombre, descripción y reglas.
  `ParticipanteAdmin` muestra usuario, nick, nivel y email de la cuenta
  vinculada, busca por nick, nombre de usuario y email, ordena por nick y
  permite editar nick, nivel y email. `TorneoAdmin`
  permite administrar y abrir o cerrar inscripciones; `InscripcionAdmin`
  permite consultar las inscripciones. `EnfrentamientoAdmin` muestra el
  resultado y carga sus relaciones para evitar consultas N+1.
- **Acceso y visibilidad:** el panel `/admin/` y la gestión de cuentas de
  usuario se reservan al administrador y aplican las comprobaciones de acceso
  y permisos de Django. `torneo:zona_participante` requiere iniciar sesión y
  limita las inscripciones al participante autenticado.
  `torneo:registrar_resultado` requiere que el usuario sea personal del sitio.
  `torneo:clasificacion` es pública y muestra únicamente nick, partidos
  jugados, ganados, perdidos, empatados y puntos por torneo.
  `torneo:graficas` y `torneo:grafica_torneo` son públicas y muestran únicamente
  nick y puntos del torneo seleccionado; `torneo:grafica_victorias_torneo`
  muestra nick y victorias.
- **Clasificación:** la tabla muestra nick, jugados, ganados, perdidos,
  empatados y puntos; cada registro se cuenta desde ambas inscripciones.
- **Dependencias:** Matplotlib 3.11.2 genera imágenes PNG en el servidor con
  backend `Agg`; no se usa JavaScript para las gráficas.
- **Configuración:** `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` y `EMAIL_BACKEND`
  se pueden establecer mediante variables de entorno. El modo local usa
  `localhost` y `127.0.0.1`; el modo producción exige clave fuerte y hosts
  definidos, activa redirección HTTPS y cookies seguras. HSTS se configura
  opcionalmente mediante `SECURE_HSTS_SECONDS`.
- **Presentación:** Tailwind CSS por CDN da estilo responsive a las plantillas
  principales. Las gráficas usan el estilo `seaborn-v0_8-darkgrid`, barras
  índigo/teal, títulos y ejes personalizados y bordes simplificados.
- **Comando de prueba:** `python manage.py poblar_datos`, implementado en
  `torneo.management.commands.poblar_datos`; crea datos demo sin borrar datos
  existentes y no modifica las contraseñas de cuentas ya creadas.

## 07/11/2026 — Fase 7, pedido 1 de 3: modelo Resultado y lógica de puntuación

- Se creó `Resultado`, asociado a un torneo y a dos inscripciones, con
  marcadores, fecha y ronda. La validación rechaza participantes repetidos y
  inscripciones de otro torneo; una restricción de base de datos impide usar la
  misma inscripción en ambos lados.
- El modelo calcula el ganador y otorga 3 puntos por victoria, 1 por empate y
  0 por derrota. El panel de administración permite consultar y gestionar los
  resultados. Se generó y aplicó `0004_resultado.py` sin cambiar la versión de
  Django ni añadir dependencias.
- Se añadieron pruebas para la victoria, el empate, la coherencia de las
  inscripciones y la disponibilidad del modelo en el admin.
- Se ejecutaron `python manage.py test` (45 pruebas), `python manage.py check`
  y `python manage.py makemigrations --check`; todos finalizaron correctamente.
- Siguiente paso pendiente: Fase 7, pedido 2 de 3 (formulario web para
  registrar resultados).

## 09/11/2026 — Fase 7, pedido 2 de 3: formulario de registro de resultados

- Se creó `ResultadoForm` como `ModelForm` con los campos de torneo,
  inscripciones, marcadores y ronda. La fecha conserva el valor predeterminado
  de `Resultado` y la validación existente del modelo se refleja en errores
  junto a los campos.
- Se añadió la vista `registrar_resultado`, su ruta `/resultados/nuevo/` y la
  plantilla `torneo/registrar_resultado.html`. El acceso está limitado al
  personal del sitio; el enlace aparece en la navegación solo para ese grupo.
- Se añadieron pruebas de guardado, validación de participantes/torneo,
  visualización de errores y control de acceso. No se modificaron modelos ni
  se añadieron librerías.
- Se ejecutaron `python manage.py test` (51 pruebas), `python manage.py check`
  y `python manage.py makemigrations --check`; todos finalizaron correctamente.
- Incidencia resuelta: las aserciones de errores del formulario se adaptaron a
  la firma de `assertFormError` de Django 5.2.
- Se actualizó `MEMORIA.md` y el contrato actual según las rutas, vistas y
  plantillas verificadas.
- Siguiente paso pendiente: Fase 7, pedido 3 de 3 (rankings y tabla de
  clasificación).

## 09/11/2026 — Fase 7, pedido 3 de 3: clasificación y rankings

- Se creó la vista pública `clasificacion` (`/clasificacion/`) con una tabla
  independiente para cada torneo y un enlace visible en la navegación para
  todos los visitantes.
- Las estadísticas se calculan en memoria a partir de `Resultado`, reutilizando
  las properties `ganador` y `puntos_clasificacion_a/b`. El orden es puntos
  descendentes, victorias descendentes y nick ascendente. No se modificaron
  modelos ni se guardaron estadísticas.
- Se añadieron pruebas para victorias, empates, derrotas, desempates, separación
  por torneo, acceso público y ausencia de persistencia. Se actualizó
  `MEMORIA.md` y el contrato actual.
- Se ejecutaron `python manage.py test` (55 pruebas), `python manage.py check`
  y `python manage.py makemigrations --check`; todos finalizaron correctamente.
- Se comprobó en navegador el acceso anónimo a `/clasificacion/`, el enlace
  público y las columnas de la tabla. La base local contiene torneos, pero aún
  no tiene resultados registrados para mostrar.
- Siguiente paso pendiente: Fase 8 (Gráficas).

## 09/11/2026 — Actualización del modelo, registro y administración de participantes

- Se añadió `Participante.nivel`, con opciones `amateur`, `normal` y `expert`,
  valor predeterminado `amateur`; se eliminó `puntos_totales`, ya que la
  clasificación obtiene sus puntuaciones de los resultados.
- Se generó y aplicó una única migración nueva para eliminar el campo antiguo y
  añadir el nivel predeterminado. `0001_initial.py` no se modificó; los
  participantes existentes reciben nivel `amateur`.
- El registro solicita email obligatorio y nivel, guarda el email en
  `User.email`, impide duplicados sin distinguir mayúsculas y crea el perfil
  dentro de la transacción existente. El admin permite consultar y editar nivel
  y email vinculado; al validar el email excluye la propia cuenta.
- Se adaptaron las diez referencias de pruebas a `puntos_totales`; se añadieron
  casos de email requerido, formato, duplicados, nivel predeterminado y nivel
  elegido en el registro. Se comprobó que la clasificación no expone email ni
  nivel.
- Se ejecutaron `python manage.py test` (62 pruebas), `python manage.py check`
  y `python manage.py makemigrations --check`; todos finalizaron correctamente.
- Se verificó en navegador el formulario público de registro: muestra el email
  y el selector de nivel con sus tres opciones, con `amateur` seleccionado por
  defecto.
- Se actualizaron `MEMORIA.md` y este contrato vigente; las entradas históricas
  anteriores se conservaron.
- Siguiente paso pendiente: Fase 8 (Gráficas).

## 03/11/2026 — Fase 1: entorno y esqueleto

- Se reutilizó el entorno virtual `.venv` existente con Python 3.14.5.
- Se cambió Django 6.1.2 por Django 5.2.18 LTS y se actualizó
  `requirements.txt`. No se añadieron otras librerías.
- Se registró la app `torneo` y se configuraron el idioma español y la zona
  horaria `Europe/Madrid`; `USE_TZ` permanece activado.
- Se añadió la vista de inicio y una prueba automatizada para la ruta raíz.
- Se crearon las estructuras iniciales de README y memoria académica.
- Incidencia resuelta: la ruta `/` no tenía vista y no mostraba una página
  inicial.
- Siguiente paso pendiente: definir y migrar los modelos del torneo.

## 03/11/2026 — Fase 2: modelos y administración

- Se generó y aplicó la migración inicial de `Juego`, `Participante` y
  `Enfrentamiento`.
- Se registraron los tres modelos en el panel de administración con columnas
  básicas.
- Se añadieron pruebas para las representaciones de los modelos, valores
  iniciales y registros del admin.
- Siguiente paso pendiente: añadir la navegación común y la autenticación.

## 04/11/2026 — Fase 3, pedido 1 de 3: plantilla base y autenticación

- Se creó `torneo/base.html` con navegación adaptada a la sesión y una zona
  para mostrar mensajes; la página de inicio ahora hereda de esa plantilla.
- Se conectaron las vistas `LoginView` y `LogoutView` de Django y se añadió
  la plantilla del formulario de inicio de sesión.
- Se configuraron `LOGIN_URL`, `LOGIN_REDIRECT_URL` y `LOGOUT_REDIRECT_URL`.
- Se añadieron pruebas para el formulario, el inicio/cierre de sesión, la
  navegación y el uso de POST para cerrar sesión. No se modificaron modelos
  ni se añadieron dependencias.
- Incidencia resuelta: la aplicación no disponía de navegación ni de
  autenticación para participantes.
- Siguiente paso pendiente: implementar el registro de participantes.

## 05/11/2026 — Fase 3, pedido 2 de 3: registro de participantes

- Se creó `RegistroParticipanteForm` para registrar nombre de usuario, nick y
  contraseñas; utiliza las validaciones de contraseña configuradas en Django.
- Se añadió la vista `registro_participante`, la URL `/registro/` y la
  plantilla `torneo/registro.html`, que hereda de `base.html`.
- El registro crea la cuenta y su `Participante` en una operación atómica,
  muestra un mensaje de confirmación y redirige al inicio de sesión.
- Se añadió el enlace «Registrarse» a la navegación solo para usuarios sin
  sesión y se cubrieron los casos acordados con pruebas automatizadas.
- No se modificaron modelos ni se añadieron migraciones o dependencias.
- Incidencia resuelta: el test de redirección seguía la página de destino y
  consumía el mensaje antes de comprobarlo; ahora verifica la ruta sin seguirla.
- Siguiente paso pendiente: completar el pedido 3 de la fase 3.

## 05/11/2026 — Fase 3, pedido 3 de 3: permisos y cierre

- Se conservó el acceso público a las vistas actuales de inicio, registro e
  inicio de sesión; el cierre de sesión mantiene el flujo existente de Django.
- Se confirmó y probó la protección integrada de `/admin/`: visitantes y
  participantes son redirigidos al login del panel; el administrador accede
  al índice y a las listas de usuarios, juegos, participantes y
  enfrentamientos.
- La navegación muestra el enlace «Administración» solo al personal con
  acceso administrativo. No se crearon pantallas de gestión adicionales.
- Se dejó documentado que las cuentas se gestionan únicamente desde el admin y
  que las futuras vistas públicas de participantes expondrán solo nick y
  puntos totales.
- Se añadieron los requisitos funcionales de registro, login/logout y permisos
  a `MEMORIA.md`. No se modificaron modelos ni se añadieron dependencias.
- Siguiente paso pendiente: fase 4 (Juegos, admin).

## 05/11/2026 — Corrección de numeración y documentación

- Se unificó la numeración de las fases en la bitácora y la memoria, y se
  actualizó la descripción y el detalle de vistas y rutas.
- Se revisó el README: no contiene numeración de fases; se dejó sin cambios.
- Siguiente paso pendiente: fase 4 (Juegos, admin).

## 05/11/2026 — Fase 4, pedido 1 de 2: gestión de juegos desde el panel

- Se mejoró `JuegoAdmin` con listado de nombre y descripción, búsqueda por
  nombre, orden alfabético y campos de edición explícitos.
- Se añadieron pruebas de creación, edición, borrado, rechazo de nombres
  duplicados, búsqueda y orden del listado, y acceso administrativo.
- Se verificó que borrar un juego también elimina sus enfrentamientos
  asociados por la relación `on_delete=models.CASCADE`.
- No se modificó el modelo `Juego` ni se creó una migración.
- Siguiente paso pendiente: pedido 2.

## 05/11/2026 — Fase 4, pedido 2 de 2: cierre de gestión de juegos

- Se completó la cobertura de permisos comprobando que visitantes y
  participantes no pueden crear, editar ni borrar juegos mediante solicitudes
  POST; las acciones de administración se mantienen reservadas al personal
  autorizado.
- Se documentaron en `MEMORIA.md` los requisitos funcionales de creación,
  listado, búsqueda, orden, edición, duplicados, borrado en cascada y acceso.
- Se actualizó el contrato actual con la configuración verificada de
  `JuegoAdmin`. No se modificaron modelos ni se añadieron dependencias.
- Siguiente paso pendiente: fase 5 (Participantes, admin).

## 05/11/2026 — Fase 5, pedido 1 de 2: gestión de participantes en el panel

- Se configuró `ParticipanteAdmin` con listado explícito de usuario, nick y
  puntos totales, búsqueda por nick y nombre de usuario, orden por nick y
  formulario explícito de edición.
- Se añadieron pruebas para comprobar el listado de participantes, la búsqueda
  y la edición del nick y los puntos por parte del administrador.
- No se modificaron modelos ni se generaron migraciones o dependencias.
- Siguiente paso pendiente: pedido 2.

## 05/11/2026 — Fase 5, pedido 2 de 2: permisos y cierre de gestión de participantes

- Se reforzaron las pruebas para verificar que personas anónimas y
  participantes reciben una redirección HTTP 302 y no pueden crear, editar,
  cambiar puntos ni eliminar perfiles mediante solicitudes POST directas,
  incluida la acción de borrado en lote.
- Se documentaron en `MEMORIA.md` los requisitos funcionales de consulta,
  búsqueda, edición y permisos de participantes.
- No se modificaron modelos ni se generaron migraciones o dependencias.
- Siguiente paso pendiente: fase 6 (Zona del participante).

## 06/11/2026 — Fase 6, pedido 1 de 2: acceso básico a la zona del participante

- Se creó la vista `zona_participante`, protegida con `@login_required`, y se
  añadió la ruta `/zona/` con nombre `torneo:zona_participante`.
- Se creó `torneo/zona_participante.html`, que hereda de `torneo/base.html` y
  muestra una página privada básica.
- Se añadió en la navegación común un enlace a la zona, visible solo para
  usuarios autenticados.
- Se añadieron pruebas para verificar la redirección de visitantes al login,
  el acceso de usuarios autenticados y la visibilidad condicional del enlace.
- No se modificaron modelos ni se generaron migraciones o dependencias.
- Se ejecutaron `python manage.py test` (33 pruebas), `python manage.py check`
  y `python manage.py makemigrations --check`; todos finalizaron correctamente.
- Siguiente paso pendiente: pedido 2 de la fase 6.

## 06/11/2026 — Fase 6, pedido 2 de 2: modelos para torneos e inscripciones

- Antes de ampliar la zona del participante, se añadieron los modelos
  `Torneo` e `Inscripcion`, con un indicador para abrir o cerrar inscripciones,
  fecha automática y una restricción contra inscripciones duplicadas.
- Se registraron ambos modelos en el admin para que personal autorizado pueda
  gestionar torneos y consultar inscripciones.
- Se creó y aplicó la migración `0003_torneo_inscripcion.py`; no se modificaron
  los modelos existentes ni se añadieron dependencias.
- Se añadieron pruebas para los valores y representación de los modelos, la
  unicidad de la inscripción y su disponibilidad en el admin.
- Se ejecutaron `python manage.py test` (35 pruebas), `python manage.py check`
  y `python manage.py makemigrations --check`; todos finalizaron correctamente.
- Siguiente paso pendiente: conectar los modelos con `zona_participante` para
  consultar torneos disponibles y apuntarse o darse de baja.

## 06/11/2026 — Fase 6, pedido 2 de 2: gestión de inscripciones en la zona

- `zona_participante` muestra las inscripciones propias y los torneos abiertos
  disponibles. Solo permite inscribirse o darse de baja mientras el torneo
  tenga abiertas sus inscripciones; las acciones se procesan por POST.
- Las cuentas autenticadas sin perfil de `Participante` reciben un aviso y no
  pueden modificar inscripciones.
- Se amplió `torneo/zona_participante.html` con los listados y formularios
  protegidos con CSRF. Se conservó `torneo:zona_participante` (`/zona/`), por lo
  que no fue necesario modificar `urls.py`.
- Se añadieron pruebas para listados, altas, bajas, torneos cerrados,
  duplicados, cuentas sin perfil y solicitudes inválidas.
- Se ejecutaron `python manage.py test` (41 pruebas), `python manage.py check`
  y `python manage.py makemigrations --check`; todos finalizaron correctamente.
- Siguiente paso pendiente: Fase 7 (Resultados y rankings).

## 10/11/2026 — Fase 8, pedido 1: base con Matplotlib y gráfica general

- Se extrajo el cálculo de las clasificaciones por torneo a una función
  compartida por la tabla y la nueva gráfica, conservando el criterio de puntos,
  victorias y nick y sin modificar modelos ni guardar estadísticas.
- Se añadieron la página pública `/graficas/` y la ruta PNG
  `/graficas/torneo/<int:torneo_id>.png`. La página permite elegir torneo,
  inicialmente muestra el primero por nombre y usa `<img>` para cargar la
  gráfica, que solo presenta nick y puntos.
- Matplotlib 3.11.2 se añadió a `requirements.txt`; la generación usa el backend
  `Agg` y cierra la figura incluso si se produce un error durante el renderizado.
  La página comunica claramente cuando un torneo no tiene resultados.
- Se añadieron pruebas de acceso público, respuesta PNG y torneo sin resultados.
- Se actualizó `MEMORIA.md` y el contrato actual conforme a las rutas, vistas y
  plantilla vigentes.
- Incidencia resuelta: Matplotlib 3.10.0 no pudo cargarse en Python 3.14 por un
  error binario; se actualizó a Matplotlib 3.11.2.
- Se ejecutaron las pruebas dirigidas (7), `python manage.py test` (65 pruebas),
  `python manage.py check` y `python manage.py makemigrations --check`; todas
  finalizaron correctamente. En el navegador se comprobó `/graficas/` sin
  resultados y que `/graficas/torneo/1.png` responde y se muestra como imagen.
- Se repitieron las tres pruebas de gráficas tras añadir comprobaciones del
  enlace público y de que la generación no modifica los resultados; también
  finalizaron correctamente.
- Siguiente paso pendiente: continuar con el siguiente pedido de la Fase 8.

## 10/11/2026 — Refinamiento visual responsive de la Fase 8

- Se modernizaron la plantilla base, la navegación y las páginas de inicio,
  clasificación, gráficas, zona del participante, registro de resultados,
  inicio de sesión y registro con Tailwind CSS por CDN. Se mantuvieron los
  bloques y URLs, enlaces de imágenes, formularios, CSRF y contexto de Django.
- Se estilizaron las gráficas existentes con Matplotlib `seaborn-v0_8-darkgrid`,
  barras índigo y teal, títulos y ejes legibles, bordes laterales simplificados
  y etiquetas rotadas. No se alteraron las consultas ni los cálculos.
- Se adaptaron las etiquetas estructurales para conservar los selectores y
  textos que ya verificaban las pruebas, sin cambiar esas pruebas ni el
  comportamiento existente. También se ajustó el grosor del título de la gráfica
  para evitar una advertencia de fuente del entorno.
- Se ejecutaron `python manage.py test` (66 pruebas), `python manage.py check`
  y `python manage.py makemigrations --check`; todas finalizaron correctamente.
  Se comprobó que la página inicial y la de gráficas responden con HTTP 200 y se
  revisó en navegador el aviso de torneo sin resultados.
- Tailwind CDN informa que está pensado para desarrollo; se documentó que en
  producción conviene compilar el CSS.
- Siguiente paso pendiente: continuar con el siguiente pedido de la Fase 8.

## 10/11/2026 — Fase 8, pedido 2: comparación de victorias

- Se añadió la visualización comparativa de victorias por participante para el
  torneo elegido. Reutiliza el cálculo `_obtener_clasificaciones()` y el campo
  calculado `ganados`; no añade consultas ni persiste estadísticas.
- Se creó la ruta pública `torneo:grafica_victorias_torneo`
  (`/graficas/torneo/<int:torneo_id>/victorias.png`) y su vista, que genera un
  PNG con Matplotlib/Agg y cierra la figura en `finally`.
- La plantilla `torneo/graficas.html` muestra la segunda imagen junto a la de
  puntos y un aviso específico si no hay resultados para comparar.
- Se añadieron pruebas para la respuesta pública PNG y el caso vacío. No se
  modificaron modelos ni dependencias.
- Se ejecutaron las pruebas dirigidas (4), `python manage.py test` (66 pruebas),
  `python manage.py check` y `python manage.py makemigrations --check`; todas
  finalizaron correctamente. En navegador se verificó el aviso del torneo vacío
  y que la nueva ruta responde como imagen PNG.
- Siguiente paso pendiente: continuar con el siguiente pedido de la Fase 8.

## 10/11/2026 — Fase 9, pedido 1 de 1: datos de demostración

- Se creó el comando `python manage.py poblar_datos`, transaccional e
  idempotente. Genera dos juegos, cuatro usuarios/perfiles demo, dos torneos,
  ocho inscripciones cruzadas y doce resultados con victorias y empates en tres
  jornadas.
- El comando no elimina datos existentes ni cambia las contraseñas de usuarios
  que ya existen. Las cuentas nuevas comparten una contraseña local de demo,
  documentada en `README.md`; no se crea una cuenta administradora.
- Se añadieron pruebas que validan cantidades, variedad de resultados,
  autenticación de la cuenta demo, conservación de contraseñas existentes y
  repetición sin duplicados. Se actualizaron `README.md`, `MEMORIA.md` y el
  contrato vigente.
- Se ejecutó el comando en la base local: creó 2 juegos, 4 usuarios, 4 perfiles,
  2 torneos, 8 inscripciones y 12 resultados. Una segunda ejecución informó
  cero elementos nuevos y se mantuvieron las cantidades.
- Se ejecutaron `python manage.py test` (67 pruebas), `python manage.py check`
  y `python manage.py makemigrations --check`; todas finalizaron correctamente.
- Se verificó con el servidor local que `/clasificacion/` y `/graficas/`
  responden HTTP 200, y que las dos rutas PNG del torneo demo responden HTTP 200
  con `image/png`.
- Siguiente paso pendiente: Fase 10 (Pruebas y limpieza).

## 10/11/2026 — Corrección de estadísticas de clasificación

- Se detectó que los empates ya aumentaban `jugados` y otorgaban el punto de
  clasificación, pero no se contaban en las estadísticas mostradas. Se añadió
  `empatados` para los dos participantes del resultado y una columna visible.
- La suma de resultados sigue considerando `Resultado.inscripcion_a` y
  `Resultado.inscripcion_b`, ya cargadas por el queryset con `select_related`;
  no se usa un filtro que limite los datos a un solo lado. Los nombres reales
  del modelo son esas inscripciones; `jugador_1` y `jugador_2` pertenecen a
  `Enfrentamiento`.
- Se añadieron comprobaciones para
  `jugados = ganados + perdidos + empatados` y
  `puntos = 3 × ganados + empatados`, incluido un participante que aparece en A
  y B en distintos resultados. No se modificaron modelos ni migraciones.
- La primera ejecución detectó expectativas erróneas en la nueva prueba: el
  participante que pierde debe sumar una derrota y 0 puntos, y quien gana debe
  sumar una victoria y 3 puntos. Se corrigieron las aserciones; el cálculo de
  producción no necesitó cambios.
- Pasaron las 9 pruebas dirigidas y la suite completa (68 pruebas). También
  pasaron `python manage.py check` y `python manage.py makemigrations --check`.
- Se verificaron los datos demo locales: ambos torneos muestran empates y todos
  sus participantes cumplen las fórmulas de partidos jugados y puntos.
- Siguiente paso pendiente: Fase 10 (Pruebas y limpieza).

## 10/11/2026 — Estilo minimalista para gráficas

- Se actualizaron ambas vistas PNG para usar barras índigo `#6366f1` de ancho
  `0.45` y título alineado a la izquierda en tono oscuro. Se ocultaron los
  bordes superior, derecho e izquierdo, conservando el inferior en `#e2e8f0`;
  la cuadrícula horizontal usa `#f1f5f9` y se ocultaron las marcas del eje Y.
- Se mantuvieron `tight_layout()`, la generación PNG en memoria, backend `Agg`,
  cierre de figuras, datos y cálculos existentes.
- Se añadió una prueba que comprueba las propiedades visuales en ambas vistas;
  no se alteraron modelos, consultas ni rutas. El entorno no dispone de un
  peso seminegrita en sus fuentes Arial, por lo que se especifica negrita para
  evitar que Matplotlib sustituya el peso y genere una advertencia. Se actualizó
  `MEMORIA.md`.
- Pasaron las 69 pruebas; `python manage.py check` y
  `python manage.py makemigrations --check` finalizaron correctamente.
- Siguiente paso pendiente: Fase 10 (Pruebas y limpieza).

## 10/11/2026 — Fase 10, pedido 1 de 2: suite de pruebas automatizadas

- Se ampliaron las pruebas existentes en `torneo/tests.py` para comprobar los
  errores concretos de `Resultado.clean()` cuando se repite participante o se
  usa una inscripción de otro torneo. También se verificó la vinculación de
  campos y los errores de validación de `ResultadoForm`.
- Se conservaron las pruebas de integración existentes para clasificación
  pública, permisos, panel de administración, gráficas PNG y torneos sin
  resultados. No se modificaron modelos, formularios, vistas, rutas ni plantillas.
- Pasaron las 23 pruebas dirigidas y la suite completa (72 pruebas).
  `python manage.py check` no detectó problemas y
  `python manage.py makemigrations --check` no detectó cambios.
- Se actualizó `MEMORIA.md` y se verificó que el contrato actual continúa
  coincidiendo con modelos, rutas, vistas y plantillas.
- Siguiente paso pendiente: Fase 10, pedido 2 de 2 (limpieza y auditoría).

## 10/11/2026 — Fase 10, pedido 2 de 2: limpieza y auditoría

- Pylance confirmó que `forms.py`, `admin.py`, `views.py` y `models.py` no
  contienen imports sin uso. No se hallaron símbolos de prueba temporales ni se
  retiró código activo.
- `ResultadoForm` carga las relaciones de sus opciones de inscripción con
  `select_related('torneo', 'participante')`. `ParticipanteAdmin`,
  `InscripcionAdmin`, `EnfrentamientoAdmin` y `ResultadoAdmin` declaran
  `list_select_related` para las relaciones que muestran. Se conservaron las
  consultas optimizadas de clasificación y zona.
- Las pruebas verifican un número fijo de consultas al aumentar los resultados
  de clasificación, las inscripciones de la zona, las opciones del formulario
  y las filas relacionadas del admin.
- La configuración ahora lee `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` y
  `EMAIL_BACKEND` del entorno, con valores de desarrollo local. En producción
  exige una clave fuerte y hosts explícitos y activa redirección HTTPS,
  cookies seguras y `SECURE_CONTENT_TYPE_NOSNIFF`. HSTS permanece optativo y
  desactivado por defecto para no afectar localhost. La opción
  `SECURE_BROWSER_XSS_FILTER` no existe en Django 5.2.18 y no se añadió como
  ajuste obsoleto.
- `check --deploy` en local informó seis advertencias esperables por HTTP de
  desarrollo y la clave local. Con el perfil de producción simulado informó
  solo W004 por HSTS optativo; ambos comandos terminaron sin errores. Pasaron
  las 76 pruebas, `manage.py check` y `makemigrations --check`.
- Se corrigieron las referencias de documentación generadas que indicaban
  Django 6.1, para que correspondan a Django 5.2.18.
- Siguiente paso pendiente: Fase 11 (Documentación final).

## 11/11/2026 — Fase 7, pedido 4 de 4: vínculo entre enfrentamiento y resultado

- Se añadió `Enfrentamiento.resultado`, una relación `OneToOneField` opcional a
  `Resultado` con `SET_NULL`. `Enfrentamiento.clean()` valida que los
  participantes coincidan en cualquier orden y que el ganador coincida con el
  marcador; un empate exige no tener ganador. `save()` ejecuta `full_clean()`.
- La migración `0006_enfrentamiento_resultado.py` solo añade el campo. Los
  enfrentamientos previos quedan con `resultado=NULL`; no se intentó deducir ni
  migrar asociaciones históricas. La base actual no tenía enfrentamientos.
- `EnfrentamientoAdmin` muestra el resultado y usa `list_select_related` para
  cargarlo junto con torneo, inscripciones y participantes. Las pruebas nuevas
  cubren seis escenarios de integridad, eliminación del resultado y consultas
  estables del admin. No se modificaron vistas, formularios, rutas, plantillas,
  clasificación ni gráficas.
- `poblar_datos` se ejecutó dos veces en la base actual y en una SQLite nueva;
  la segunda ejecución no duplicó datos. La suite completa pasó 82 pruebas;
  `python manage.py check` y `python manage.py makemigrations --check`
  finalizaron correctamente. Sin dependencias nuevas.
- Se actualizaron README y MEMORIA. Revisión manual pendiente de la memoria:
  modelo de datos y esquema, evolutivos y número de pruebas (82).
- Siguiente paso pendiente: Fase 11 (Documentación final).

## 11/11/2026 — Fase 11, pedido 1 de 2: diagrama entidad-relación en la memoria

- Se insertó en `MEMORIA.md` la imagen `assets/diagrama_ER.png` en el apartado
  «Modelo de datos» y se añadió una descripción de las relaciones entre
  `Torneo`, `Participante`, `Enfrentamiento` y `Resultado`.
- Se verificó que el PNG existe y corresponde a los modelos y relaciones
  definidos en `torneo/models.py`. No se modificaron modelos ni código.
- Siguiente paso pendiente: Fase 11, pedido 2 de 2 (cierre documental y auditoría final).

## 11/11/2026 — Fase 11, pedido 2 de 2: cierre de documentación y auditoría final

- Se completó la documentación técnica final en `README.md` y `MEMORIA.md`.
  La memoria incorpora el diagrama entidad-relación validado y la explicación
  de las relaciones entre modelos; también incluye el acceso de evaluación al
  panel de administración.
- Se revisó la arquitectura y el código de modelos, formularios, vistas,
  administración y rutas, además de la consistencia de las plantillas y la
  documentación frente al contrato del proyecto.
- La suite completa registra 82 pruebas aprobadas; `python manage.py check` y
  `python manage.py makemigrations --check` finalizaron correctamente.
- Se cotejaron el modelo de datos, el diagrama E-R, los evolutivos y el número
  de pruebas documentado con el estado verificado del proyecto.
- Fase 11 (Documentación final) completada.
- Siguiente paso pendiente: Ninguno; proyecto finalizado.