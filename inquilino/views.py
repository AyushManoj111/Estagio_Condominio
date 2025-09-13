# Certifique-se de que estes imports estão no seu arquivo views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required, user_passes_test
from gerente.models import Inquilino, Casa, Manutencao, Contratos
from .models import PagamentoRenda
from django.db import transaction
from django.db.models import Q
from datetime import date
from dateutil.relativedelta import relativedelta
import uuid

# --- Funções auxiliares para verificação de permissões ---
def is_inquilino(user):
    """
    Verifica se o utilizador está autenticado e pertence ao grupo 'Inquilino'.
    """
    return user.is_authenticated and user.groups.filter(name='Inquilino').exists()

def login_inquilino(request):
    """
    View para o inquilino fazer login.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 1. Autenticar o utilizador com as credenciais fornecidas
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # 2. Verificar se o utilizador pertence ao grupo 'Inquilino'
            try:
                if user.groups.filter(name='Inquilino').exists():
                    login(request, user)
                    messages.success(request, 'Login de inquilino realizado com sucesso!')
                    return redirect('dashboard_inquilino')  # Substitua pela sua URL de dashboard de inquilino
                else:
                    messages.error(request, 'Credenciais inválidas ou não pertence ao grupo Inquilino.')
            except Group.DoesNotExist:
                messages.error(request, 'Grupo "Inquilino" não encontrado. Verifique se o grupo foi criado.')
        else:
            messages.error(request, 'Nome de utilizador ou senha inválidos.')
    
    return render(request, 'inquilino/login_inquilino.html')  # Substitua pelo seu template de login de inquilino

def logout_inquilino(request):
    """
    View para o inquilino fazer logout.
    """
    logout(request)
    messages.success(request, 'Logout realizado com sucesso.')
    return redirect('login_inquilino')

@login_required(login_url='login_inquilino')
@user_passes_test(is_inquilino)
def dashboard_inquilino(request):
    """
    View para o dashboard principal do inquilino.
    Não contém mais formulários ou informações pessoais.
    """
    inquilino = request.user.inquilino
    
    context = {
        'inquilino': inquilino,
    }
    return render(request, 'inquilino/dashboard_inquilino.html', context)

@login_required(login_url='login_inquilino')
@user_passes_test(is_inquilino)
def dados_pessoais_inquilino(request):
    """
    View para exibir as informações de perfil e casa do inquilino.
    """
    inquilino = request.user.inquilino
    
    try:
        casa = Casa.objects.get(inquilino=inquilino)
    except Casa.DoesNotExist:
        casa = None
    
    context = {
        'inquilino': inquilino,
        'casa': casa,
    }
    return render(request, 'inquilino/dados_pessoais_inquilino.html', context)


@login_required(login_url='login_inquilino')
@user_passes_test(is_inquilino)
def ver_manutencoes_inquilino(request):
    """
    View para exibir o histórico de todas as solicitações de manutenção do inquilino.
    """
    inquilino = request.user.inquilino
    manutencoes = Manutencao.objects.filter(solicitado_por_inquilino=inquilino).order_by('-data_solicitacao')
    
    context = {
        'inquilino': inquilino,
        'manutencoes': manutencoes,
    }
    return render(request, 'inquilino/ver_manutencoes_inquilino.html', context)


@login_required(login_url='login_inquilino')
@user_passes_test(is_inquilino)
def adicionar_manutencoes(request):
    """
    View que lida com a exibição do formulário (GET) e o processamento (POST).
    """
    inquilino = request.user.inquilino
    try:
        casa = Casa.objects.get(inquilino=inquilino)
    except Casa.DoesNotExist:
        casa = None
    
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        descricao = request.POST.get('descricao')
        
        if not casa:
            messages.error(request, 'Não foi possível encontrar uma casa associada a este perfil. Solicitação não enviada.')
            return redirect('adicionar_manutencoes')
            
        if tipo == 'geral':
            messages.error(request, 'Não é possível solicitar manutenção do tipo "Geral". Por favor, selecione outro tipo.')
            return redirect('adicionar_manutencoes')
        
        try:
            Manutencao.objects.create(
                solicitado_por_inquilino=inquilino,
                casa=casa,
                tipo=tipo,
                descricao=descricao
            )
            messages.success(request, 'Sua solicitação de manutenção foi enviada com sucesso!')
            return redirect('ver_manutencoes_inquilino')
        except Exception as e:
            messages.error(request, f'Erro ao enviar a solicitação: {e}')
            return redirect('adicionar_manutencoes')

    # GET request - Exibe o formulário
    context = {
        'inquilino': inquilino,
        'casa': casa,
        'manutencao_choices': Manutencao.TIPO_CHOICES,
    }
    return render(request, 'inquilino/adicionar_manutencoes.html', context)

@user_passes_test(is_inquilino, login_url='login_inquilino')
def ver_financas(request):
    try:
        inquilino = request.user.inquilino
        contrato_ativo = Contratos.objects.filter(inquilino=inquilino).order_by('-data_inicio').first()

        pagamentos = []
        if contrato_ativo:
            # Gerar pagamentos para a duração total do contrato
            gerar_pagamentos_em_falta(contrato_ativo)

            # Obter todos os pagamentos para este contrato
            pagamentos = PagamentoRenda.objects.filter(contrato=contrato_ativo).order_by('mes_referencia')

    except Exception as e:
        pagamentos = []
        messages.error(request, f'Ocorreu um erro ao carregar as finanças: {e}')

    context = {
        'pagamentos': pagamentos,
    }
    return render(request, 'inquilino/financas.html', context)

def gerar_pagamentos_em_falta(contrato):
    """
    Função auxiliar para gerar pagamentos mensais para a duração total de um contrato.
    """
    # Encontrar a data final do contrato
    data_fim_contrato = contrato.data_inicio + relativedelta(months=contrato.duracao_meses)
    
    # Encontrar a data do último pagamento gerado
    ultimo_pagamento = PagamentoRenda.objects.filter(contrato=contrato).order_by('-mes_referencia').first()
    
    if ultimo_pagamento:
        mes_inicio_geracao = ultimo_pagamento.mes_referencia + relativedelta(months=1)
    else:
        mes_inicio_geracao = date(contrato.data_inicio.year, contrato.data_inicio.month, 1)

    # Gerar pagamentos até a data final do contrato
    while mes_inicio_geracao < data_fim_contrato:
        # Gerar uma referência única para o pagamento
        referencia = f"{contrato.id}-{mes_inicio_geracao.year}{mes_inicio_geracao.month:02d}-{uuid.uuid4().hex[:6]}"
        
        PagamentoRenda.objects.get_or_create(
            contrato=contrato,
            mes_referencia=mes_inicio_geracao,
            defaults={
                'valor': contrato.valor_renda,
                'entidade': '9501',
                'referencia': referencia,
            }
        )
        mes_inicio_geracao += relativedelta(months=1)


@user_passes_test(is_inquilino, login_url='login_inquilino')
def pagar_renda(request, pk):
    """
    Simula o pagamento de uma renda.
    """
    if request.method == 'POST':
        pagamento = get_object_or_404(PagamentoRenda, pk=pk)
        
        # O inquilino só pode pagar se for o seu próprio pagamento
        if pagamento.contrato.inquilino.user != request.user:
            messages.error(request, 'Não tem permissão para realizar esta ação.')
            return redirect('ver_financas')

        if pagamento.estado == 'nao_pago':
            with transaction.atomic():
                pagamento.estado = 'pago'
                pagamento.save()
            messages.success(request, f'Pagamento de {pagamento.mes_referencia.strftime("%B/%Y")} efetuado com sucesso!')
        else:
            messages.info(request, 'Este pagamento já foi efetuado.')
    
    return redirect('ver_financas')