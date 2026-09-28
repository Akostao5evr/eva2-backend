from django.shortcuts import render, redirect, get_object_or_404
from .models import Funcionario
from .forms import FuncionarioForm

# 1. READ (Listar y Buscar)
def listar_funcionarios(request):
    query = request.GET.get('q', '')
    if query:
        funcionarios = Funcionario.objects.filter(rut__icontains=query).select_related('delegacion', 'cargo')
    else:
        funcionarios = Funcionario.objects.select_related('delegacion', 'cargo').all()

    return render(request, 'seguimientoWeb/listado_funcionarios.html', {
        'funcionarios': funcionarios,
        'query': query
    })

# 2. CREATE (Agregar)
def agregar_funcionario(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('nomina_funcionarios')
    else:
        form = FuncionarioForm()
        
    return render(request, 'seguimientoWeb/form_funcionario.html', {
        'form': form, 
        'titulo': 'Agregar Nuevo Funcionario'
    })

# 3. UPDATE (Modificar)
def editar_funcionario(request, id):
    funcionario = get_object_or_404(Funcionario, pk=id)
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, instance=funcionario)
        if form.is_valid():
            form.save()
            return redirect('nomina_funcionarios')
    else:
        form = FuncionarioForm(instance=funcionario)
        
    return render(request, 'seguimientoWeb/form_funcionario.html', {
        'form': form, 
        'titulo': f'Modificar Funcionario: {funcionario.nombre} {funcionario.apellido}'
    })

# 4. DELETE (Eliminar)
def eliminar_funcionario(request, id):
    funcionario = get_object_or_404(Funcionario, pk=id)
    if request.method == 'POST':
        funcionario.delete()
        return redirect('nomina_funcionarios')
        
    return render(request, 'seguimientoWeb/confirmar_eliminar.html', {
        'funcionario': funcionario
    })