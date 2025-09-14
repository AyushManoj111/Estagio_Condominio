from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from .models import Casa, Gerente, Predio, Inquilino, Manutencao, Contratos
from django.db.models import Q
from datetime import date
from dateutil.relativedelta import relativedelta
from django.db import transaction

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
    Permite ao Gerente adicionar uma nova casa usando formulário HTML puro,
    sem a opção de atribuir um inquilino.
    """
    gerente = request.user.gerente
    predios_do_gerente = Predio.objects.filter(gerente=gerente)

    if request.method == 'POST':
        numero = request.POST.get('numero')
        predio_id = request.POST.get('predio')

        # 1. Validação básica
        if not numero or not predio_id:
            messages.error(request, 'O número da casa e o prédio são obrigatórios.')
            return redirect('adicionar_casa')

        # 2. Verifica se o prédio pertence ao gerente
        predio = get_object_or_404(Predio, id=predio_id, gerente=gerente)
        
        # 3. Cria a nova casa sem um inquilino
        Casa.objects.create(
            numero=numero,
            predio=predio,
            inquilino=None
        )
        messages.success(request, 'Casa adicionada com sucesso!')
        return redirect('ver_casas')

    context = {
        'predios': predios_do_gerente,
    }
    return render(request, 'gerente/adicionar_casa.html', context)

@user_passes_test(is_gerente, login_url='login_gerente')
def editar_casa(request, casa_id):
    """
    Permite ao Gerente editar uma casa existente, sem a opção de alterar o inquilino.
    """
    gerente = request.user.gerente
    casa = get_object_or_404(Casa, id=casa_id, predio__gerente=gerente)
    
    predios_do_gerente = Predio.objects.filter(gerente=gerente)

    if request.method == 'POST':
        numero = request.POST.get('numero')
        predio_id = request.POST.get('predio')

        if not numero or not predio_id:
            messages.error(request, 'O número da casa e o prédio são obrigatórios.')
            return redirect('editar_casa', casa_id=casa.id)
        
        # 1. Atualiza os dados da casa
        casa.numero = numero
        casa.predio = get_object_or_404(Predio, id=predio_id, gerente=gerente)
        
        # A atribuição de inquilino agora é feita apenas pela gestão de contratos.
        # Nenhuma mudança é feita no campo `inquilino` aqui.
            
        casa.save()
        messages.success(request, 'Casa editada com sucesso!')
        return redirect('ver_casas')
        
    context = {
        'casa': casa,
        'predios': predios_do_gerente,
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
    try:
        gerente = request.user.gerente
        
        # Agora o filtro é direto: mostre apenas os inquilinos registrados por este gerente.
        inquilinos = Inquilino.objects.filter(gerente=gerente)
    except Gerente.DoesNotExist:
        inquilinos = []
    
    context = {
        'inquilinos': inquilinos
    }
    return render(request, 'gerente/ver_inquilinos.html', context)


@user_passes_test(is_gerente, login_url='login_gerente')
def adicionar_inquilino(request):
    """
    Permite ao Gerente adicionar um novo inquilino e adicioná-lo ao grupo 'Inquilino'.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        contacto = request.POST.get('contacto')

        # 1. Validação básica
        if not username or not password or not contacto:
            messages.error(request, 'Nome de utilizador, senha e contacto são obrigatórios.')
            return redirect('adicionar_inquilino')
            
        # 2. Verifica se o username já existe
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Nome de utilizador já existe. Por favor, escolha outro.')
            return redirect('adicionar_inquilino')

        try:
            # 3. Cria o novo User e o perfil de Inquilino
            user = User.objects.create_user(username=username, password=password)
            
            # Pega o gerente logado
            gerente = request.user.gerente
            
            # Cria o perfil do inquilino e atribui o gerente
            inquilino = Inquilino.objects.create(user=user, contacto=contacto, gerente=gerente)
            
            # 4. Adiciona o usuário ao grupo 'Inquilino'
            inquilino_group, created = Group.objects.get_or_create(name='Inquilino')
            user.groups.add(inquilino_group)
            
            messages.success(request, 'Inquilino adicionado com sucesso!')
            return redirect('ver_inquilinos')

        except Exception as e:
            messages.error(request, f'Ocorreu um erro ao adicionar o inquilino: {e}')
            return redirect('adicionar_inquilino')
            
    # Para requisições GET, apenas renderiza o formulário
    return render(request, 'gerente/adicionar_inquilino.html')

