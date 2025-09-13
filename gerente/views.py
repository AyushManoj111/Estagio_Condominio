from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from .models import Casa, Gerente, Predio, Inquilino, Manutencao
from django.db.models import Q

# --- Funções auxiliares para verificação de permissões ---
def is_gerente(user):
    """
    Verifica se o utilizador está autenticado e pertence ao grupo 'Gerente'.
    """
    return user.is_authenticated and user.groups.filter(name='Gerente').exists()

def login_gerente(request):
    """
    View para o Gerente fazer login.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 1. Autenticar o utilizador com as credenciais fornecidas
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # 2. Verificar se o utilizador pertence ao grupo 'Gerente'
            try:
                if user.groups.filter(name='Gerente').exists():
                    login(request, user)
                    messages.success(request, 'Login de Gerente realizado com sucesso!')
                    return redirect('dashboard_gerente')  # Substitua 'dashboard_gerente' pela sua URL de dashboard
                else:
                    messages.error(request, 'Credenciais inválidas ou não pertence ao grupo Gerente.')
            except Group.DoesNotExist:
                messages.error(request, 'Grupo "Gerente" não encontrado. Verifique se o grupo foi criado.')
        else:
            messages.error(request, 'Nome de utilizador ou senha inválidos.')
    
    return render(request, 'gerente/login_gerente.html')  # Substitua pelo seu template de login de Gerente

def logout_gerente(request):
    """
    View para o gerente fazer logout.
    """
    logout(request)
    messages.success(request, 'Logout realizado com sucesso.')
    return redirect('login_gerente')


@user_passes_test(is_gerente, login_url='login_gerente')
def dashboard_gerente(request):
    """
    View do dashboard para o Gerente.
    Requer autenticação e verifica se o utilizador pertence ao grupo 'Gerente'.
    """
    context = {}
    return render(request, 'gerente/dashboard_gerente.html', context)


@user_passes_test(is_gerente, login_url='login_gerente')
def ver_casas(request):
    """
    Exibe uma lista de casas pertencentes ao Gerente logado.
    """
    try:
        # Pega a instância do Gerente associada ao usuário logado.
        gerente = request.user.gerente
        
        # Filtra as casas que pertencem aos prédios do gerente.
        casas = Casa.objects.filter(predio__gerente=gerente).order_by('predio__nome', 'numero')
        
    except Gerente.DoesNotExist:
        # Caso o usuário logado não tenha um perfil de Gerente.
        casas = []
        
    context = {
        'casas': casas
    }
    return render(request, 'gerente/ver_casas.html', context)


@user_passes_test(is_gerente, login_url='login_gerente')
def adicionar_casa(request):
    """
    Permite ao Gerente adicionar uma nova casa usando formulário HTML puro.
    """
    gerente = request.user.gerente
    predios_do_gerente = Predio.objects.filter(gerente=gerente)
    inquilinos_disponiveis = Inquilino.objects.all()

    if request.method == 'POST':
        numero = request.POST.get('numero')
        predio_id = request.POST.get('predio')
        inquilino_id = request.POST.get('inquilino')

        # 1. Validação básica
        if not numero or not predio_id:
            messages.error(request, 'O número da casa e o prédio são obrigatórios.')
            return redirect('adicionar_casa')

        # 2. Verifica se o prédio pertence ao gerente
        predio = get_object_or_404(Predio, id=predio_id, gerente=gerente)
        
        inquilino = None
        if inquilino_id:
            inquilino = get_object_or_404(Inquilino, id=inquilino_id)

        # 3. Cria a nova casa
        Casa.objects.create(
            numero=numero,
            predio=predio,
            inquilino=inquilino
        )
        messages.success(request, 'Casa adicionada com sucesso!')
        return redirect('ver_casas')

    context = {
        'predios': predios_do_gerente,
        'inquilinos': inquilinos_disponiveis
    }
    return render(request, 'gerente/adicionar_casa.html', context)


@user_passes_test(is_gerente, login_url='login_gerente')
def editar_casa(request, casa_id):
    """
    Permite ao Gerente editar uma casa existente usando formulário HTML puro.
    """
    gerente = request.user.gerente
    casa = get_object_or_404(Casa, id=casa_id, predio__gerente=gerente)
    
    predios_do_gerente = Predio.objects.filter(gerente=gerente)
    inquilinos_disponiveis = Inquilino.objects.all()

    if request.method == 'POST':
        numero = request.POST.get('numero')
        predio_id = request.POST.get('predio')
        inquilino_id = request.POST.get('inquilino')

        if not numero or not predio_id:
            messages.error(request, 'O número da casa e o prédio são obrigatórios.')
            return redirect('editar_casa', casa_id=casa.id)
        
        # 1. Atualiza os dados da casa
        casa.numero = numero
        casa.predio = get_object_or_404(Predio, id=predio_id, gerente=gerente)
        
        if inquilino_id:
            casa.inquilino = get_object_or_404(Inquilino, id=inquilino_id)
        else:
            casa.inquilino = None
            
        casa.save()
        messages.success(request, 'Casa editada com sucesso!')
        return redirect('ver_casas')
        
    context = {
        'casa': casa,
        'predios': predios_do_gerente,
        'inquilinos': inquilinos_disponiveis
    }
    return render(request, 'gerente/editar_casa.html', context)
    

@user_passes_test(is_gerente, login_url='login_gerente')
def excluir_casa(request, casa_id):
    """
    Exclui uma casa do Gerente logado sem uma página de confirmação.
    A exclusão só é processada se a requisição for POST.
    """
    gerente = request.user.gerente
    casa = get_object_or_404(Casa, id=casa_id, predio__gerente=gerente)

    if request.method == 'POST':
        casa.delete()
        messages.success(request, f'Casa {casa.numero} excluída com sucesso!')
    else:
        messages.error(request, 'Método de requisição inválido para exclusão.')
        
    return redirect('ver_casas')


@user_passes_test(is_gerente, login_url='login_gerente')
def ver_inquilinos(request):
    """
    Exibe uma lista de inquilinos associados aos prédios do Gerente logado.
    """
    try:
        gerente = request.user.gerente
        # Filtra os inquilinos que têm uma casa em um prédio do gerente.
        inquilinos = Inquilino.objects.filter(casas_alugadas__predio__gerente=gerente).distinct()
    except Inquilino.DoesNotExist:
        inquilinos = []
    
    context = {
        'inquilinos': inquilinos
    }
    return render(request, 'gerente/ver_inquilinos.html', context)


@user_passes_test(is_gerente, login_url='login_gerente')
def adicionar_inquilino(request):
    """
    Permite ao Gerente adicionar um novo inquilino, com a opção de atribuí-lo a uma casa vaga
    e adicionando o usuário ao grupo 'Inquilino'.
    """
    gerente = request.user.gerente
    casas_vagas = Casa.objects.filter(inquilino__isnull=True, predio__gerente=gerente)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        contacto = request.POST.get('contacto')
        casa_id = request.POST.get('casa_id') # Campo para a casa vaga

        # 1. Validação básica
        if not username or not password or not contacto:
            messages.error(request, 'Nome de utilizador, senha e contacto são obrigatórios.')
            return redirect('adicionar_inquilino')
            
        # 2. Verifica se o username já existe
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Nome de utilizador já existe. Por favor, escolha outro.')
            return redirect('adicionar_inquilino')

        # 3. Cria o novo User e o perfil de Inquilino
        user = User.objects.create_user(username=username, password=password)
        inquilino = Inquilino.objects.create(user=user, contacto=contacto)
        
        # 4. Adiciona o usuário ao grupo 'Inquilino'
        try:
            inquilino_group, created = Group.objects.get_or_create(name='Inquilino')
            user.groups.add(inquilino_group)
        except Exception:
            messages.warning(request, 'O grupo "Inquilino" não foi encontrado. O inquilino foi criado, mas não foi adicionado ao grupo.')
        
        # 5. Atribui o inquilino à casa, se uma foi selecionada
        if casa_id:
            try:
                casa = Casa.objects.get(id=casa_id, inquilino__isnull=True, predio__gerente=gerente)
                casa.inquilino = inquilino
                casa.save()
            except Casa.DoesNotExist:
                messages.warning(request, 'A casa selecionada não está disponível ou não pertence a você. O inquilino foi criado, mas não foi atribuído a uma casa.')
                return redirect('ver_inquilinos')

        messages.success(request, 'Inquilino adicionado com sucesso!')
        return redirect('ver_inquilinos')
        
    context = {
        'casas_vagas': casas_vagas
    }
    return render(request, 'gerente/adicionar_inquilino.html', context)


@user_passes_test(is_gerente, login_url='login_gerente')
def editar_inquilino(request, inquilino_id):
    """
    Permite ao Gerente editar um inquilino existente.
    """
    inquilino_perfil = get_object_or_404(Inquilino, id=inquilino_id, casas_alugadas__predio__gerente=request.user.gerente)
    inquilino_user = inquilino_perfil.user
    
    if request.method == 'POST':
        username = request.POST.get('username')
        contacto = request.POST.get('contacto')
        
        # 1. Validação
        if not username or not contacto:
            messages.error(request, 'Nome de utilizador e contacto são obrigatórios.')
            return redirect('editar_inquilino', inquilino_id=inquilino_id)
            
        # 2. Atualiza o User e Inquilino
        if username != inquilino_user.username and User.objects.filter(username=username).exists():
            messages.error(request, 'Nome de utilizador já existe. Por favor, escolha outro.')
            return redirect('editar_inquilino', inquilino_id=inquilino_id)
        
        inquilino_user.username = username
        inquilino_user.save()
        inquilino_perfil.contacto = contacto
        inquilino_perfil.save()
        
        messages.success(request, 'Inquilino editado com sucesso!')
        return redirect('ver_inquilinos')

    context = {
        'inquilino': inquilino_perfil,
        'user': inquilino_user
    }
    return render(request, 'gerente/editar_inquilino.html', context)


@user_passes_test(is_gerente, login_url='login_gerente')
def excluir_inquilino(request, inquilino_id):
    """
    Exclui um inquilino (e seu usuário associado) sem página de confirmação.
    """
    inquilino_perfil = get_object_or_404(Inquilino, id=inquilino_id, casas_alugadas__predio__gerente=request.user.gerente)

    if request.method == 'POST':
        try:
            # A exclusão do User fará o Inquilino ser excluído em cascata.
            inquilino_perfil.user.delete()
            messages.success(request, f'Inquilino {inquilino_perfil.user.username} excluído com sucesso!')
        except Exception:
            messages.error(request, 'Erro ao deletar o inquilino.')
    else:
        messages.error(request, 'Método de requisição inválido para exclusão.')
        
    return redirect('ver_inquilinos')


@user_passes_test(is_gerente, login_url='login_gerente')
def ver_manutencoes(request):
    gerente = request.user.gerente
    
    # Busca todas as manutenções relacionadas a um prédio do gerente,
    # tanto as específicas (com casa) quanto as gerais (com prédio)
    manutencoes = Manutencao.objects.filter(
        Q(casa__predio__gerente=gerente) | Q(predio__gerente=gerente)
    ).order_by('-data_solicitacao')
    
    context = {
        'manutencoes': manutencoes
    }
    return render(request, 'gerente/ver_manutencoes.html', context)

@user_passes_test(is_gerente, login_url='login_gerente')
def atualizar_estado_manutencao(request, manutencao_id):
    """
    Permite ao Gerente atualizar o estado de uma solicitação de manutenção.
    """
    manutencao = get_object_or_404(Manutencao, id=manutencao_id, casa__predio__gerente=request.user.gerente)
    
    if request.method == 'POST':
        novo_estado = request.POST.get('estado')
        if novo_estado and novo_estado in [choice[0] for choice in Manutencao.ESTADO_CHOICES]:
            manutencao.estado = novo_estado
            manutencao.save()
            messages.success(request, f'Estado da manutenção "{manutencao.descricao[:20]}..." atualizado para "{manutencao.get_estado_display()}".')
        else:
            messages.error(request, 'Estado inválido selecionado.')
    
    return redirect('ver_manutencoes')

@user_passes_test(is_gerente, login_url='login_gerente')
def adicionar_manutencao(request):
    """
    Permite ao gerente adicionar uma nova solicitação de manutenção.
    """
    gerente = request.user.gerente
    predios = Predio.objects.filter(gerente=gerente)
    casas = Casa.objects.filter(predio__gerente=gerente)
    tipo_choices = Manutencao.TIPO_CHOICES
    
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        descricao = request.POST.get('descricao')
        casa_id = request.POST.get('casa')
        predio_id = request.POST.get('predio')
        
        casa_obj = None
        predio_obj = None
        try:
            if tipo != 'geral' and casa_id:
                casa_obj = get_object_or_404(Casa, id=casa_id)
            elif tipo == 'geral' and predio_id:
                predio_obj = get_object_or_404(Predio, id=predio_id)
            else:
                messages.error(request, 'Não foi possível encontrar um local válido para esta solicitação.')
                return redirect('adicionar_manutencao')

            Manutencao.objects.create(
                tipo=tipo,
                descricao=descricao,
                casa=casa_obj,
                predio=predio_obj,
                solicitado_por_gerente=gerente,
                estado='pendente'
            )
            messages.success(request, 'Solicitação de manutenção adicionada com sucesso!')
            
            return redirect('ver_manutencoes')

        except Exception as e:
            messages.error(request, f'Erro ao adicionar a manutenção: {e}')
            
    context = {
        'predios': predios,
        'casas': casas,
        'tipo_choices': tipo_choices,
    }
    return render(request, 'gerente/adicionar_manutencao.html', context)

# Adicione esta nova função de exclusão
@user_passes_test(is_gerente, login_url='login_gerente')
def excluir_manutencao(request, manutencao_id):
    if request.method == 'POST':
        manutencao = get_object_or_404(Manutencao, pk=manutencao_id)
        
        # Verifique se o gerente tem permissão para excluir esta manutenção
        try:
            # Caso 1: Manutenção de uma casa de um prédio do gerente
            if manutencao.casa and manutencao.casa.predio.gerente == request.user.gerente:
                manutencao.delete()
                messages.success(request, 'Manutenção excluída com sucesso!')
            # Caso 2: Manutenção geral solicitada pelo próprio gerente
            elif not manutencao.casa and manutencao.solicitado_por_gerente == request.user.gerente:
                manutencao.delete()
                messages.success(request, 'Manutenção geral excluída com sucesso!')
            else:
                messages.error(request, 'Você não tem permissão para excluir esta manutenção.')

        except Exception as e:
            messages.error(request, f'Erro ao excluir a manutenção: {e}')
            
    return redirect('ver_manutencoes')