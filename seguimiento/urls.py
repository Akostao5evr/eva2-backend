from django.urls import path
from . import views

urlpatterns = [
    # Tus rutas originales
    path('dashboard/', views.dashboard_delegaciones, name='dashboard_delegaciones'),
    path('tickets/', views.listado_tickets, name='listado_tickets'),
    path('actividades/', views.listado_actividades, name='listado_actividades'),
    path('actividades/nueva/', views.crear_actividad, name='crear_actividad'),

    # Acceso y Recuperación (Diseños 1 a 4)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('recuperar/paso1/', views.recuperar_paso1, name='recuperar_paso1'),
    path('recuperar/paso2/', views.recuperar_paso2, name='recuperar_paso2'),
    path('recuperar/paso3/', views.recuperar_paso3, name='recuperar_paso3'),

    # 1. CRUD Delegaciones
    path('delegaciones/', views.listado_delegaciones, name='listado_delegaciones'),
    path('delegaciones/agregar/', views.agregar_delegacion, name='agregar_delegacion'),
    path('delegaciones/editar/<int:id>/', views.editar_delegacion, name='editar_delegacion'),
    path('delegaciones/eliminar/<int:id>/', views.eliminar_delegacion, name='eliminar_delegacion'),

    # 2. CRUD Roles (Cargos)
    path('roles/', views.listado_roles, name='listado_roles'),
    path('roles/agregar/', views.agregar_rol, name='agregar_rol'),
    path('roles/editar/<int:id>/', views.editar_rol, name='editar_rol'),
    path('roles/eliminar/<int:id>/', views.eliminar_rol, name='eliminar_rol'),

    # 3. CRUD Usuarios (Funcionarios)
    path('funcionarios/', views.listado_funcionarios, name='listado_funcionarios'),
    path('funcionarios/agregar/', views.agregar_funcionario, name='agregar_funcionario'),
    path('funcionarios/editar/<int:id>/', views.editar_funcionario, name='editar_funcionario'),
    path('funcionarios/eliminar/<int:id>/', views.eliminar_funcionario, name='eliminar_funcionario'),

    # 4. CRUD Ítems y metas
    path('items/', views.listado_items, name='listado_items'),
    path('items/agregar/', views.agregar_item, name='agregar_item'),
    path('items/editar/<int:id>/', views.editar_item, name='editar_item'),
    path('items/eliminar/<int:id>/', views.eliminar_item, name='eliminar_item'),

    # 5. CRUD Tipo de Atención
    path('tipos-atencion/', views.listado_tipos_atencion, name='listado_tipos_atencion'),
    path('tipos-atencion/agregar/', views.agregar_tipo_atencion, name='agregar_tipo_atencion'),
    path('tipos-atencion/editar/<int:id>/', views.editar_tipo_atencion, name='editar_tipo_atencion'),
    path('tipos-atencion/eliminar/<int:id>/', views.eliminar_tipo_atencion, name='eliminar_tipo_atencion'),

    # 6. CRUD Sub Atención
    path('sub-atenciones/', views.listado_sub_atenciones, name='listado_sub_atenciones'),
    path('sub-atenciones/agregar/', views.agregar_sub_atencion, name='agregar_sub_atencion'),
    path('sub-atenciones/editar/<int:id>/', views.editar_sub_atencion, name='editar_sub_atencion'),
    path('sub-atenciones/eliminar/<int:id>/', views.eliminar_sub_atencion, name='eliminar_sub_atencion'),
]