@user_passes_test(is_gerente, login_url='login_gerente')
def editar_inquilino(request, inquilino_id):
    """
    Permite ao Gerente editar um inquilino existente.
    """
    # Filtra o inquilino pelo ID e pelo gerente logado
    inquilino_perfil = get_object_or_404(Inquilino, id=inquilino_id, gerente=request.user.gerente)
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
    # Filtra o inquilino pelo ID e pelo gerente logado
    inquilino_perfil = get_object_or_404(Inquilino, id=inquilino_id, gerente=request.user.gerente)

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

@user_passes_test(is_gerente, login_url='login_gerente')
def ver_contratos(request):
    """
    Exibe uma lista de contratos associados aos prédios do Gerente logado.
    """
    try:
        gerente = request.user.gerente
        # Filtra os contratos cujos inquilinos têm uma casa num prédio do gerente.
        contratos = Contratos.objects.filter(
            inquilino__casas_alugadas__predio__gerente=gerente
        ).distinct().select_related('inquilino__user').prefetch_related('inquilino__casas_alugadas__predio')

        hoje = date.today()
        for contrato in contratos:
            # Duração total em meses
            contrato.duracao_total = f'{contrato.duracao_meses} meses'
            
            # Data de término do contrato
            data_termino = contrato.data_inicio + relativedelta(months=+contrato.duracao_meses)
            
            # Cálculo da duração restante
            delta = relativedelta(data_termino, hoje)
            
            if delta.years > 0:
                contrato.duracao_restante = f'{delta.years} anos e {delta.months} meses'
            elif delta.months > 0:
                contrato.duracao_restante = f'{delta.months} meses'
            elif delta.days > 0:
                contrato.duracao_restante = f'{delta.days} dias'
            else:
                contrato.duracao_restante = 'Expirado'

    except Exception as e:
        # Lida com erros de forma graciosa
        contratos = []
        # Opcionalmente, pode adicionar uma mensagem de erro:
        # from django.contrib import messages
        # messages.error(request, f'Ocorreu um erro ao carregar os contratos: {e}')

    context = {
        'contratos': contratos
    }
    return render(request, 'gerente/ver_contratos.html', context)

@user_passes_test(is_gerente, login_url='login_gerente')
def adicionar_contrato(request):
    gerente = request.user.gerente
    
    # 1. Obtenha os inquilinos que pertencem a este gerente e que não têm um contrato ativo.
    inquilinos_disponiveis = Inquilino.objects.filter(gerente=gerente).exclude(
        contratos__isnull=False
    ).distinct()

    # 2. Obtenha as casas vagas que pertencem a este gerente.
    casas_vagas = Casa.objects.filter(
        predio__gerente=gerente, 
        inquilino__isnull=True
    ).distinct()
    
    anos_de_contrato = [(i, f"{i} ano{'s' if i > 1 else ''}") for i in range(1, 6)]

    if request.method == 'POST':
        inquilino_id = request.POST.get('inquilino')
        casa_id = request.POST.get('casa_vaga')
        duracao_anos = request.POST.get('duracao_anos')
        valor_renda = request.POST.get('valor_aluguel')

        if not all([inquilino_id, casa_id, duracao_anos, valor_renda]):
            messages.error(request, 'Por favor, preencha todos os campos.')
            return redirect('adicionar_contrato')

        try:
            # 3. Validação de acesso: Garante que o inquilino e a casa pertencem ao gerente.
            inquilino = get_object_or_404(Inquilino, id=inquilino_id, gerente=gerente)
            casa = get_object_or_404(Casa, id=casa_id, predio__gerente=gerente)
            
            duracao_meses = int(duracao_anos) * 12
            valor_renda = float(valor_renda.replace(',', '.'))

            with transaction.atomic():
                contrato = Contratos.objects.create(
                    inquilino=inquilino,
                    casa=casa, 
                    data_inicio=date.today(),
                    valor_renda=valor_renda,
                    duracao_meses=duracao_meses
                )
                
                casa.inquilino = inquilino
                casa.save()

            messages.success(request, f'Contrato para {inquilino.user.username} criado com sucesso e casa atribuída.')
            return redirect('ver_contratos')
            
        except (ValueError, TypeError):
            messages.error(request, 'O valor da renda é inválido.')
            return redirect('adicionar_contrato')
        except Exception as e:
            messages.error(request, f'Ocorreu um erro: {e}')
            return redirect('adicionar_contrato')

    context = {
        'inquilinos_disponiveis': inquilinos_disponiveis,
        'casas_vagas': casas_vagas,
        'anos_de_contrato': anos_de_contrato,
    }
    return render(request, 'gerente/adicionar_contrato.html', context)


