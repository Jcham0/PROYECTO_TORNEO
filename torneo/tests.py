from io import StringIO
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.db.models import F
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from matplotlib.colors import to_hex

from .forms import ResultadoForm
from .models import (
    Enfrentamiento,
    Inscripcion,
    Juego,
    Participante,
    Resultado,
    Torneo,
)
from .views import _estilizar_grafica, _obtener_clasificaciones


class PaginaInicioTests(TestCase):
    def test_pagina_inicio_muestra_confirmacion(self):
        respuesta = self.client.get('/')

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'La aplicación de torneo está funcionando.')


class DatosDemostracionTests(TestCase):
    def test_comando_crea_datos_variados_y_es_idempotente(self):
        salida = StringIO()

        call_command('poblar_datos', stdout=salida)

        self.assertEqual(Juego.objects.count(), 2)
        self.assertEqual(
            get_user_model().objects.filter(
                username__startswith='demo_',
            ).count(),
            4,
        )
        self.assertEqual(
            Participante.objects.filter(nick__startswith='Demo').count(),
            4,
        )
        self.assertEqual(
            Torneo.objects.filter(nombre__startswith='Demo - ').count(),
            2,
        )
        self.assertEqual(Inscripcion.objects.count(), 8)
        self.assertEqual(Resultado.objects.count(), 12)
        self.assertEqual(
            set(
                Resultado.objects.values_list('ronda', flat=True).distinct(),
            ),
            {1, 2, 3},
        )
        self.assertTrue(
            Resultado.objects.filter(puntos_a=F('puntos_b')).exists(),
        )
        self.assertTrue(
            Resultado.objects.exclude(puntos_a=F('puntos_b')).exists(),
        )

        usuario_demo = get_user_model().objects.get(username='demo_ana')
        self.assertTrue(usuario_demo.check_password('DemoTorneo2026!'))

        usuario_demo.set_password('ClaveElegida2026!')
        usuario_demo.save(update_fields=['password'])
        call_command('poblar_datos', stdout=StringIO())

        usuario_demo.refresh_from_db()
        self.assertTrue(usuario_demo.check_password('ClaveElegida2026!'))
        self.assertEqual(Juego.objects.count(), 2)
        self.assertEqual(
            Participante.objects.filter(nick__startswith='Demo').count(),
            4,
        )
        self.assertEqual(
            Torneo.objects.filter(nombre__startswith='Demo - ').count(),
            2,
        )
        self.assertEqual(Inscripcion.objects.count(), 8)
        self.assertEqual(Resultado.objects.count(), 12)


