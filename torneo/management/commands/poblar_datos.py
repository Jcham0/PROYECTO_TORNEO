from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, CommandError
from django.db import transaction

from torneo.models import Inscripcion, Juego, Participante, Resultado, Torneo


class Command(BaseCommand):
    help = 'Crea o actualiza datos de demostración para el torneo.'

    password_demo = 'DemoTorneo2026!'

    participantes_demo = (
        (
            'demo_ana',
            'ana.demo@example.com',
            'DemoAna',
            Participante.Nivel.AMATEUR,
        ),
        (
            'demo_bruno',
            'bruno.demo@example.com',
            'DemoBruno',
            Participante.Nivel.NORMAL,
        ),
        (
            'demo_carla',
            'carla.demo@example.com',
            'DemoCarla',
            Participante.Nivel.EXPERT,
        ),
        (
            'demo_diego',
            'diego.demo@example.com',
            'DemoDiego',
            Participante.Nivel.NORMAL,
        ),
    )

    torneos_demo = (
        ('Demo - Copa de invierno', True),
        ('Demo - Liga de verano', False),
    )

    resultados_demo = (
        ('Demo - Copa de invierno', 1, 'demo_ana', 'demo_bruno', 3, 1),
        ('Demo - Copa de invierno', 1, 'demo_carla', 'demo_diego', 2, 2),
        ('Demo - Copa de invierno', 2, 'demo_ana', 'demo_carla', 1, 3),
        ('Demo - Copa de invierno', 2, 'demo_bruno', 'demo_diego', 2, 0),
        ('Demo - Copa de invierno', 3, 'demo_ana', 'demo_diego', 0, 1),
        ('Demo - Copa de invierno', 3, 'demo_bruno', 'demo_carla', 3, 3),
        ('Demo - Liga de verano', 1, 'demo_ana', 'demo_diego', 0, 2),
        ('Demo - Liga de verano', 1, 'demo_bruno', 'demo_carla', 3, 0),
        ('Demo - Liga de verano', 2, 'demo_ana', 'demo_carla', 2, 1),
        ('Demo - Liga de verano', 2, 'demo_bruno', 'demo_diego', 1, 1),
        ('Demo - Liga de verano', 3, 'demo_ana', 'demo_bruno', 2, 2),
        ('Demo - Liga de verano', 3, 'demo_carla', 'demo_diego', 0, 1),
    )

    @transaction.atomic
    def handle(self, *args, **options):
        totales = {
            'juegos': 0,
            'usuarios': 0,
            'participantes': 0,
            'torneos': 0,
            'inscripciones': 0,
            'resultados': 0,
        }

        for nombre, descripcion, reglas in (
            (
                'Demo - Estrategia',
                'Juego de estrategia para partidas de demostración.',
                'Gana quien obtiene más puntos.',
            ),
            (
                'Demo - Aventura',
                'Juego de aventura para partidas de demostración.',
                'Gana quien completa más objetivos.',
            ),
        ):
            _, creado = Juego.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'descripcion': descripcion,
                    'reglas': reglas,
                },
            )
            totales['juegos'] += creado

        perfiles = {}
        modelo_usuario = get_user_model()
        for username, email, nick, nivel in self.participantes_demo:
            usuario, creado = modelo_usuario.objects.get_or_create(
                username=username,
                defaults={'email': email},
            )
            if creado:
                usuario.set_password(self.password_demo)
                usuario.save(update_fields=['password'])
                totales['usuarios'] += 1

            nick_en_uso = (
                Participante.objects.filter(nick=nick)
                .exclude(usuario=usuario)
                .exists()
            )
            if nick_en_uso:
                raise CommandError(
                    f'El nick {nick} ya pertenece a otra cuenta. '
                    'Libéralo o cambia los nombres de demostración antes '
                    'de ejecutar este comando.',
                )

            perfil, creado = Participante.objects.get_or_create(
                usuario=usuario,
                defaults={'nick': nick, 'nivel': nivel},
            )
            if perfil.nick != nick:
                raise CommandError(
                    f'La cuenta {username} ya tiene el perfil {perfil.nick}; '
                    f'el comando esperaba {nick}. '
                    'No se modificaron sus datos.',
                )

            totales['participantes'] += creado
            perfiles[username] = perfil

        torneos = {}
        for nombre, inscripciones_abiertas in self.torneos_demo:
            torneo, creado = Torneo.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'descripcion': (
                        'Torneo de demostración con resultados variados.'
                    ),
                    'inscripciones_abiertas': inscripciones_abiertas,
                },
            )
            torneos[nombre] = torneo
            totales['torneos'] += creado

            for perfil in perfiles.values():
                _, creada = Inscripcion.objects.get_or_create(
                    torneo=torneo,
                    participante=perfil,
                )
                totales['inscripciones'] += creada

        for (
            nombre_torneo,
            ronda,
            username_a,
            username_b,
            puntos_a,
            puntos_b,
        ) in self.resultados_demo:
            torneo = torneos[nombre_torneo]
            inscripcion_a = Inscripcion.objects.get(
                torneo=torneo,
                participante=perfiles[username_a],
            )
            inscripcion_b = Inscripcion.objects.get(
                torneo=torneo,
                participante=perfiles[username_b],
            )
            _, creado = Resultado.objects.update_or_create(
                torneo=torneo,
                ronda=ronda,
                inscripcion_a=inscripcion_a,
                inscripcion_b=inscripcion_b,
                defaults={
                    'puntos_a': puntos_a,
                    'puntos_b': puntos_b,
                },
            )
            totales['resultados'] += creado

        resumen = ', '.join(
            f'{cantidad} {modelo}'
            for modelo, cantidad in totales.items()
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Datos de demostración disponibles ({resumen}).',
            ),
        )
        self.stdout.write(
            'La contraseña demo se asigna solo a las cuentas nuevas; '
            'las cuentas existentes no se modifican.',
        )
