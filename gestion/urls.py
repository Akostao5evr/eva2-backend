from django.urls import path
from . import views

urlpatterns = [
    path('funcionarios/', views.listar_funcionarios, name='nomina_funcionarios'),
    path('funcionarios/agregar/', views.agregar_funcionario, name='agregar_funcionario'),
    path('funcionarios/editar/<int:id>/', views.editar_funcionario, name='editar_funcionario'),
    path('funcionarios/eliminar/<int:id>/', views.eliminar_funcionario, name='eliminar_funcionario'),
]