@user_passes_test(is_gerente, login_url='login_gerente')
def editar_contrato(request, pk):
    # Garante que o contrato a ser editado pertence ao gerente logado.
    contrato = get_object_or_404(Contratos, pk=pk, inquilino__gerente=request.user.gerente)
    gerente = request.user.gerente
    
    casa_atual = contrato.casa

    # 1. Filtra as casas vagas para o gerente logado, e inclui a casa atual do contrato.
    casas_vagas_qs = Casa.objects.filter(
        Q(predio__gerente=gerente, inquilino__isnull=True) | Q(id=casa_atual.id)
    ).distinct()
    
    # 2. Filtra os inquilinos que pertencem a este gerente.
    # Exclui inquilinos que já têm um contrato ativo, mas inclui o inquilino atual do contrato.
    inquilinos_disponiveis = Inquilino.objects.filter(gerente=gerente).exclude(
        contratos__isnull=False
    ).distinct()

    # Adiciona o inquilino atual do contrato à lista de disponíveis.
    inquilinos_disponiveis = list(inquilinos_disponiveis) + [contrato.inquilino]

    anos_de_contrato = [(i, f"{i} ano{'s' if i > 1 else ''}") for i in range(1, 6)]
    
    # Prepara o valor da duração em anos para o template
    contrato_duracao_anos = int(contrato.duracao_meses / 12)

    if request.method == 'POST':
        novo_inquilino_id = request.POST.get('inquilino')
        nova_casa_id = request.POST.get('casa_vaga')
        nova_duracao_anos = request.POST.get('duracao_anos')
        novo_valor_renda = request.POST.get('valor_aluguel')

        if not all([novo_inquilino_id, nova_casa_id, nova_duracao_anos, novo_valor_renda]):
            messages.error(request, 'Por favor, preencha todos os campos.')
            return redirect('editar_contrato', pk=pk)

        try:
            # 3. Validação de segurança: Garante que o novo inquilino e a nova casa pertencem ao gerente.
            novo_inquilino = get_object_or_404(Inquilino, id=novo_inquilino_id, gerente=gerente)
            nova_casa = get_object_or_404(Casa, id=nova_casa_id, predio__gerente=gerente)
            
            nova_duracao_meses = int(nova_duracao_anos) * 12
            novo_valor_renda = float(novo_valor_renda.replace(',', '.'))

            with transaction.atomic():
                # Liberta a casa anterior se ela for diferente da nova
                if casa_atual and casa_atual.id != nova_casa.id:
                    casa_atual.inquilino = None
                    casa_atual.save()

                # Atribui a nova casa ao novo inquilino
                nova_casa.inquilino = novo_inquilino
                nova_casa.save()

                # Atualiza os dados do contrato
                contrato.inquilino = novo_inquilino
                contrato.casa = nova_casa
                contrato.duracao_meses = nova_duracao_meses
                contrato.valor_renda = novo_valor_renda
                contrato.save()

            messages.success(request, 'Contrato atualizado com sucesso.')
            return redirect('ver_contratos')
        
        except (ValueError, TypeError):
            messages.error(request, 'O valor da renda é inválido.')
            return redirect('editar_contrato', pk=pk)
        except Exception as e:
            messages.error(request, f'Ocorreu um erro: {e}')
            return redirect('editar_contrato', pk=pk)

    context = {
        'contrato': contrato,
        'inquilinos_disponiveis': inquilinos_disponiveis,
        'casas_vagas': casas_vagas_qs,
        'anos_de_contrato': anos_de_contrato,
        'contrato_duracao_anos': contrato_duracao_anos,
        'casa_atual': casa_atual
    }
    return render(request, 'gerente/editar_contrato.html', context)

@user_passes_test(is_gerente, login_url='login_gerente')
def excluir_contrato(request, pk):
    contrato = get_object_or_404(Contratos, pk=pk)
    
    # A exclusão deve ser feita apenas através de um POST,
    # para evitar exclusões acidentais.
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Encontra a casa associada ao inquilino do contrato
                casa_associada = contrato.inquilino.casas_alugadas.first()
                
                # Se houver uma casa, a libera
                if casa_associada:
                    casa_associada.inquilino = None
                    casa_associada.save()

                # Exclui o contrato
                contrato.delete()

            messages.success(request, 'Contrato excluído com sucesso e casa liberada.')
            return redirect('ver_contratos')
        
        except Exception as e:
            messages.error(request, f'Ocorreu um erro ao excluir o contrato: {e}')
            return redirect('ver_contratos')

    # Se a requisição não for POST, redireciona de volta
    return redirect('ver_contratos')