class ClasificacionTests(TestCase):
    def setUp(self):
        self.torneo = Torneo.objects.create(nombre='Torneo de clasificación')
        self.participantes = {
            nick: self._crear_participante(nick)
            for nick in (
                'Zulu',
                'Gamma',
                'Alpha',
                'Beta',
                'Delta',
                'Bravo',
                'Echo',
                'Charlie',
                'Foxtrot',
            )
        }
        self._crear_resultado('Zulu', 'Gamma', 2, 1)
        self._crear_resultado('Alpha', 'Beta', 1, 1)
        self._crear_resultado('Alpha', 'Gamma', 2, 2)
        self._crear_resultado('Alpha', 'Delta', 0, 0)
        self._crear_resultado('Bravo', 'Echo', 1, 0)
        self._crear_resultado('Charlie', 'Foxtrot', 3, 2)

    def _crear_participante(self, nick):
        usuario = get_user_model().objects.create_user(
            username=f'usuario-{nick.lower()}',
            email=f'{nick.lower()}@example.com',
            password='clave-de-prueba',
        )
        return Participante.objects.create(usuario=usuario, nick=nick)

    def _crear_resultado(self, nick_a, nick_b, puntos_a, puntos_b):
        inscripcion_a, _ = Inscripcion.objects.get_or_create(
            torneo=self.torneo,
            participante=self.participantes[nick_a],
        )
        inscripcion_b, _ = Inscripcion.objects.get_or_create(
            torneo=self.torneo,
            participante=self.participantes[nick_b],
        )
        return Resultado.objects.create(
            torneo=self.torneo,
            inscripcion_a=inscripcion_a,
            inscripcion_b=inscripcion_b,
            puntos_a=puntos_a,
            puntos_b=puntos_b,
        )

    def test_clasificacion_carga_relaciones_sin_consultas_por_resultado(self):
        with self.assertNumQueries(2):
            clasificaciones = _obtener_clasificaciones()

        self.assertEqual(len(clasificaciones[0]['participantes']), 9)

    def test_clasificacion_calcula_estadisticas_y_aplica_desempates(self):
        respuesta = self.client.get(reverse('torneo:clasificacion'))

        self.assertEqual(respuesta.status_code, 200)
        clasificacion = respuesta.context['clasificaciones'][0]
        self.assertEqual(clasificacion['torneo'], self.torneo)
        self.assertEqual(
            [
                (
                    participante['nick'],
                    participante['jugados'],
                    participante['ganados'],
                    participante['perdidos'],
                    participante['empatados'],
                    participante['puntos'],
                )
                for participante in clasificacion['participantes']
            ],
            [
                ('Bravo', 1, 1, 0, 0, 3),
                ('Charlie', 1, 1, 0, 0, 3),
                ('Zulu', 1, 1, 0, 0, 3),
                ('Alpha', 3, 0, 0, 3, 3),
                ('Beta', 1, 0, 0, 1, 1),
                ('Delta', 1, 0, 0, 1, 1),
                ('Gamma', 2, 0, 1, 1, 1),
                ('Echo', 1, 0, 1, 0, 0),
                ('Foxtrot', 1, 0, 1, 0, 0),
            ],
        )
        for participante in clasificacion['participantes']:
            self.assertEqual(
                participante['jugados'],
                (
                    participante['ganados']
                    + participante['perdidos']
                    + participante['empatados']
                ),
            )
            self.assertEqual(
                participante['puntos'],
                3 * participante['ganados'] + participante['empatados'],
            )

    def test_clasificacion_cuenta_participante_en_ambos_lados_del_resultado(
        self,
    ):
        self._crear_resultado('Gamma', 'Zulu', 1, 0)

        respuesta = self.client.get(reverse('torneo:clasificacion'))
        participantes = {
            participante['nick']: participante
            for participante in respuesta.context['clasificaciones'][0][
                'participantes'
            ]
        }

        self.assertEqual(
            (
                participantes['Zulu']['jugados'],
                participantes['Zulu']['ganados'],
                participantes['Zulu']['perdidos'],
                participantes['Zulu']['empatados'],
                participantes['Zulu']['puntos'],
            ),
            (2, 1, 1, 0, 3),
        )
        self.assertEqual(
            (
                participantes['Gamma']['jugados'],
                participantes['Gamma']['ganados'],
                participantes['Gamma']['perdidos'],
                participantes['Gamma']['empatados'],
                participantes['Gamma']['puntos'],
            ),
            (3, 1, 1, 1, 4),
        )

    def test_clasificacion_es_publica_y_muestra_solo_las_columnas_previstas(self):
        respuesta = self.client.get(reverse('torneo:clasificacion'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Clasificación')
        self.assertContains(
            respuesta,
            f'href="{reverse("torneo:clasificacion")}">Clasificación</a>',
        )
        for encabezado in (
            'Nick',
            'Jugados',
            'Ganados',
            'Perdidos',
            'Empatados',
            'Puntos',
        ):
            self.assertContains(respuesta, f'<th scope="col">{encabezado}</th>')
        self.assertNotContains(respuesta, 'Fecha')
        self.assertNotContains(respuesta, 'Ronda')
        self.assertNotContains(respuesta, '@example.com')
        self.assertNotContains(respuesta, 'Amateur')
        self.assertNotContains(respuesta, 'Normal')
        self.assertNotContains(respuesta, 'Expert')

    def test_clasificacion_separa_torneos_y_no_guarda_puntuaciones(self):
        otro_torneo = Torneo.objects.create(nombre='Otro torneo')
        self._crear_resultado('Zulu', 'Echo', 0, 0)
        inscripcion_otro_a = Inscripcion.objects.create(
            torneo=otro_torneo,
            participante=self.participantes['Zulu'],
        )
        inscripcion_otro_b = Inscripcion.objects.create(
            torneo=otro_torneo,
            participante=self.participantes['Echo'],
        )
        Resultado.objects.create(
            torneo=otro_torneo,
            inscripcion_a=inscripcion_otro_a,
            inscripcion_b=inscripcion_otro_b,
            puntos_a=5,
            puntos_b=2,
        )
        resultados_antes = list(
            Resultado.objects.order_by('pk').values_list(
                'pk',
                'puntos_a',
                'puntos_b',
            )
        )

        respuesta = self.client.get(reverse('torneo:clasificacion'))

        clasificaciones = respuesta.context['clasificaciones']
        self.assertEqual(
            [clasificacion['torneo'] for clasificacion in clasificaciones],
            [otro_torneo, self.torneo],
        )
        clasificacion_original = clasificaciones[1]
        zulu_original = next(
            participante
            for participante in clasificacion_original['participantes']
            if participante['nick'] == 'Zulu'
        )
        self.assertEqual(zulu_original['puntos'], 4)
        self.assertEqual(Resultado.objects.count(), 8)
        resultados_despues = list(
            Resultado.objects.order_by('pk').values_list(
                'pk',
                'puntos_a',
                'puntos_b',
            )
        )
        self.assertEqual(resultados_despues, resultados_antes)

    def test_muestra_torneos_sin_resultados_y_estado_sin_torneos(self):
        Torneo.objects.create(nombre='Torneo vacío')

        respuesta = self.client.get(reverse('torneo:clasificacion'))

        self.assertContains(respuesta, 'Torneo vacío')
        self.assertContains(respuesta, 'Todavía no hay resultados registrados.')

        Torneo.objects.all().delete()
        respuesta_sin_torneos = self.client.get(
            reverse('torneo:clasificacion'),
        )
        self.assertContains(respuesta_sin_torneos, 'Aún no hay torneos')


class GraficasTests(TestCase):
    def setUp(self):
        self.torneo = Torneo.objects.create(nombre='Torneo de gráficas')
        self.participante_a = self._crear_participante('Alpha')
        self.participante_b = self._crear_participante('Beta')
        inscripcion_a = Inscripcion.objects.create(
            torneo=self.torneo,
            participante=self.participante_a,
        )
        inscripcion_b = Inscripcion.objects.create(
            torneo=self.torneo,
            participante=self.participante_b,
        )
        Resultado.objects.create(
            torneo=self.torneo,
            inscripcion_a=inscripcion_a,
            inscripcion_b=inscripcion_b,
            puntos_a=3,
            puntos_b=1,
        )

    def _crear_participante(self, nick):
        usuario = get_user_model().objects.create_user(
            username=f'usuario-{nick.lower()}',
            email=f'{nick.lower()}@example.com',
            password='clave-de-prueba',
        )
        return Participante.objects.create(usuario=usuario, nick=nick)

    def test_pagina_publica_muestra_grafica_del_torneo_seleccionado(self):
        respuesta = self.client.get(reverse('torneo:graficas'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Gráficas de resultados')
        self.assertContains(
            respuesta,
            reverse(
                'torneo:grafica_torneo',
                kwargs={'torneo_id': self.torneo.pk},
            ),
        )
        self.assertContains(
            respuesta,
            reverse(
                'torneo:grafica_victorias_torneo',
                kwargs={'torneo_id': self.torneo.pk},
            ),
        )
        self.assertContains(respuesta, 'Victorias por participante')
        self.assertContains(
            respuesta,
            f'href="{reverse("torneo:graficas")}">Gráficas</a>',
        )
        self.assertNotContains(respuesta, '@example.com')
        self.assertNotContains(respuesta, 'Amateur')
        self.assertNotContains(respuesta, 'Normal')
        self.assertNotContains(respuesta, 'Expert')

    def test_vista_devuelve_una_imagen_png(self):
        resultados_antes = list(
            Resultado.objects.order_by('pk').values_list(
                'pk',
                'puntos_a',
                'puntos_b',
            )
        )
        respuesta = self.client.get(
            reverse(
                'torneo:grafica_torneo',
                kwargs={'torneo_id': self.torneo.pk},
            ),
        )
        resultados_despues = list(
            Resultado.objects.order_by('pk').values_list(
                'pk',
                'puntos_a',
                'puntos_b',
            )
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta['Content-Type'], 'image/png')
        self.assertTrue(respuesta.content.startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertEqual(resultados_despues, resultados_antes)

    def test_vista_de_victorias_devuelve_una_imagen_png(self):
        respuesta = self.client.get(
            reverse(
                'torneo:grafica_victorias_torneo',
                kwargs={'torneo_id': self.torneo.pk},
            ),
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta['Content-Type'], 'image/png')
        self.assertTrue(respuesta.content.startswith(b'\x89PNG\r\n\x1a\n'))

    def test_vistas_aplican_estilo_minimalista_a_las_barras(self):
        rutas = (
            'torneo:grafica_torneo',
            'torneo:grafica_victorias_torneo',
        )
        with patch(
            'torneo.views._estilizar_grafica',
            wraps=_estilizar_grafica,
        ) as estilizar:
            respuestas = [
                self.client.get(
                    reverse(ruta, kwargs={'torneo_id': self.torneo.pk}),
                )
                for ruta in rutas
            ]

        self.assertEqual(
            [respuesta.status_code for respuesta in respuestas],
            [200, 200],
        )
        for llamada in estilizar.call_args_list:
            eje = llamada.args[0]
            self.assertEqual(
                [to_hex(barra.get_facecolor()) for barra in eje.patches],
                ['#6366f1', '#6366f1'],
            )
            self.assertEqual(
                [barra.get_width() for barra in eje.patches],
                [0.45, 0.45],
            )
            self.assertFalse(eje.spines['top'].get_visible())
            self.assertFalse(eje.spines['right'].get_visible())
            self.assertFalse(eje.spines['left'].get_visible())
            self.assertTrue(eje.spines['bottom'].get_visible())
            self.assertEqual(
                to_hex(eje.spines['bottom'].get_edgecolor()),
                '#e2e8f0',
            )
            self.assertRegex(
                eje.get_title(loc='left'),
                r'^(Puntos|Victorias) por participante:',
            )
            self.assertEqual(eje._left_title.get_fontweight(), 'bold')
            self.assertTrue(
                all(
                    tick.get_markersize() == 0
                    for tick in eje.get_yticklines()
                ),
            )
            self.assertTrue(
                all(
                    not etiqueta.get_visible()
                    for etiqueta in eje.get_yticklabels()
                ),
            )
            self.assertEqual(
                to_hex(eje.get_ygridlines()[0].get_color()),
                '#f1f5f9',
            )

    def test_torneo_sin_resultados_muestra_mensaje_y_sigue_devolviendo_png(
        self,
    ):
        Resultado.objects.all().delete()
        respuesta_pagina = self.client.get(reverse('torneo:graficas'))
        respuesta_imagen = self.client.get(
            reverse(
                'torneo:grafica_torneo',
                kwargs={'torneo_id': self.torneo.pk},
            ),
        )

        self.assertEqual(respuesta_pagina.status_code, 200)
        self.assertContains(
            respuesta_pagina,
            'Todavía no hay resultados registrados para este torneo.',
        )
        self.assertContains(
            respuesta_pagina,
            'No hay resultados para comparar las victorias de este torneo.',
        )
        self.assertNotContains(respuesta_pagina, '<img')
        self.assertEqual(respuesta_imagen.status_code, 200)
        self.assertEqual(respuesta_imagen['Content-Type'], 'image/png')
        self.assertTrue(respuesta_imagen.content.startswith(b'\x89PNG\r\n\x1a\n'))
        respuesta_victorias = self.client.get(
            reverse(
                'torneo:grafica_victorias_torneo',
                kwargs={'torneo_id': self.torneo.pk},
            ),
        )
        self.assertEqual(respuesta_victorias.status_code, 200)
        self.assertEqual(respuesta_victorias['Content-Type'], 'image/png')
        self.assertTrue(
            respuesta_victorias.content.startswith(b'\x89PNG\r\n\x1a\n'),
        )


class ZonaParticipanteTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username='participante-zona',
            password='clave-de-prueba',
        )
        self.participante = Participante.objects.create(
            usuario=self.usuario,
            nick='JugadorZona',
        )

    def test_usuario_anonimo_es_redirigido_al_login(self):
        url_zona = reverse('torneo:zona_participante')

        respuesta = self.client.get(url_zona)

        self.assertRedirects(
            respuesta,
            f'{reverse("torneo:login")}?next={url_zona}',
        )

    def test_enlace_zona_solo_se_muestra_a_usuarios_autenticados(self):
        respuesta_anonima = self.client.get(reverse('torneo:inicio'))

        self.assertNotContains(respuesta_anonima, 'Zona del participante')

        usuario = get_user_model().objects.create_user(
            username='participante-menu',
            password='clave-de-prueba',
        )
        self.client.force_login(usuario)
        respuesta_autenticada = self.client.get(reverse('torneo:inicio'))

        self.assertContains(respuesta_autenticada, 'Zona del participante')
        self.assertContains(
            respuesta_autenticada,
            f'href="{reverse("torneo:zona_participante")}"',
        )

    def test_usuario_autenticado_accede_a_la_zona(self):
        self.client.force_login(self.usuario)

        respuesta = self.client.get(reverse('torneo:zona_participante'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Zona del participante')
        self.assertContains(respuesta, 'JugadorZona')

    def test_muestra_inscripciones_y_torneos_disponibles(self):
        torneo_abierto = Torneo.objects.create(nombre='Torneo abierto')
        torneo_cerrado = Torneo.objects.create(
            nombre='Torneo cerrado',
            inscripciones_abiertas=False,
        )
        Inscripcion.objects.create(
            torneo=torneo_cerrado,
            participante=self.participante,
        )
        self.client.force_login(self.usuario)

        respuesta = self.client.get(reverse('torneo:zona_participante'))

        self.assertContains(respuesta, 'Torneo cerrado')
        self.assertContains(respuesta, 'Torneo abierto')
        self.assertEqual(
            list(respuesta.context['torneos_disponibles']),
            [torneo_abierto],
        )
        self.assertEqual(
            list(
                respuesta.context['mis_inscripciones'].values_list(
                    'torneo_id',
                    flat=True,
                ),
            ),
            [torneo_cerrado.pk],
        )

    def test_listado_no_multiplica_consultas_por_inscripcion(self):
        self.client.force_login(self.usuario)
        primer_torneo = Torneo.objects.create(nombre='Torneo inicial')
        Inscripcion.objects.create(
            torneo=primer_torneo,
            participante=self.participante,
        )

        with CaptureQueriesContext(connection) as consultas_iniciales:
            respuesta_inicial = self.client.get(
                reverse('torneo:zona_participante'),
            )

        for numero in range(2, 5):
            torneo = Torneo.objects.create(nombre=f'Torneo {numero}')
            Inscripcion.objects.create(
                torneo=torneo,
                participante=self.participante,
            )

        with CaptureQueriesContext(connection) as consultas_ampliadas:
            respuesta_ampliada = self.client.get(
                reverse('torneo:zona_participante'),
            )

        self.assertEqual(respuesta_inicial.status_code, 200)
        self.assertEqual(respuesta_ampliada.status_code, 200)
        self.assertEqual(
            len(consultas_iniciales.captured_queries),
            len(consultas_ampliadas.captured_queries),
        )

    def test_participante_se_apunta_a_un_torneo_abierto_sin_duplicarse(self):
        torneo = Torneo.objects.create(nombre='Torneo abierto')
        self.client.force_login(self.usuario)
        url_zona = reverse('torneo:zona_participante')

        respuesta = self.client.post(
            url_zona,
            {'accion': 'apuntarse', 'torneo_id': torneo.pk},
        )
        self.assertRedirects(respuesta, url_zona)

        self.client.post(
            url_zona,
            {'accion': 'apuntarse', 'torneo_id': torneo.pk},
        )

        self.assertEqual(
            Inscripcion.objects.filter(
                torneo=torneo,
                participante=self.participante,
            ).count(),
            1,
        )

    def test_participante_se_da_de_baja_de_un_torneo_abierto(self):
        torneo = Torneo.objects.create(nombre='Torneo abierto')
        Inscripcion.objects.create(
            torneo=torneo,
            participante=self.participante,
        )
        self.client.force_login(self.usuario)

        respuesta = self.client.post(
            reverse('torneo:zona_participante'),
            {'accion': 'desapuntarse', 'torneo_id': torneo.pk},
        )

        self.assertRedirects(respuesta, reverse('torneo:zona_participante'))
        self.assertFalse(
            Inscripcion.objects.filter(
                torneo=torneo,
                participante=self.participante,
            ).exists()
        )

    def test_nivel_por_defecto_es_amateur(self):
        usuario = get_user_model().objects.create_user(
            username='usuario-nivel-predeterminado',
            password='clave-de-prueba',
        )

        participante = Participante.objects.create(
            usuario=usuario,
            nick='NivelPredeterminado',
        )

        self.assertEqual(participante.nivel, Participante.Nivel.AMATEUR)

    def test_no_puede_apuntarse_ni_darse_de_baja_si_el_torneo_esta_cerrado(self):
        torneo = Torneo.objects.create(
            nombre='Torneo cerrado',
            inscripciones_abiertas=False,
        )
        self.client.force_login(self.usuario)
        url_zona = reverse('torneo:zona_participante')

        respuesta_apuntarse = self.client.post(
            url_zona,
            {'accion': 'apuntarse', 'torneo_id': torneo.pk},
        )
        self.assertRedirects(respuesta_apuntarse, url_zona)
        self.assertFalse(Inscripcion.objects.filter(torneo=torneo).exists())

        inscripcion = Inscripcion.objects.create(
            torneo=torneo,
            participante=self.participante,
        )
        respuesta_baja = self.client.post(
            url_zona,
            {'accion': 'desapuntarse', 'torneo_id': torneo.pk},
        )
        self.assertRedirects(respuesta_baja, url_zona)
        self.assertTrue(Inscripcion.objects.filter(pk=inscripcion.pk).exists())

    def test_cuenta_sin_perfil_no_puede_gestionar_inscripciones(self):
        usuario = get_user_model().objects.create_user(
            username='cuenta-sin-perfil-zona',
            password='clave-de-prueba',
        )
        torneo = Torneo.objects.create(nombre='Torneo abierto')
        self.client.force_login(usuario)

        respuesta = self.client.get(reverse('torneo:zona_participante'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'no tiene un perfil de participante')

        respuesta_post = self.client.post(
            reverse('torneo:zona_participante'),
            {'accion': 'apuntarse', 'torneo_id': torneo.pk},
        )

        self.assertEqual(respuesta_post.status_code, 403)
        self.assertFalse(Inscripcion.objects.filter(torneo=torneo).exists())

    def test_una_accion_post_invalida_responde_400(self):
        self.client.force_login(self.usuario)

        respuesta = self.client.post(
            reverse('torneo:zona_participante'),
            {'accion': 'accion-invalida', 'torneo_id': '1'},
        )

        self.assertEqual(respuesta.status_code, 400)


class AutenticacionTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username='participante',
            password='clave-de-prueba',
        )
        Participante.objects.create(usuario=self.usuario, nick='Campeon')

    def test_login_muestra_formulario_y_autentica_al_usuario(self):
        respuesta = self.client.get(reverse('torneo:login'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'name="username"')
        self.assertContains(respuesta, 'Iniciar sesión')

        respuesta = self.client.post(
            reverse('torneo:login'),
            {'username': 'participante', 'password': 'clave-de-prueba'},
        )

        self.assertRedirects(respuesta, reverse('torneo:inicio'))
        self.assertContains(self.client.get('/'), 'Campeon')
        self.assertContains(self.client.get('/'), 'Cerrar sesión')

    def test_navegacion_muestra_login_y_logout_solo_por_post(self):
        respuesta = self.client.get('/')

        self.assertContains(respuesta, 'Iniciar sesión')
        self.assertNotContains(respuesta, 'Cerrar sesión')

        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse('torneo:logout')).status_code, 405)

        respuesta = self.client.post(reverse('torneo:logout'))

        self.assertRedirects(respuesta, reverse('torneo:inicio'))
        self.assertTrue(self.client.get('/').wsgi_request.user.is_anonymous)
        self.assertContains(self.client.get('/'), 'Iniciar sesión')

    def test_usuario_sin_participante_ve_su_nombre_de_usuario(self):
        usuario = get_user_model().objects.create_user(
            username='cuenta-sin-perfil',
            password='clave-de-prueba',
        )
        self.client.force_login(usuario)

        self.assertContains(self.client.get('/'), 'cuenta-sin-perfil')

    def test_enlace_registrarse_solo_aparece_sin_sesion(self):
        respuesta = self.client.get(reverse('torneo:inicio'))

        self.assertContains(respuesta, 'Registrarse')
        self.assertNotContains(respuesta, 'Administración')

        self.client.force_login(self.usuario)
        respuesta = self.client.get(reverse('torneo:inicio'))

        self.assertNotContains(respuesta, 'Registrarse')
        self.assertNotContains(respuesta, 'Administración')

    def test_enlace_administracion_aparece_para_personal(self):
        administrador = get_user_model().objects.create_user(
            username='administrador-nav',
            password='clave-de-prueba',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(administrador)

        respuesta = self.client.get(reverse('torneo:inicio'))

        self.assertContains(respuesta, 'Administración')


class ModelosTorneoTests(TestCase):
    def setUp(self):
        usuario_1 = get_user_model().objects.create_user(
            username='jugador1',
            password='clave-de-prueba',
        )
        usuario_2 = get_user_model().objects.create_user(
            username='jugador2',
            password='clave-de-prueba',
        )
        self.juego = Juego.objects.create(nombre='Ajedrez')
        self.jugador_1 = Participante.objects.create(
            usuario=usuario_1,
            nick='Alfil',
        )
        self.jugador_2 = Participante.objects.create(
            usuario=usuario_2,
            nick='Torre',
        )

    def test_modelos_tienen_representacion_legible(self):
        enfrentamiento = Enfrentamiento.objects.create(
            juego=self.juego,
            jugador_1=self.jugador_1,
            jugador_2=self.jugador_2,
        )

        self.assertEqual(str(self.juego), 'Ajedrez')
        self.assertEqual(str(self.jugador_1), 'Alfil')
        self.assertEqual(str(enfrentamiento), 'Alfil vs Torre (Ajedrez)')
        self.assertFalse(enfrentamiento.finalizado)
        self.assertIsNone(enfrentamiento.ganador)
        self.assertIsNotNone(enfrentamiento.fecha)

    def test_torneo_e_inscripcion_tienen_valores_y_representacion(self):
        torneo = Torneo.objects.create(nombre='Torneo de prueba')
        inscripcion = Inscripcion.objects.create(
            torneo=torneo,
            participante=self.jugador_1,
        )

        self.assertTrue(torneo.inscripciones_abiertas)
        self.assertEqual(str(torneo), 'Torneo de prueba')
        self.assertEqual(str(inscripcion), 'Alfil - Torneo de prueba')
        self.assertIsNotNone(inscripcion.fecha_inscripcion)

    def test_no_se_permite_inscribir_dos_veces_al_mismo_torneo(self):
        torneo = Torneo.objects.create(nombre='Torneo de prueba')
        Inscripcion.objects.create(
            torneo=torneo,
            participante=self.jugador_1,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Inscripcion.objects.create(
                    torneo=torneo,
                    participante=self.jugador_1,
                )

    def test_admin_muestra_las_listas_de_los_modelos_del_torneo(self):
        usuario_admin = get_user_model().objects.create_user(
            username='administrador',
            password='clave-de-prueba',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(usuario_admin)

        listas = {
            Juego: ('nombre',),
            Participante: ('nick', 'usuario', 'nivel', 'email_usuario'),
            Enfrentamiento: (
                'juego',
                'jugador_1',
                'jugador_2',
                'ganador',
                'resultado',
                'finalizado',
                'fecha',
            ),
            Torneo: ('nombre', 'inscripciones_abiertas'),
            Inscripcion: ('torneo', 'participante', 'fecha_inscripcion'),
            Resultado: (
                'torneo',
                'inscripcion_a',
                'inscripcion_b',
                'puntos_a',
                'puntos_b',
                'ronda',
                'fecha',
            ),
        }

        for modelo, columnas in listas.items():
            with self.subTest(modelo=modelo.__name__):
                respuesta = self.client.get(
                    reverse(f'admin:torneo_{modelo._meta.model_name}_changelist')
                )

                self.assertEqual(respuesta.status_code, 200)
                self.assertTrue(admin.site.is_registered(modelo))
                self.assertTrue(
                    set(columnas).issubset(respuesta.context['cl'].list_display)
                )

    def test_listados_admin_cargan_relaciones_en_una_consulta(self):
        administrador = get_user_model().objects.create_superuser(
            username='administrador-consultas',
            password='clave-de-prueba',
        )
        torneo = Torneo.objects.create(nombre='Torneo de consultas')
        inscripcion_1 = Inscripcion.objects.create(
            torneo=torneo,
            participante=self.jugador_1,
        )
        inscripcion_2 = Inscripcion.objects.create(
            torneo=torneo,
            participante=self.jugador_2,
        )
        resultado = Resultado.objects.create(
            torneo=torneo,
            inscripcion_a=inscripcion_1,
            inscripcion_b=inscripcion_2,
            puntos_a=3,
            puntos_b=1,
        )
        Enfrentamiento.objects.create(
            juego=self.juego,
            jugador_1=self.jugador_1,
            jugador_2=self.jugador_2,
            ganador=self.jugador_1,
            resultado=resultado,
        )
        segundo_resultado = Resultado.objects.create(
            torneo=torneo,
            inscripcion_a=inscripcion_1,
            inscripcion_b=inscripcion_2,
            puntos_a=0,
            puntos_b=2,
        )
        Enfrentamiento.objects.create(
            juego=self.juego,
            jugador_1=self.jugador_1,
            jugador_2=self.jugador_2,
            ganador=self.jugador_2,
            resultado=segundo_resultado,
        )
        resolver_relaciones = {
            Participante: lambda objeto: (
                objeto.usuario.username,
                admin.site._registry[Participante].email_usuario(objeto),
            ),
            Inscripcion: lambda objeto: (
                objeto.torneo.nombre,
                objeto.participante.nick,
            ),
            Enfrentamiento: lambda objeto: (
                objeto.juego.nombre,
                objeto.jugador_1.nick,
                objeto.jugador_2.nick,
                objeto.ganador.nick,
                objeto.resultado.torneo.nombre,
                objeto.resultado.inscripcion_a.participante.nick,
                objeto.resultado.inscripcion_b.participante.nick,
            ),
            Resultado: lambda objeto: (
                objeto.torneo.nombre,
                objeto.inscripcion_a.participante.nick,
                objeto.inscripcion_b.participante.nick,
            ),
        }

        for modelo, resolver in resolver_relaciones.items():
            with self.subTest(modelo=modelo.__name__):
                url = reverse(
                    f'admin:torneo_{modelo._meta.model_name}_changelist',
                )
                request = RequestFactory().get(url)
                request.user = administrador
                changelist = admin.site._registry[
                    modelo
                ].get_changelist_instance(request)

                with self.assertNumQueries(1):
                    for objeto in changelist.result_list:
                        resolver(objeto)


class ModeloResultadoTests(TestCase):
    def setUp(self):
        usuario_a = get_user_model().objects.create_user(
            username='jugador_a',
            password='clave-de-prueba',
        )
        usuario_b = get_user_model().objects.create_user(
            username='jugador_b',
            password='clave-de-prueba',
        )
        self.torneo = Torneo.objects.create(nombre='Torneo de prueba')
        participante_a = Participante.objects.create(
            usuario=usuario_a,
            nick='Alfil',
        )
        participante_b = Participante.objects.create(
            usuario=usuario_b,
            nick='Torre',
        )
        self.inscripcion_a = Inscripcion.objects.create(
            torneo=self.torneo,
            participante=participante_a,
        )
        self.inscripcion_b = Inscripcion.objects.create(
            torneo=self.torneo,
            participante=participante_b,
        )

    def test_victoria_calcula_ganador_y_puntos_de_clasificacion(self):
        resultado = Resultado.objects.create(
            torneo=self.torneo,
            inscripcion_a=self.inscripcion_a,
            inscripcion_b=self.inscripcion_b,
            puntos_a=3,
            puntos_b=1,
        )

        self.assertEqual(resultado.ganador, self.inscripcion_a.participante)
        self.assertEqual(resultado.puntos_clasificacion_a, 3)
        self.assertEqual(resultado.puntos_clasificacion_b, 0)
        self.assertEqual(resultado.ronda, 1)
        self.assertIsNotNone(resultado.fecha)

    def test_empate_reparte_un_punto_a_cada_participante(self):
        resultado = Resultado.objects.create(
            torneo=self.torneo,
            inscripcion_a=self.inscripcion_a,
            inscripcion_b=self.inscripcion_b,
            puntos_a=2,
            puntos_b=2,
        )

        self.assertIsNone(resultado.ganador)
        self.assertEqual(resultado.puntos_clasificacion_a, 1)
        self.assertEqual(resultado.puntos_clasificacion_b, 1)

    def test_rechaza_un_participante_enfrentado_consigo_mismo(self):
        resultado = Resultado(
            torneo=self.torneo,
            inscripcion_a=self.inscripcion_a,
            inscripcion_b=self.inscripcion_a,
            puntos_a=1,
            puntos_b=0,
        )

        with self.assertRaises(ValidationError):
            resultado.save()

    def test_clean_indica_el_campo_del_participante_repetido(self):
        resultado = Resultado(
            torneo=self.torneo,
            inscripcion_a=self.inscripcion_a,
            inscripcion_b=self.inscripcion_a,
            puntos_a=1,
            puntos_b=0,
        )

        with self.assertRaises(ValidationError) as error:
            resultado.clean()

        self.assertEqual(
            error.exception.message_dict,
            {
                'inscripcion_b': [
                    'Los dos participantes del resultado deben ser distintos.',
                ],
            },
        )

    def test_rechaza_inscripciones_de_otro_torneo(self):
        otro_torneo = Torneo.objects.create(nombre='Otro torneo')
        inscripcion_otro_torneo = Inscripcion.objects.create(
            torneo=otro_torneo,
            participante=self.inscripcion_b.participante,
        )
        resultado = Resultado(
            torneo=self.torneo,
            inscripcion_a=self.inscripcion_a,
            inscripcion_b=inscripcion_otro_torneo,
            puntos_a=1,
            puntos_b=0,
        )

        with self.assertRaises(ValidationError):
            resultado.save()

    def test_clean_indica_el_campo_de_una_inscripcion_de_otro_torneo(self):
        otro_torneo = Torneo.objects.create(nombre='Otro torneo')
        inscripcion_otro_torneo = Inscripcion.objects.create(
            torneo=otro_torneo,
            participante=self.inscripcion_b.participante,
        )
        resultado = Resultado(
            torneo=self.torneo,
            inscripcion_a=self.inscripcion_a,
            inscripcion_b=inscripcion_otro_torneo,
            puntos_a=1,
            puntos_b=0,
        )

        with self.assertRaises(ValidationError) as error:
            resultado.clean()

        self.assertEqual(
            error.exception.message_dict,
            {
                'inscripcion_b': [
                    'La inscripción debe pertenecer al torneo del resultado.',
                ],
            },
        )


class EnfrentamientoResultadoTests(TestCase):
    def setUp(self):
        usuario_a = get_user_model().objects.create_user(
            username='jugador-enfrentamiento-a',
            password='clave-de-prueba',
        )
        usuario_b = get_user_model().objects.create_user(
            username='jugador-enfrentamiento-b',
            password='clave-de-prueba',
        )
        usuario_c = get_user_model().objects.create_user(
            username='jugador-enfrentamiento-c',
            password='clave-de-prueba',
        )
        self.jugador_a = Participante.objects.create(
            usuario=usuario_a,
            nick='EnfrentamientoA',
        )
        self.jugador_b = Participante.objects.create(
            usuario=usuario_b,
            nick='EnfrentamientoB',
        )
        self.jugador_c = Participante.objects.create(
            usuario=usuario_c,
            nick='EnfrentamientoC',
        )
        self.torneo = Torneo.objects.create(
            nombre='Torneo de enfrentamientos',
        )
        self.inscripcion_a = Inscripcion.objects.create(
            torneo=self.torneo,
            participante=self.jugador_a,
        )
        self.inscripcion_b = Inscripcion.objects.create(
            torneo=self.torneo,
            participante=self.jugador_b,
        )
        self.juego = Juego.objects.create(nombre='Juego de enfrentamientos')

    def _crear_resultado(self, puntos_a=3, puntos_b=1):
        return Resultado.objects.create(
            torneo=self.torneo,
            inscripcion_a=self.inscripcion_a,
            inscripcion_b=self.inscripcion_b,
            puntos_a=puntos_a,
            puntos_b=puntos_b,
        )

    def test_enfrentamiento_sin_resultado_es_valido(self):
        enfrentamiento = Enfrentamiento.objects.create(
            juego=self.juego,
            jugador_1=self.jugador_a,
            jugador_2=self.jugador_b,
        )

        self.assertIsNone(enfrentamiento.resultado)

    def test_acepta_resultado_coherente_con_jugadores_en_cualquier_orden(self):
        resultado = self._crear_resultado()
        enfrentamiento = Enfrentamiento.objects.create(
            juego=self.juego,
            jugador_1=self.jugador_b,
            jugador_2=self.jugador_a,
            ganador=self.jugador_a,
            resultado=resultado,
        )

        self.assertEqual(enfrentamiento.resultado, resultado)

    def test_rechaza_jugadores_distintos_a_los_del_resultado(self):
        enfrentamiento = Enfrentamiento(
            juego=self.juego,
            jugador_1=self.jugador_a,
            jugador_2=self.jugador_c,
            resultado=self._crear_resultado(),
        )

        with self.assertRaises(ValidationError) as error:
            enfrentamiento.save()

        self.assertIn('resultado', error.exception.message_dict)

    def test_rechaza_ganador_distinto_al_del_resultado(self):
        enfrentamiento = Enfrentamiento(
            juego=self.juego,
            jugador_1=self.jugador_a,
            jugador_2=self.jugador_b,
            ganador=self.jugador_b,
            resultado=self._crear_resultado(),
        )

        with self.assertRaises(ValidationError) as error:
            enfrentamiento.save()

        self.assertIn('ganador', error.exception.message_dict)

    def test_rechaza_ganador_en_un_resultado_empatado(self):
        enfrentamiento = Enfrentamiento(
            juego=self.juego,
            jugador_1=self.jugador_a,
            jugador_2=self.jugador_b,
            ganador=self.jugador_a,
            resultado=self._crear_resultado(puntos_a=2, puntos_b=2),
        )

        with self.assertRaises(ValidationError) as error:
            enfrentamiento.save()

        self.assertIn('ganador', error.exception.message_dict)

    def test_al_borrar_el_resultado_se_conserva_el_enfrentamiento(self):
        resultado = self._crear_resultado()
        enfrentamiento = Enfrentamiento.objects.create(
            juego=self.juego,
            jugador_1=self.jugador_a,
            jugador_2=self.jugador_b,
            ganador=self.jugador_a,
            resultado=resultado,
        )

        resultado.delete()
        enfrentamiento.refresh_from_db()

        self.assertIsNone(enfrentamiento.resultado)
        self.assertTrue(
            Enfrentamiento.objects.filter(pk=enfrentamiento.pk).exists(),
        )


class RegistroResultadoTests(TestCase):
    def setUp(self):
        self.personal = get_user_model().objects.create_user(
            username='personal-resultados',
            password='clave-de-prueba',
            is_staff=True,
        )
        self.torneo = Torneo.objects.create(nombre='Torneo resultados')
        self.inscripcion_a = self._crear_inscripcion(
            'jugador-resultado-a',
            'JugadorResultadoA',
            self.torneo,
        )
        self.inscripcion_b = self._crear_inscripcion(
            'jugador-resultado-b',
            'JugadorResultadoB',
            self.torneo,
        )
        self.url = reverse('torneo:registrar_resultado')
        self.datos_validos = {
            'torneo': self.torneo.pk,
            'inscripcion_a': self.inscripcion_a.pk,
            'inscripcion_b': self.inscripcion_b.pk,
            'puntos_a': 3,
            'puntos_b': 1,
            'ronda': 1,
        }

    def _crear_inscripcion(self, username, nick, torneo):
        usuario = get_user_model().objects.create_user(
            username=username,
            password='clave-de-prueba',
        )
        participante = Participante.objects.create(
            usuario=usuario,
            nick=nick,
        )
        return Inscripcion.objects.create(
            torneo=torneo,
            participante=participante,
        )

    def test_personal_accede_al_formulario_de_resultados(self):
        self.client.force_login(self.personal)

        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertIsInstance(respuesta.context['form'], ResultadoForm)
        self.assertContains(respuesta, 'Participante A')
        self.assertContains(respuesta, 'Puntos del participante A')

    def test_personal_registra_un_resultado(self):
        self.client.force_login(self.personal)

        respuesta = self.client.post(self.url, self.datos_validos)

        self.assertRedirects(
            respuesta,
            self.url,
            fetch_redirect_response=False,
        )
        resultado = Resultado.objects.get()
        self.assertEqual(resultado.torneo, self.torneo)
        self.assertEqual(resultado.inscripcion_a, self.inscripcion_a)
        self.assertEqual(resultado.inscripcion_b, self.inscripcion_b)
        self.assertEqual((resultado.puntos_a, resultado.puntos_b), (3, 1))
        self.assertEqual(resultado.ronda, 1)
        self.assertIsNotNone(resultado.fecha)
        self.assertContains(
            self.client.get(self.url),
            'El resultado se ha registrado correctamente.',
        )

    def test_model_form_vincula_campos_y_muestra_errores_del_modelo(self):
        campos_esperados = (
            'torneo',
            'inscripcion_a',
            'inscripcion_b',
            'puntos_a',
            'puntos_b',
            'ronda',
        )
        formulario_valido = ResultadoForm(data=self.datos_validos)

        self.assertEqual(tuple(formulario_valido.fields), campos_esperados)
        self.assertTrue(formulario_valido.is_valid(), formulario_valido.errors)
        resultado = formulario_valido.save(commit=False)
        self.assertEqual(resultado.torneo, self.torneo)
        self.assertEqual(resultado.inscripcion_a, self.inscripcion_a)
        self.assertEqual(resultado.inscripcion_b, self.inscripcion_b)
        self.assertEqual((resultado.puntos_a, resultado.puntos_b), (3, 1))
        self.assertEqual(resultado.ronda, 1)

        formulario_invalido = ResultadoForm(
            data={
                **self.datos_validos,
                'inscripcion_b': self.inscripcion_a.pk,
            },
        )

        self.assertFalse(formulario_invalido.is_valid())
        self.assertEqual(
            formulario_invalido.errors['inscripcion_b'],
            ['Los dos participantes del resultado deben ser distintos.'],
        )

    def test_formulario_muestra_error_del_modelo_y_no_guarda(self):
        self.client.force_login(self.personal)
        datos = {
            **self.datos_validos,
            'inscripcion_b': self.inscripcion_a.pk,
        }

        respuesta = self.client.post(self.url, datos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertFormError(
            respuesta.context['form'],
            'inscripcion_b',
            'Los dos participantes del resultado deben ser distintos.',
        )
        self.assertContains(respuesta, 'role="alert"')
        self.assertFalse(Resultado.objects.exists())

    def test_formulario_rechaza_inscripcion_de_otro_torneo(self):
        otro_torneo = Torneo.objects.create(nombre='Otro torneo de resultados')
        inscripcion_otro_torneo = self._crear_inscripcion(
            'jugador-otro-torneo',
            'JugadorOtroTorneo',
            otro_torneo,
        )
        self.client.force_login(self.personal)

        respuesta = self.client.post(
            self.url,
            {
                **self.datos_validos,
                'inscripcion_b': inscripcion_otro_torneo.pk,
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFormError(
            respuesta.context['form'],
            'inscripcion_b',
            'La inscripción debe pertenecer al torneo del resultado.',
        )
        self.assertFalse(Resultado.objects.exists())

    def test_opciones_de_inscripcion_evitan_consultas_n_mas_uno(self):
        formulario = ResultadoForm()

        for nombre_campo in ('inscripcion_a', 'inscripcion_b'):
            with self.subTest(campo=nombre_campo):
                with self.assertNumQueries(2):
                    opciones = list(
                        formulario.fields[nombre_campo].choices,
                    )

                etiquetas = [etiqueta for _, etiqueta in opciones]
                self.assertTrue(
                    any(
                        'JugadorResultado' in etiqueta
                        for etiqueta in etiquetas
                    ),
                )

    def test_visitantes_y_participantes_no_pueden_registrar_resultados(self):
        usuario = get_user_model().objects.create_user(
            username='participante-sin-permisos-resultados',
            password='clave-de-prueba',
        )
        rutas = (
            ('anónimo', None),
            ('participante', usuario),
        )

        for tipo_usuario, usuario_actual in rutas:
            with self.subTest(usuario=tipo_usuario):
                if usuario_actual is None:
                    self.client.logout()
                else:
                    self.client.force_login(usuario_actual)

                respuesta = self.client.get(self.url)

                self.assertRedirects(
                    respuesta,
                    f'{reverse("admin:login")}?next={self.url}',
                )
                respuesta_post = self.client.post(
                    self.url,
                    self.datos_validos,
                )
                self.assertRedirects(
                    respuesta_post,
                    f'{reverse("admin:login")}?next={self.url}',
                )
        self.assertFalse(Resultado.objects.exists())

    def test_enlace_de_registro_solo_aparece_para_personal(self):
        self.assertNotContains(
            self.client.get(reverse('torneo:inicio')),
            'Registrar resultado',
        )
        usuario = get_user_model().objects.create_user(
            username='participante-menu-resultados',
            password='clave-de-prueba',
        )
        self.client.force_login(usuario)
        self.assertNotContains(
            self.client.get(reverse('torneo:inicio')),
            'Registrar resultado',
        )
        self.client.force_login(self.personal)
        self.assertContains(
            self.client.get(reverse('torneo:inicio')),
            f'href="{self.url}"',
        )


class GestionJuegosAdminTests(TestCase):
    def setUp(self):
        self.administrador = get_user_model().objects.create_superuser(
            username='administrador-juegos',
            email='admin-juegos@example.com',
            password='clave-de-prueba',
        )
        self.client.force_login(self.administrador)
        self.lista_url = reverse('admin:torneo_juego_changelist')
        self.agregar_url = reverse('admin:torneo_juego_add')

    def test_administrador_crea_un_juego(self):
        respuesta = self.client.post(
            self.agregar_url,
            {
                'nombre': 'Ajedrez',
                'descripcion': 'Juego de estrategia',
                'reglas': 'Mover las piezas por turnos',
                '_save': 'Guardar',
            },
        )

        self.assertRedirects(respuesta, self.lista_url)
        self.assertTrue(Juego.objects.filter(nombre='Ajedrez').exists())

    def test_administrador_edita_un_juego(self):
        juego = Juego.objects.create(nombre='Ajedrez')
        url_edicion = reverse('admin:torneo_juego_change', args=(juego.pk,))

        respuesta = self.client.post(
            url_edicion,
            {
                'nombre': 'Ajedrez rápido',
                'descripcion': 'Partidas breves',
                'reglas': 'Reloj con tiempo limitado',
                '_save': 'Guardar',
            },
        )

        self.assertRedirects(respuesta, self.lista_url)
        juego.refresh_from_db()
        self.assertEqual(juego.nombre, 'Ajedrez rápido')
        self.assertEqual(juego.descripcion, 'Partidas breves')

    def test_administrador_elimina_juego_y_enfrentamientos_asociados(self):
        juego = Juego.objects.create(nombre='Ajedrez')
        usuario_1 = get_user_model().objects.create_user(
            username='jugador-juegos-1',
            password='clave-de-prueba',
        )
        usuario_2 = get_user_model().objects.create_user(
            username='jugador-juegos-2',
            password='clave-de-prueba',
        )
        jugador_1 = Participante.objects.create(
            usuario=usuario_1,
            nick='AlfilJuegos',
        )
        jugador_2 = Participante.objects.create(
            usuario=usuario_2,
            nick='TorreJuegos',
        )
        enfrentamiento = Enfrentamiento.objects.create(
            juego=juego,
            jugador_1=jugador_1,
            jugador_2=jugador_2,
        )
        url_borrado = reverse('admin:torneo_juego_delete', args=(juego.pk,))

        respuesta = self.client.post(url_borrado, {'post': 'yes'})

        self.assertRedirects(respuesta, self.lista_url)
        self.assertFalse(Juego.objects.filter(pk=juego.pk).exists())
        self.assertFalse(
            Enfrentamiento.objects.filter(pk=enfrentamiento.pk).exists()
        )

    def test_nombre_duplicado_es_rechazado(self):
        Juego.objects.create(nombre='Ajedrez')

        respuesta = self.client.post(
            self.agregar_url,
            {
                'nombre': 'Ajedrez',
                'descripcion': '',
                'reglas': '',
                '_save': 'Guardar',
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta.context['adminform'].form.errors['nombre'])
        self.assertEqual(Juego.objects.filter(nombre='Ajedrez').count(), 1)

    def test_lista_muestra_busca_y_ordena_por_nombre(self):
        Juego.objects.create(nombre='Zelda')
        Juego.objects.create(nombre='Ajedrez')
        Juego.objects.create(nombre='Ajedrez rápido')

        respuesta_lista = self.client.get(self.lista_url)

        self.assertEqual(respuesta_lista.status_code, 200)
        nombres = [
            juego.nombre
            for juego in respuesta_lista.context['cl'].result_list
        ]
        self.assertEqual(nombres, ['Ajedrez', 'Ajedrez rápido', 'Zelda'])
        self.assertContains(respuesta_lista, 'Ajedrez')

        respuesta_busqueda = self.client.get(self.lista_url, {'q': 'Zelda'})

        self.assertEqual(respuesta_busqueda.status_code, 200)
        self.assertEqual(
            list(respuesta_busqueda.context['cl'].result_list),
            [Juego.objects.get(nombre='Zelda')],
        )
        self.assertContains(respuesta_busqueda, 'Zelda')
        self.assertNotContains(respuesta_busqueda, 'Ajedrez rápido')


class GestionParticipantesAdminTests(TestCase):
    def setUp(self):
        usuario_admin = get_user_model().objects.create_superuser(
            username='administrador-participantes',
            email='admin-participantes@example.com',
            password='clave-de-prueba',
        )
        self.usuario = get_user_model().objects.create_user(
            username='jugador-participantes',
            email='campeon@example.com',
            password='clave-de-prueba',
        )
        self.participante = Participante.objects.create(
            usuario=self.usuario,
            nick='Campeon',
        )
        self.usuario_secundario = get_user_model().objects.create_user(
            username='otro-jugador',
            email='otro-jugador@example.com',
            password='clave-de-prueba',
        )
        Participante.objects.create(
            usuario=self.usuario_secundario,
            nick='OtroNick',
        )
        self.client.force_login(usuario_admin)
        self.lista_url = reverse('admin:torneo_participante_changelist')

    def test_lista_muestra_al_participante_y_sus_datos(self):
        respuesta = self.client.get(self.lista_url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(
            self.participante,
            respuesta.context['cl'].result_list,
        )
        self.assertContains(respuesta, 'jugador-participantes')
        self.assertContains(respuesta, 'Campeon')
        self.assertContains(respuesta, 'campeon@example.com')
        self.assertContains(respuesta, 'Amateur')

    def test_busca_por_nick_y_nombre_de_usuario(self):
        for consulta in ('Campeon', 'jugador-participantes'):
            with self.subTest(consulta=consulta):
                respuesta = self.client.get(
                    self.lista_url,
                    {'q': consulta},
                )

                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(
                    list(respuesta.context['cl'].result_list),
                    [self.participante],
                )

    def test_administrador_edita_nick_nivel_y_email(self):
        url_edicion = reverse(
            'admin:torneo_participante_change',
            args=(self.participante.pk,),
        )

        respuesta = self.client.post(
            url_edicion,
            {
                'usuario': self.usuario.pk,
                'nick': 'CampeonActualizado',
                'nivel': Participante.Nivel.EXPERT,
                'email': 'campeon-actualizado@example.com',
                '_save': 'Guardar',
            },
        )

        self.assertRedirects(respuesta, self.lista_url)
        self.participante.refresh_from_db()
        self.assertEqual(self.participante.nick, 'CampeonActualizado')
        self.assertEqual(self.participante.nivel, Participante.Nivel.EXPERT)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.email, 'campeon-actualizado@example.com')

    def test_admin_rechaza_email_duplicado_sin_distinguir_mayusculas(self):
        url_edicion = reverse(
            'admin:torneo_participante_change',
            args=(self.participante.pk,),
        )

        respuesta = self.client.post(
            url_edicion,
            {
                'usuario': self.usuario.pk,
                'nick': self.participante.nick,
                'nivel': self.participante.nivel,
                'email': 'OTRO-JUGADOR@example.com',
                '_save': 'Guardar',
            },
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('email', respuesta.context['adminform'].form.errors)
        self.participante.refresh_from_db()
        self.usuario.refresh_from_db()
        self.assertEqual(self.participante.nick, 'Campeon')
        self.assertEqual(self.usuario.email, 'campeon@example.com')

    def test_admin_permite_conservar_el_email_del_usuario_actual(self):
        url_edicion = reverse(
            'admin:torneo_participante_change',
            args=(self.participante.pk,),
        )

        respuesta = self.client.post(
            url_edicion,
            {
                'usuario': self.usuario.pk,
                'nick': self.participante.nick,
                'nivel': self.participante.nivel,
                'email': 'CAMPEON@example.com',
                '_save': 'Guardar',
            },
        )

        self.assertRedirects(respuesta, self.lista_url)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.email, 'CAMPEON@example.com')


class RegistroParticipanteTests(TestCase):
    def setUp(self):
        self.url = reverse('torneo:registro')
        self.datos_validos = {
            'username': 'nuevo-participante',
            'email': 'nuevo-participante@example.com',
            'nick': 'NuevoNick',
            'nivel': Participante.Nivel.NORMAL,
            'password1': 'T0rneo-G4nador!x',
            'password2': 'T0rneo-G4nador!x',
        }

    def test_formulario_muestra_email_y_nivel(self):
        respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'name="email"')
        self.assertContains(respuesta, 'name="nivel"')

    def test_registro_correcto_crea_cuenta_perfil_y_mensaje(self):
        respuesta = self.client.post(self.url, self.datos_validos)

        self.assertRedirects(
            respuesta,
            reverse('torneo:login'),
            fetch_redirect_response=False,
        )
        usuario = get_user_model().objects.get(
            username=self.datos_validos['username'],
        )
        participante = Participante.objects.get(usuario=usuario)
        self.assertEqual(participante.nick, self.datos_validos['nick'])
        self.assertEqual(participante.nivel, self.datos_validos['nivel'])
        self.assertEqual(usuario.email, self.datos_validos['email'])

        respuesta_login = self.client.get(reverse('torneo:login'))

        self.assertTrue(respuesta_login.wsgi_request.user.is_anonymous)
        self.assertContains(
            respuesta_login,
            'Tu cuenta se ha creado correctamente. Ya puedes iniciar sesión.',
        )

    def test_datos_invalidos_no_crean_cuenta(self):
        datos = {
            **self.datos_validos,
            'password1': '123',
            'password2': '123',
        }

        respuesta = self.client.post(self.url, datos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(
            get_user_model().objects.filter(
                username=self.datos_validos['username'],
            ).exists()
        )

    def test_email_es_obligatorio(self):
        datos = {**self.datos_validos, 'email': ''}

        respuesta = self.client.post(self.url, datos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('email', respuesta.context['form'].errors)
        self.assertFalse(
            get_user_model().objects.filter(
                username=self.datos_validos['username'],
            ).exists()
        )

    def test_email_con_formato_invalido_no_se_registra(self):
        datos = {**self.datos_validos, 'email': 'correo-invalido'}

        respuesta = self.client.post(self.url, datos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('email', respuesta.context['form'].errors)
        self.assertFalse(
            get_user_model().objects.filter(
                username=self.datos_validos['username'],
            ).exists()
        )

    def test_email_duplicado_sin_distinguir_mayusculas_no_se_registra(self):
        get_user_model().objects.create_user(
            username='usuario-email-existente',
            email='existente@example.com',
            password='Otra-Clave-Segura!2026',
        )
        datos = {
            **self.datos_validos,
            'email': 'EXISTENTE@example.com',
        }

        respuesta = self.client.post(self.url, datos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn('email', respuesta.context['form'].errors)
        self.assertFalse(
            get_user_model().objects.filter(
                username=self.datos_validos['username'],
            ).exists()
        )

    def test_usuario_duplicado_no_se_registra(self):
        get_user_model().objects.create_user(
            username=self.datos_validos['username'],
            password='Otra-Clave-Segura!2026',
        )

        respuesta = self.client.post(self.url, self.datos_validos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            get_user_model().objects.filter(
                username=self.datos_validos['username'],
            ).count(),
            1,
        )

    def test_nick_duplicado_no_se_registra(self):
        usuario = get_user_model().objects.create_user(
            username='otro-participante',
            password='Otra-Clave-Segura!2026',
        )
        Participante.objects.create(
            usuario=usuario,
            nick=self.datos_validos['nick'],
        )

        respuesta = self.client.post(self.url, self.datos_validos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(
            get_user_model().objects.filter(
                username=self.datos_validos['username'],
            ).exists()
        )

    def test_contrasenas_distintas_no_se_registran(self):
        datos = {
            **self.datos_validos,
            'password2': 'Otra-Clave-Segura!2026',
        }

        respuesta = self.client.post(self.url, datos)

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(
            get_user_model().objects.filter(
                username=self.datos_validos['username'],
            ).exists()
        )


class PermisosAdministracionTests(TestCase):
    def setUp(self):
        self.juego = Juego.objects.create(nombre='Juego protegido')
        usuario_participante = get_user_model().objects.create_user(
            username='participante-permisos',
            password='clave-de-prueba',
        )
        self.participante = Participante.objects.create(
            usuario=usuario_participante,
            nick='ParticipantePermisos',
        )
        self.usuario_sin_perfil = get_user_model().objects.create_user(
            username='usuario-disponible-permisos',
            password='clave-de-prueba',
        )
        self.rutas_admin = (
            'admin:index',
            'admin:auth_user_changelist',
            'admin:torneo_juego_changelist',
            'admin:torneo_participante_changelist',
            'admin:torneo_enfrentamiento_changelist',
        )

    def test_anonimo_es_redirigido_del_panel_y_sus_listas(self):
        for nombre_ruta in self.rutas_admin:
            with self.subTest(ruta=nombre_ruta):
                ruta = reverse(nombre_ruta)
                respuesta = self.client.get(ruta)

                self.assertRedirects(
                    respuesta,
                    f'{reverse("admin:login")}?next={ruta}',
                )

    def test_anonimo_no_accede_a_gestion_de_juegos(self):
        rutas_juegos = (
            reverse('admin:torneo_juego_changelist'),
            reverse('admin:torneo_juego_add'),
            reverse('admin:torneo_juego_change', args=(self.juego.pk,)),
            reverse('admin:torneo_juego_delete', args=(self.juego.pk,)),
        )

        for ruta in rutas_juegos:
            with self.subTest(ruta=ruta):
                self.assertRedirects(
                    self.client.get(ruta),
                    f'{reverse("admin:login")}?next={ruta}',
                )

    def test_participante_no_accede_a_gestion_de_juegos(self):
        usuario_participante = get_user_model().objects.get(
            username='participante-permisos',
        )
        self.client.force_login(usuario_participante)
        rutas_juegos = (
            reverse('admin:torneo_juego_changelist'),
            reverse('admin:torneo_juego_add'),
            reverse('admin:torneo_juego_change', args=(self.juego.pk,)),
            reverse('admin:torneo_juego_delete', args=(self.juego.pk,)),
        )

        for ruta in rutas_juegos:
            with self.subTest(ruta=ruta):
                self.assertRedirects(
                    self.client.get(ruta),
                    f'{reverse("admin:login")}?next={ruta}',
                )

    def _assert_acciones_juegos_denegadas(self):
        url_agregar = reverse('admin:torneo_juego_add')
        respuesta = self.client.post(
            url_agregar,
            {
                'nombre': 'Juego no autorizado',
                'descripcion': '',
                'reglas': '',
                '_save': 'Guardar',
            },
        )
        self.assertRedirects(
            respuesta,
            f'{reverse("admin:login")}?next={url_agregar}',
        )
        self.assertFalse(
            Juego.objects.filter(nombre='Juego no autorizado').exists()
        )

        url_edicion = reverse(
            'admin:torneo_juego_change',
            args=(self.juego.pk,),
        )
        respuesta = self.client.post(
            url_edicion,
            {
                'nombre': 'Nombre modificado sin permiso',
                'descripcion': '',
                'reglas': '',
                '_save': 'Guardar',
            },
        )
        self.assertRedirects(
            respuesta,
            f'{reverse("admin:login")}?next={url_edicion}',
        )
        self.juego.refresh_from_db()
        self.assertEqual(self.juego.nombre, 'Juego protegido')

        url_borrado = reverse(
            'admin:torneo_juego_delete',
            args=(self.juego.pk,),
        )
        respuesta = self.client.post(url_borrado, {'post': 'yes'})
        self.assertRedirects(
            respuesta,
            f'{reverse("admin:login")}?next={url_borrado}',
        )
        self.assertTrue(Juego.objects.filter(pk=self.juego.pk).exists())

    def test_anonimo_no_puede_modificar_juegos_por_post(self):
        self._assert_acciones_juegos_denegadas()

    def test_participante_no_puede_modificar_juegos_por_post(self):
        usuario_participante = get_user_model().objects.get(
            username='participante-permisos',
        )
        self.client.force_login(usuario_participante)

        self._assert_acciones_juegos_denegadas()

    def _assert_acciones_participantes_denegadas(self):
        total_participantes = Participante.objects.count()
        url_agregar = reverse('admin:torneo_participante_add')
        respuesta = self.client.post(
            url_agregar,
            {
                'usuario': self.usuario_sin_perfil.pk,
                'nick': 'ParticipanteNoAutorizado',
                'nivel': Participante.Nivel.EXPERT,
                'email': 'no-autorizado@example.com',
                '_save': 'Guardar',
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertRedirects(
            respuesta,
            f'{reverse("admin:login")}?next={url_agregar}',
        )
        self.assertEqual(Participante.objects.count(), total_participantes)
        self.assertFalse(
            Participante.objects.filter(
                nick='ParticipanteNoAutorizado',
            ).exists()
        )

        url_edicion = reverse(
            'admin:torneo_participante_change',
            args=(self.participante.pk,),
        )
        respuesta = self.client.post(
            url_edicion,
            {
                'usuario': self.participante.usuario_id,
                'nick': 'NickAlteradoSinPermiso',
                'nivel': Participante.Nivel.EXPERT,
                'email': 'alterado@example.com',
                '_save': 'Guardar',
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertRedirects(
            respuesta,
            f'{reverse("admin:login")}?next={url_edicion}',
        )
        self.participante.refresh_from_db()
        self.assertEqual(self.participante.nick, 'ParticipantePermisos')
        self.assertEqual(
            self.participante.nivel,
            Participante.Nivel.AMATEUR,
        )
        self.participante.usuario.refresh_from_db()
        self.assertEqual(
            self.participante.usuario.email,
            '',
        )

        url_borrado = reverse(
            'admin:torneo_participante_delete',
            args=(self.participante.pk,),
        )
        respuesta = self.client.post(url_borrado, {'post': 'yes'})
        self.assertEqual(respuesta.status_code, 302)
        self.assertRedirects(
            respuesta,
            f'{reverse("admin:login")}?next={url_borrado}',
        )
        self.assertTrue(
            Participante.objects.filter(pk=self.participante.pk).exists()
        )

        url_lista = reverse('admin:torneo_participante_changelist')
        respuesta = self.client.post(
            url_lista,
            {
                'action': 'delete_selected',
                '_selected_action': [self.participante.pk],
                'post': 'yes',
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertRedirects(
            respuesta,
            f'{reverse("admin:login")}?next={url_lista}',
        )
        self.assertTrue(
            Participante.objects.filter(pk=self.participante.pk).exists()
        )

    def test_anonimo_no_puede_modificar_participantes_por_post(self):
        self._assert_acciones_participantes_denegadas()

    def test_participante_no_puede_modificar_participantes_por_post(self):
        usuario_participante = get_user_model().objects.get(
            username='participante-permisos',
        )
        self.client.force_login(usuario_participante)

        self._assert_acciones_participantes_denegadas()

    def test_participante_es_redirigido_del_panel_y_sus_listas(self):
        usuario_participante = get_user_model().objects.get(
            username='participante-permisos',
        )
        self.client.force_login(usuario_participante)

        for nombre_ruta in self.rutas_admin:
            with self.subTest(ruta=nombre_ruta):
                ruta = reverse(nombre_ruta)
                respuesta = self.client.get(ruta)

                self.assertRedirects(
                    respuesta,
                    f'{reverse("admin:login")}?next={ruta}',
                )

    def test_administrador_accede_al_panel_y_sus_listas(self):
        administrador = get_user_model().objects.create_user(
            username='administrador-permisos',
            password='clave-de-prueba',
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(administrador)

        for nombre_ruta in self.rutas_admin:
            with self.subTest(ruta=nombre_ruta):
                respuesta = self.client.get(reverse(nombre_ruta))

                self.assertEqual(respuesta.status_code, 200)
