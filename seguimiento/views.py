from django.shortcuts import render, redirect, get_object_or_404
from .models import CompromisoTicket, Actividad
from gestion.models import Funcionario, Delegacion
from .forms import FuncionarioForm

# 1. Vista de Tickets y Semáforo
def listado_tickets(request):
    tickets = CompromisoTicket.objects.select_related('delegacion', 'funcionario_asignado').all()
    return render(request, 'seguimientoWeb/listado_tickets.html', {'tickets': tickets})

# 2. Vista de Actividades y Evidencias
def listado_actividades(request):
    actividades = Actividad.objects.select_related('funcionario', 'delegacion').all()
    return render(request, 'seguimientoWeb/listado_actividades.html', {'actividades': actividades})

# 3. Vista de Funcionarios (READ + Búsqueda)
def listado_funcionarios(request):
    query = request.GET.get('q', '')
    if query:
        funcionarios = Funcionario.objects.filter(rut__icontains=query).select_related('delegacion', 'cargo')
    else:
        funcionarios = Funcionario.objects.select_related('delegacion', 'cargo').all()

    return render(request, 'seguimientoWeb/listado_funcionarios.html', {
        'funcionarios': funcionarios,
        'query': query
    })

# 3.1 Agregar Funcionario (CREATE)
def agregar_funcionario(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listado_funcionarios')
    else:
        form = FuncionarioForm()
        
    return render(request, 'seguimientoWeb/form_funcionario.html', {
        'form': form, 
        'titulo': 'Agregar Nuevo Funcionario'
    })

# 3.2 Editar Funcionario (UPDATE)
def editar_funcionario(request, id):
    funcionario = get_object_or_404(Funcionario, pk=id)
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, instance=funcionario)
        if form.is_valid():
            form.save()
            return redirect('listado_funcionarios')
    else:
        form = FuncionarioForm(instance=funcionario)
        
    return render(request, 'seguimientoWeb/form_funcionario.html', {
        'form': form, 
        'titulo': f'Modificar Funcionario: {funcionario.nombre} {funcionario.apellido}'
    })

# 3.3 Eliminar Funcionario (DELETE)
def eliminar_funcionario(request, id):
    funcionario = get_object_or_404(Funcionario, pk=id)
    if request.method == 'POST':
        funcionario.delete()
        return redirect('listado_funcionarios')
        
    return render(request, 'seguimientoWeb/confirmar_eliminar.html', {
        'funcionario': funcionario
    })

# 4. Vista Dashboard / Resumen de Delegación
def dashboard_delegaciones(request):
    total_tickets = CompromisoTicket.objects.count()
    tickets_a_tiempo = CompromisoTicket.objects.filter(estado_color='VERDE').count()
    tickets_vencidos = CompromisoTicket.objects.filter(estado_color='ROJO').count()
    delegaciones = Delegacion.objects.all()

    context = {
        'total_tickets': total_tickets,
        'tickets_a_tiempo': tickets_a_tiempo,
        'tickets_vencidos': tickets_vencidos,
        'delegaciones': delegaciones,
    }
    return render(request, 'seguimientoWeb/dashboard.html', context)