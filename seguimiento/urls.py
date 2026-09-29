from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_delegaciones, name='dashboard_delegaciones'),
    path('tickets/', views.listado_tickets, name='listado_tickets'),
    path('actividades/', views.listado_actividades, name='listado_actividades'),
    path('funcionarios/', views.listado_funcionarios, name='listado_funcionarios'),
    path('funcionarios/agregar/', views.agregar_funcionario, name='agregar_funcionario'),
    path('funcionarios/editar/<int:id>/', views.editar_funcionario, name='editar_funcionario'),
    path('funcionarios/eliminar/<int:id>/', views.eliminar_funcionario, name='eliminar_funcionario'),
    path('actividades/nueva/', views.crear_actividad, name='crear_actividad'),
]