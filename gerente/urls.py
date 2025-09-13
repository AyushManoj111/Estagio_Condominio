# gerente/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Rotas de Autenticação (assumindo que já existem)
    path('login/', views.login_gerente, name='login_gerente'),
    path('logout/', views.logout_gerente, name='logout_gerente'),

    # Dashboard
    path('dashboard/', views.dashboard_gerente, name='dashboard_gerente'),

    # Gestão de Casas
    path('casas/', views.ver_casas, name='ver_casas'),
    path('casas/adicionar/', views.adicionar_casa, name='adicionar_casa'),
    path('casas/<int:casa_id>/editar/', views.editar_casa, name='editar_casa'),
    path('casas/<int:casa_id>/excluir/', views.excluir_casa, name='excluir_casa'),

    # Gestão de Inquilinos
    path('inquilinos/', views.ver_inquilinos, name='ver_inquilinos'),
    path('inquilinos/adicionar/', views.adicionar_inquilino, name='adicionar_inquilino'),
    path('inquilinos/<int:inquilino_id>/editar/', views.editar_inquilino, name='editar_inquilino'),
    path('inquilinos/<int:inquilino_id>/excluir/', views.excluir_inquilino, name='excluir_inquilino'),

    # Gestão de Manutenções
    path('manutencoes/', views.ver_manutencoes, name='ver_manutencoes'),
    path('manutencoes/<int:manutencao_id>/atualizar-estado/', views.atualizar_estado_manutencao, name='atualizar_estado_manutencao'),
    path('manutencoes/adicionar/', views.adicionar_manutencao, name='adicionar_manutencao'),
    path('manutencoes/excluir/<int:manutencao_id>/', views.excluir_manutencao, name='excluir_manutencao'),
]