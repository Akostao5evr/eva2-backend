from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.models import User, Group
from .models import Funcionario
from .forms import FuncionarioForm

# 1. READ (Listar y Buscar)
@login_required
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
@login_required
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
@login_required
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
@login_required
def eliminar_funcionario(request, id):
    funcionario = get_object_or_404(Funcionario, pk=id)
    if request.method == 'POST':
        funcionario.delete()
        return redirect('nomina_funcionarios')
        
    return render(request, 'seguimientoWeb/confirmar_eliminar.html', {
        'funcionario': funcionario
    })

def agregar_funcionario(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST)
        if form.is_valid():
            # commit=False guarda los datos en memoria sin enviarlos a la BD todavía
            funcionario = form.save(commit=False) 
            
            rut = funcionario.rut
            correo = funcionario.correo
            nombres = funcionario.nombre
            apellidos = funcionario.apellido

            # Validar que ingresó un correo (vital para recuperar contraseña)
            if not correo:
                messages.error(request, 'El correo es obligatorio para generar la cuenta de acceso.')
                return render(request, 'gestion/form_funcionario.html', {'form': form})

            # Usamos transaction.atomic para que, si algo falla, no se cree basura en la BD
            try:
                with transaction.atomic():
                    # 1. Generar contraseña segura de prueba: "Sgr@" + los primeros 4 números del RUT + "!"
                    # Ejemplo: RUT 19876543-2 -> Clave: Sgr@1987!
                    password_prueba = f"Sgr@{rut[:4]}!"

                    # 2. Crear el Usuario nativo de Django
                    user = User.objects.create_user(
                        username=rut,
                        email=correo,
                        password=password_prueba,
                        first_name=nombres,
                        last_name=apellidos
                    )

                    # 3. Asignar el perfil (Grupo) por defecto
                    # Le damos el grupo Funcionario (siempre puedes cambiarlo luego en el CRUD de Roles)
                    grupo, created = Group.objects.get_or_create(name='Funcionario')
                    user.groups.add(grupo)

                    # 4. Vincular el User al Funcionario y guardar definitivamente
                    funcionario.usuario = user
                    funcionario.save()

                    messages.success(
                        request, 
                        f'Funcionario creado exitosamente. Acceso: {rut} | Clave temporal: {password_prueba}'
                    )
                    return redirect('nomina_funcionarios')  # O el nombre de tu url de listado
                    
            except Exception as e:
                messages.error(request, f'Error interno al generar la cuenta: {str(e)}')
        else:
            messages.error(request, 'Error en el formulario. Verifica los datos ingresados.')
    else:
        form = FuncionarioForm()

    return render(request, 'gestion/form_funcionario.html', {'form': form})