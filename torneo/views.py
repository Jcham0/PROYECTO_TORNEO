from io import BytesIO

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RegistroParticipanteForm, ResultadoForm
from .models import Inscripcion, Participante, Resultado, Torneo

plt.style.use('seaborn-v0_8-darkgrid')


def _obtener_clasificaciones():
    clasificaciones_por_torneo = {
        torneo.pk: {
            'torneo': torneo,
            'participantes': {},
        }
        for torneo in Torneo.objects.order_by('nombre')
    }

    resultados = Resultado.objects.select_related(
        'torneo',
        'inscripcion_a__participante',
        'inscripcion_b__participante',
    )
    for resultado in resultados:
        participantes = clasificaciones_por_torneo[
            resultado.torneo_id
        ]['participantes']
        participante_a = resultado.inscripcion_a.participante
        participante_b = resultado.inscripcion_b.participante
        estadisticas_a = participantes.setdefault(
            participante_a.pk,
            {
                'nick': participante_a.nick,
                'jugados': 0,
                'ganados': 0,
                'perdidos': 0,
                'empatados': 0,
                'puntos': 0,
            },
        )
        estadisticas_b = participantes.setdefault(
            participante_b.pk,
            {
                'nick': participante_b.nick,
                'jugados': 0,
                'ganados': 0,
                'perdidos': 0,
                'empatados': 0,
                'puntos': 0,
            },
        )

        estadisticas_a['jugados'] += 1
        estadisticas_b['jugados'] += 1
        estadisticas_a['puntos'] += resultado.puntos_clasificacion_a
        estadisticas_b['puntos'] += resultado.puntos_clasificacion_b

        ganador = resultado.ganador
        if ganador is None:
            estadisticas_a['empatados'] += 1
            estadisticas_b['empatados'] += 1
        elif ganador.pk == participante_a.pk:
            estadisticas_a['ganados'] += 1
            estadisticas_b['perdidos'] += 1
        else:
            estadisticas_b['ganados'] += 1
            estadisticas_a['perdidos'] += 1

    clasificaciones = []
    for clasificacion_torneo in clasificaciones_por_torneo.values():
        participantes_ordenados = sorted(
            clasificacion_torneo['participantes'].values(),
            key=lambda estadisticas: (
                -estadisticas['puntos'],
                -estadisticas['ganados'],
                estadisticas['nick'].casefold(),
            ),
        )
        clasificaciones.append(
            {
                'torneo': clasificacion_torneo['torneo'],
                'participantes': participantes_ordenados,
            }
        )

    return clasificaciones


def inicio(request):
    return render(request, 'torneo/inicio.html')


def clasificacion(request):
    return render(
        request,
        'torneo/clasificacion.html',
        {'clasificaciones': _obtener_clasificaciones()},
    )


def graficas(request):
    clasificaciones = _obtener_clasificaciones()
    torneo_id = request.GET.get('torneo')

    if torneo_id:
        if not torneo_id.isdecimal():
            raise Http404
        torneo = get_object_or_404(Torneo, pk=int(torneo_id))
        clasificacion_seleccionada = next(
            clasificacion
            for clasificacion in clasificaciones
            if clasificacion['torneo'].pk == torneo.pk
        )
    elif clasificaciones:
        clasificacion_seleccionada = clasificaciones[0]
    else:
        clasificacion_seleccionada = None

    return render(
        request,
        'torneo/graficas.html',
        {
            'clasificaciones': clasificaciones,
            'clasificacion_seleccionada': clasificacion_seleccionada,
        },
    )


def grafica_torneo(request, torneo_id):
    torneo = get_object_or_404(Torneo, pk=torneo_id)
    clasificacion = next(
        clasificacion
        for clasificacion in _obtener_clasificaciones()
        if clasificacion['torneo'].pk == torneo.pk
    )
    participantes = clasificacion['participantes']
    etiquetas = [participante['nick'] for participante in participantes]
    puntos = [participante['puntos'] for participante in participantes]

    figura, eje = plt.subplots(
        figsize=(max(6, len(participantes) * 0.8), 4),
    )
    try:
        if participantes:
            eje.bar(
                etiquetas,
                puntos,
                color='#6366f1',
                width=0.45,
            )
            _estilizar_grafica(
                eje,
                f'Puntos por participante: {torneo.nombre}',
                'Puntos',
            )
        else:
            eje.text(
                0.5,
                0.5,
                'Todavía no hay resultados registrados.',
                ha='center',
                va='center',
                transform=eje.transAxes,
                fontsize=11,
                color='#64748b',
            )
            eje.set_axis_off()

        figura.set_facecolor('white')
        figura.tight_layout()
        with BytesIO() as imagen:
            figura.savefig(imagen, format='png', bbox_inches='tight')
            contenido = imagen.getvalue()
    finally:
        plt.close(figura)

    return HttpResponse(contenido, content_type='image/png')


