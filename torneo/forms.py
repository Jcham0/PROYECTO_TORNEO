from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Inscripcion, Participante, Resultado


class RegistroParticipanteForm(UserCreationForm):
    email = forms.EmailField(label='Correo electrónico')
    nick = forms.CharField(max_length=50, label='Nick')
    nivel = forms.ChoiceField(
        choices=Participante.Nivel.choices,
        label='Nivel',
    )
    field_order = (
        'username',
        'email',
        'nick',
        'nivel',
        'password1',
        'password2',
    )

    class Meta(UserCreationForm.Meta):
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data['email']
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise ValidationError(
                'Ya existe una cuenta con ese correo electrónico.',
            )
        return email

    def clean_nick(self):
        nick = self.cleaned_data['nick']
        if Participante.objects.filter(nick=nick).exists():
            raise ValidationError('Ya existe un participante con ese nick.')
        return nick

    @transaction.atomic
    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.email = self.cleaned_data['email']
        if commit:
            usuario.save()
            Participante.objects.create(
                usuario=usuario,
                nick=self.cleaned_data['nick'],
                nivel=self.cleaned_data['nivel'],
            )
        return usuario


class ResultadoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        inscripciones = Inscripcion.objects.select_related(
            'torneo',
            'participante',
        )
        self.fields['inscripcion_a'].queryset = inscripciones
        self.fields['inscripcion_b'].queryset = inscripciones

    class Meta:
        model = Resultado
        fields = (
            'torneo',
            'inscripcion_a',
            'inscripcion_b',
            'puntos_a',
            'puntos_b',
            'ronda',
        )
        labels = {
            'torneo': 'Torneo',
            'inscripcion_a': 'Participante A',
            'inscripcion_b': 'Participante B',
            'puntos_a': 'Puntos del participante A',
            'puntos_b': 'Puntos del participante B',
            'ronda': 'Ronda',
        }
