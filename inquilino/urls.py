# urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Rotas de Autenticação
    path('login/', views.login_inquilino, name='login_inquilino'),
    path('logout/', views.logout_inquilino, name='logout_inquilino'),
    
    # Rotas do Dashboard e Páginas Principais
    path('dashboard/', views.dashboard_inquilino, name='dashboard_inquilino'),
    path('dados-pessoais/', views.dados_pessoais_inquilino, name='dados_pessoais_inquilino'),
    
    # Rotas de Manutenção (Agora são apenas duas)
    path('manutencoes/adicionar/', views.adicionar_manutencoes, name='adicionar_manutencoes'),
    path('manutencoes/ver/', views.ver_manutencoes_inquilino, name='ver_manutencoes_inquilino'),
]