def _estilizar_grafica(eje, titulo, etiqueta_y):
    eje.set_xlabel('Participante', fontsize=10, color='#475569', labelpad=10)
    eje.set_ylabel(etiqueta_y, fontsize=10, color='#475569', labelpad=10)
    eje.set_title(
        titulo,
        loc='left',
        fontsize=14,
        fontweight='bold',
        color='#0f172a',
        pad=16,
    )
    eje.set_facecolor('white')
    eje.spines['top'].set_visible(False)
    eje.spines['right'].set_visible(False)
    eje.spines['left'].set_visible(False)
    eje.spines['bottom'].set_color('#e2e8f0')
    eje.spines['bottom'].set_linewidth(0.8)
    eje.tick_params(axis='x', labelrotation=35, labelsize=9, colors='#475569')
    eje.tick_params(
        axis='y',
        which='both',
        length=0,
        labelleft=False,
    )
    eje.grid(axis='y', color='#f1f5f9', linewidth=0.8)
    eje.grid(axis='x', visible=False)
    eje.set_axisbelow(True)
    eje.margins(x=0.08)


def grafica_victorias_torneo(request, torneo_id):
    torneo = get_object_or_404(Torneo, pk=torneo_id)
    clasificacion = next(
        clasificacion
        for clasificacion in _obtener_clasificaciones()
        if clasificacion['torneo'].pk == torneo.pk
    )
    participantes = clasificacion['participantes']

    figura, eje = plt.subplots(
        figsize=(max(6, len(participantes) * 0.8), 4),
    )
    try:
        if participantes:
            nicks = [participante['nick'] for participante in participantes]
            victorias = [
                participante['ganados']
                for participante in participantes
            ]
            eje.bar(
                nicks,
                victorias,
                color='#6366f1',
                width=0.45,
            )
            _estilizar_grafica(
                eje,
                f'Victorias por participante: {torneo.nombre}',
                'Victorias',
            )
        else:
            eje.text(
                0.5,
                0.5,
                'Todavía no hay resultados registrados.',
                ha='center',
                va='center',
                transform=eje.transAxes,
                fontsize=11,
                color='#64748b',
            )
            eje.set_axis_off()

        figura.set_facecolor('white')
        figura.tight_layout()
        with BytesIO() as imagen:
            figura.savefig(imagen, format='png', bbox_inches='tight')
            contenido = imagen.getvalue()
    finally:
        plt.close(figura)

    return HttpResponse(contenido, content_type='image/png')


@login_required
def zona_participante(request):
    participante = Participante.objects.filter(usuario=request.user).first()
    if participante is None:
        if request.method == 'POST':
            raise PermissionDenied
        messages.error(
            request,
            'Tu cuenta no tiene un perfil de participante.',
        )
        return render(request, 'torneo/zona_participante.html')

    if request.method == 'POST':
        accion = request.POST.get('accion')
        torneo_id = request.POST.get('torneo_id', '')
        if (
            accion not in ('apuntarse', 'desapuntarse')
            or not torneo_id.isdecimal()
        ):
            return HttpResponseBadRequest('La acción o el torneo no son válidos.')

        torneo = get_object_or_404(Torneo, pk=torneo_id)
        if not torneo.inscripciones_abiertas:
            messages.error(
                request,
                'Las inscripciones de este torneo están cerradas.',
            )
            return redirect('torneo:zona_participante')

        if accion == 'apuntarse':
            _, creada = Inscripcion.objects.get_or_create(
                torneo=torneo,
                participante=participante,
            )
            if creada:
                messages.success(request, 'Te has apuntado al torneo.')
            else:
                messages.info(request, 'Ya estás inscrito en este torneo.')
        else:
            eliminadas, _ = Inscripcion.objects.filter(
                torneo=torneo,
                participante=participante,
            ).delete()
            if eliminadas:
                messages.success(request, 'Te has dado de baja del torneo.')
            else:
                messages.warning(request, 'No estabas inscrito en este torneo.')

        return redirect('torneo:zona_participante')

    mis_inscripciones = (
        Inscripcion.objects.filter(participante=participante)
        .select_related('torneo')
        .order_by('torneo__nombre')
    )
    torneos_disponibles = (
        Torneo.objects.filter(inscripciones_abiertas=True)
        .exclude(pk__in=mis_inscripciones.values_list('torneo_id', flat=True))
        .order_by('nombre')
    )
    return render(
        request,
        'torneo/zona_participante.html',
        {
            'participante': participante,
            'mis_inscripciones': mis_inscripciones,
            'torneos_disponibles': torneos_disponibles,
        },
    )


def registro_participante(request):
    if request.method == 'POST':
        form = RegistroParticipanteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Tu cuenta se ha creado correctamente. Ya puedes iniciar sesión.',
            )
            return redirect('torneo:login')
    else:
        form = RegistroParticipanteForm()

    return render(request, 'torneo/registro.html', {'form': form})


@staff_member_required
def registrar_resultado(request):
    if request.method == 'POST':
        form = ResultadoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'El resultado se ha registrado correctamente.')
            return redirect('torneo:registrar_resultado')
    else:
        form = ResultadoForm()

    return render(
        request,
        'torneo/registrar_resultado.html',
        {'form': form},
    )
