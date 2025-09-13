from django.urls import path
from . import views

urlpatterns = [
    # Rotas de Autenticação
    path('login/', views.login_admin, name='login_admin'),
    path('logout/', views.logout_admin, name='logout_admin'),
    
    # Rotas Principais de Navegação
    path('dashboard/', views.dashboard_admin, name='dashboard_admin'),
    path('ver-gerentes/', views.ver_gerentes, name='ver_gerentes'),
    path('ver-predios/', views.ver_predios, name='ver_predios'),

    # Rotas para Gerentes (Adicionar, Editar, Deletar)
    path('gerentes/adicionar/', views.adicionar_gerente, name='adicionar_gerente'),
    path('gerentes/editar/<int:gerente_id>/', views.editar_gerente, name='editar_gerente'),
    path('gerentes/deletar/<int:gerente_id>/', views.deletar_gerente, name='deletar_gerente'),

    # Rotas para Prédios (Adicionar, Editar, Deletar)
    path('predios-adicionar/', views.adicionar_predio, name='adicionar_predio'),
    path('predios-editar/<int:predio_id>/', views.editar_predio, name='editar_predio'),
    path('predios-deletar/<int:predio_id>/', views.deletar_predio, name='deletar_predio'),
]