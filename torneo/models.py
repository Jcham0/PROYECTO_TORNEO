from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Juego(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    reglas = models.TextField(blank=True)

    def __str__(self):
        return self.nombre


class Participante(models.Model):
    class Nivel(models.TextChoices):
        AMATEUR = 'amateur', 'Amateur'
        NORMAL = 'normal', 'Normal'
        EXPERT = 'expert', 'Expert'

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='participante',
    )
    nick = models.CharField(max_length=50, unique=True)
    nivel = models.CharField(
        max_length=7,
        choices=Nivel.choices,
        default=Nivel.AMATEUR,
    )

    def __str__(self):
        return self.nick


class Torneo(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    inscripciones_abiertas = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Inscripcion(models.Model):
    torneo = models.ForeignKey(
        Torneo,
        on_delete=models.CASCADE,
        related_name='inscripciones',
    )
    participante = models.ForeignKey(
        Participante,
        on_delete=models.CASCADE,
        related_name='inscripciones',
    )
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('torneo', 'participante'),
                name='unica_inscripcion_por_torneo_y_participante',
            ),
        ]

    def __str__(self):
        return f'{self.participante} - {self.torneo}'


class Resultado(models.Model):
    torneo = models.ForeignKey(
        Torneo,
        on_delete=models.CASCADE,
        related_name='resultados',
    )
    inscripcion_a = models.ForeignKey(
        Inscripcion,
        on_delete=models.CASCADE,
        related_name='resultados_como_a',
    )
    inscripcion_b = models.ForeignKey(
        Inscripcion,
        on_delete=models.CASCADE,
        related_name='resultados_como_b',
    )
    puntos_a = models.PositiveIntegerField()
    puntos_b = models.PositiveIntegerField()
    fecha = models.DateTimeField(default=timezone.now)
    ronda = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(inscripcion_a=models.F('inscripcion_b')),
                name='resultado_con_dos_inscripciones_distintas',
            ),
        ]

    def clean(self):
        super().clean()
        errores = {}

        if self.inscripcion_a_id and self.inscripcion_b_id:
            inscripcion_a = self.inscripcion_a
            inscripcion_b = self.inscripcion_b
            if (
                inscripcion_a.participante_id
                == inscripcion_b.participante_id
            ):
                errores['inscripcion_b'] = (
                    'Los dos participantes del resultado deben ser distintos.'
                )

        if self.torneo_id:
            if (
                self.inscripcion_a_id
                and self.inscripcion_a.torneo_id != self.torneo_id
            ):
                errores['inscripcion_a'] = (
                    'La inscripción debe pertenecer al torneo del resultado.'
                )
            if (
                self.inscripcion_b_id
                and self.inscripcion_b.torneo_id != self.torneo_id
            ):
                errores['inscripcion_b'] = (
                    'La inscripción debe pertenecer al torneo del resultado.'
                )

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def ganador(self):
        if self.puntos_a == self.puntos_b:
            return None
        if self.puntos_a > self.puntos_b:
            return self.inscripcion_a.participante
        return self.inscripcion_b.participante

    @property
    def puntos_clasificacion_a(self):
        if self.puntos_a == self.puntos_b:
            return 1
        return 3 if self.puntos_a > self.puntos_b else 0

    @property
    def puntos_clasificacion_b(self):
        if self.puntos_a == self.puntos_b:
            return 1
        return 3 if self.puntos_b > self.puntos_a else 0

    def __str__(self):
        return (
            f'{self.torneo}: {self.inscripcion_a.participante} '
            f'{self.puntos_a} - {self.puntos_b} '
            f'{self.inscripcion_b.participante}'
        )


class Enfrentamiento(models.Model):
    juego = models.ForeignKey(
        Juego,
        on_delete=models.CASCADE,
        related_name='enfrentamientos',
    )
    jugador_1 = models.ForeignKey(
        Participante,
        on_delete=models.CASCADE,
        related_name='enfrentamientos_j1',
    )
    jugador_2 = models.ForeignKey(
        Participante,
        on_delete=models.CASCADE,
        related_name='enfrentamientos_j2',
    )
    ganador = models.ForeignKey(
        Participante,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='victorias',
    )
    fecha = models.DateTimeField(auto_now_add=True)
    finalizado = models.BooleanField(default=False)
    resultado = models.OneToOneField(
        Resultado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enfrentamiento',
    )

    def clean(self):
        super().clean()
        if not self.resultado_id:
            return

        resultado = self.resultado
        jugadores = {self.jugador_1_id, self.jugador_2_id}
        participantes = {
            resultado.inscripcion_a.participante_id,
            resultado.inscripcion_b.participante_id,
        }
        errores = {}

        if jugadores != participantes:
            errores['resultado'] = (
                'Los jugadores del enfrentamiento deben coincidir con '
                'los participantes del resultado.'
            )
        if self.ganador_id != (
            resultado.ganador.pk if resultado.ganador is not None else None
        ):
            errores['ganador'] = (
                'El ganador del enfrentamiento debe coincidir con '
                'el ganador del resultado.'
            )

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.jugador_1} vs {self.jugador_2} ({self.juego})'
