from django.db.models import F, Q, Sum
from django.shortcuts import render

from AdminApp.models import Usuario
from CoordinadorApp.models import Desempeno, Periodo
from DelegadoApp.models import Compromiso
from FuncionarioApp.models import Registro
from SupervisorApp.models import Evidencia
from config.decorators import cargo_required


@cargo_required('vistaf', 'consulta', 'usuario de consulta')
def home(request):
	registros = Registro.objects.all()
	compromisos = Compromiso.objects.all()
	evidencias = Evidencia.objects.filter(estado=Evidencia.Estado.PENDIENTE)
	desempenos = Desempeno.objects.all()
	query = request.GET.get('q', '').strip()

	delegation = request.user.delegacion_actual
	if delegation:
		delegation_id = delegation.delegacion_id
		registros = registros.filter(
			autor__usuariodelegacion__delegacion_id=delegation_id,
			autor__usuariodelegacion__fecha_fin__isnull=True,
		).distinct()
		compromisos = compromisos.filter(agenda__delegacion_id=delegation_id)
		evidencias = evidencias.filter(
			registro__autor__usuariodelegacion__delegacion_id=delegation_id,
			registro__autor__usuariodelegacion__fecha_fin__isnull=True,
		) | evidencias.filter(compromiso__agenda__delegacion_id=delegation_id)
		desempenos = desempenos.filter(
			usuario__usuariodelegacion__delegacion_id=delegation_id,
			usuario__usuariodelegacion__fecha_fin__isnull=True,
		).distinct()
		scope_label = delegation.delegacion.nombre
	elif request.user.is_superuser:
		scope_label = 'Visión general'
	else:
		registros = registros.none()
		compromisos = compromisos.none()
		evidencias = evidencias.none()
		desempenos = desempenos.none()
		scope_label = 'Sin delegación asignada'

	if query:
		desempenos = desempenos.filter(
			Q(usuario__email__icontains=query)
			| Q(usuario__first_name__icontains=query)
			| Q(usuario__last_name__icontains=query)
			| Q(item__nombre__icontains=query)
			| Q(periodo__nombre__icontains=query)
		)

	summary = desempenos.values(
		delegacion=F('usuario__usuariodelegacion__delegacion__nombre'),
		periodo_nombre=F('periodo__nombre'),
	).annotate(meta_total=Sum('meta'), avance_total=Sum('avance')).order_by(
		'delegacion', 'periodo_nombre',
	)[:30]
	return render(request, 'VistaFApp/index.html', {
		'sgr_role': 'Consulta',
		'scope_label': scope_label,
		'query': query,
		'sidebar_modules': ('Búsqueda de información',),
		'registro_count': registros.count(),
		'compromiso_count': compromisos.count(),
		'evidencia_count': evidencias.count(),
		'periodo_count': Periodo.objects.filter(estado=Periodo.Estado.ABIERTO).count(),
		'summary': summary,
	})
