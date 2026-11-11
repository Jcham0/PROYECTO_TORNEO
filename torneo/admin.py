from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import (
    Enfrentamiento,
    Inscripcion,
    Juego,
    Participante,
    Resultado,
    Torneo,
)


class ParticipanteAdminForm(forms.ModelForm):
    email = forms.EmailField(
        label='Correo electrónico',
        required=False,
    )

    class Meta:
        model = Participante
        fields = ('usuario', 'nick', 'nivel', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['email'] = self.instance.usuario.email

    def clean_email(self):
        email = self.cleaned_data['email']
        if not email:
            return email

        usuarios = get_user_model().objects.filter(email__iexact=email)
        usuario = self.cleaned_data.get('usuario')
        if usuario:
            usuarios = usuarios.exclude(pk=usuario.pk)
        if usuarios.exists():
            raise ValidationError(
                'Ya existe una cuenta con ese correo electrónico.',
            )
        return email


@admin.register(Juego)
class JuegoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)
    ordering = ('nombre',)
    fields = ('nombre', 'descripcion', 'reglas')


@admin.register(Participante)
class ParticipanteAdmin(admin.ModelAdmin):
    form = ParticipanteAdminForm
    list_display = ('usuario', 'nick', 'nivel', 'email_usuario')
    list_select_related = ('usuario',)
    search_fields = ('nick', 'usuario__username', 'usuario__email')
    ordering = ('nick',)
    fields = ('usuario', 'nick', 'nivel', 'email')

    @admin.display(description='Correo electrónico', ordering='usuario__email')
    def email_usuario(self, participante):
        return participante.usuario.email

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        usuario = obj.usuario
        email = form.cleaned_data['email']
        if usuario.email != email:
            usuario.email = email
            usuario.save(update_fields=('email',))


@admin.register(Torneo)
class TorneoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'inscripciones_abiertas')
    list_filter = ('inscripciones_abiertas',)
    search_fields = ('nombre',)
    ordering = ('nombre',)
    fields = ('nombre', 'descripcion', 'inscripciones_abiertas')


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('torneo', 'participante', 'fecha_inscripcion')
    list_filter = ('torneo',)
    search_fields = ('torneo__nombre', 'participante__nick')
    ordering = ('torneo__nombre', 'participante__nick')
    list_select_related = ('torneo', 'participante')


@admin.register(Enfrentamiento)
class EnfrentamientoAdmin(admin.ModelAdmin):
    list_display = (
        'juego',
        'jugador_1',
        'jugador_2',
        'ganador',
        'resultado',
        'finalizado',
        'fecha',
    )
    list_select_related = (
        'juego',
        'jugador_1',
        'jugador_2',
        'ganador',
        'resultado__torneo',
        'resultado__inscripcion_a__participante',
        'resultado__inscripcion_b__participante',
    )


@admin.register(Resultado)
class ResultadoAdmin(admin.ModelAdmin):
    list_display = (
        'torneo',
        'inscripcion_a',
        'inscripcion_b',
        'puntos_a',
        'puntos_b',
        'ronda',
        'fecha',
    )
    list_select_related = (
        'torneo',
        'inscripcion_a__participante',
        'inscripcion_b__participante',
    )
    list_filter = ('torneo', 'ronda')
    search_fields = (
        'torneo__nombre',
        'inscripcion_a__participante__nick',
        'inscripcion_b__participante__nick',
    )
    ordering = ('torneo__nombre', 'ronda', 'fecha')
