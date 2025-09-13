from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.db.models import ProtectedError
from django.contrib import messages
from django.shortcuts import get_object_or_404
from .models import Gerente, Predio
from django.contrib.auth.decorators import user_passes_test

# --- Funções auxiliares para verificação de permissões ---
def is_admin(user):
    """
    Verifica se o utilizador está autenticado e pertence ao grupo 'Administrador'.
    """
    return user.is_authenticated and user.groups.filter(name='Administrador').exists()

def login_admin(request):
    """
    View para o administrador fazer login.
    Esta view não pode ser protegida, pois é a porta de entrada.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # 1. Autenticar o utilizador com as credenciais fornecidas
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # 2. Verificar se o utilizador pertence ao grupo 'Administrador'
            try:
                if user.groups.filter(name='Administrador').exists():
                    login(request, user)
                    messages.success(request, 'Login de administrador realizado com sucesso!')
                    return redirect('dashboard_admin') # Redirecionar para a página desejada
                else:
                    messages.error(request, 'Credenciais inválidas ou não pertence ao grupo Administrador.')
            except Group.DoesNotExist:
                messages.error(request, 'Grupo "Administrador" não encontrado. Verifique se o grupo foi criado.')
        else:
            messages.error(request, 'Nome de utilizador ou senha inválidos.')
            
    return render(request, 'administrador/login_admin.html')

def logout_admin(request):
    """
    View para o administrador fazer logout.
    """
    logout(request)
    messages.success(request, 'Logout realizado com sucesso.')
    return redirect('login_admin')

# --- Views protegidas por login e permissão ---

@user_passes_test(is_admin, login_url='login_admin')
def dashboard_admin(request):
    """
    Renderiza o dashboard principal com a tabela de prédios.
    """
    predios = Predio.objects.all()
    context = {'predios': predios}
    return render(request, 'administrador/dashboard_admin.html', context)

@user_passes_test(is_admin, login_url='login_admin')
def ver_gerentes(request):
    """
    Renderiza a página para gerenciar gerentes.
    Exibe a lista de gerentes e botões de ação.
    """
    gerentes = Gerente.objects.all()
    context = {'gerentes': gerentes}
    return render(request, 'administrador/ver_gerentes.html', context)

@user_passes_test(is_admin, login_url='login_admin')
def ver_predios(request):
    """
    Renderiza a página para gerenciar prédios.
    Exibe a lista de prédios e botões de ação.
    """
    predios = Predio.objects.all()
    context = {'predios': predios}
    return render(request, 'administrador/ver_predios.html', context)

# Views de Adição
@user_passes_test(is_admin, login_url='login_admin')
def adicionar_gerente(request):
    """
    View para o administrador adicionar um novo gerente e seu perfil.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        contacto = request.POST.get('contacto')
        try:
            gerente = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            grupo_gerente, created = Group.objects.get_or_create(name='Gerente')
            gerente.groups.add(grupo_gerente)
            Gerente.objects.create(
                user=gerente,
                contacto=contacto
            )
            messages.success(request, 'Gerente criado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao criar o gerente: {e}')
        return redirect('adicionar_gerente')
    
    return render(request, 'administrador/adicionar_gerente.html')

@user_passes_test(is_admin, login_url='login_admin')
def adicionar_predio(request):
    """
    View para o administrador adicionar um novo prédio e associá-lo a um gerente.
    """
    gerentes = Gerente.objects.all()
    if request.method == 'POST':
        nome = request.POST.get('nome')
        localizacao = request.POST.get('localizacao')
        gerente_id = request.POST.get('gerente')
        gerente = get_object_or_404(Gerente, pk=gerente_id)
        try:
            Predio.objects.create(
                nome=nome,
                localizacao=localizacao,
                gerente=gerente
            )
            messages.success(request, 'Prédio criado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao criar o prédio: {e}')
        return redirect('adicionar_predio')
    
    context = {'gerentes': gerentes}
    return render(request, 'administrador/adicionar_predio.html', context)

# Views de Edição
@user_passes_test(is_admin, login_url='login_admin')
def editar_gerente(request, gerente_id):
    """
    View para o administrador editar um gerente e seu perfil.
    """
    gerente_perfil = get_object_or_404(Gerente, pk=gerente_id)
    gerente_user = gerente_perfil.user
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        contacto = request.POST.get('contacto')
        try:
            gerente_user.username = username
            gerente_user.email = email
            new_password = request.POST.get('password')
            if new_password:
                gerente_user.set_password(new_password)
            gerente_user.save()
            gerente_perfil.contacto = contacto
            gerente_perfil.save()
            messages.success(request, 'Gerente atualizado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar o gerente: {e}')
        return redirect('editar_gerente', gerente_id=gerente_id)
    context = {'gerente': gerente_perfil, 'user': gerente_user}
    return render(request, 'administrador/editar_gerente.html', context)

@user_passes_test(is_admin, login_url='login_admin')
def editar_predio(request, predio_id):
    """
    View para o administrador editar um prédio.
    """
    predio = get_object_or_404(Predio, pk=predio_id)
    gerentes = Gerente.objects.all()
    if request.method == 'POST':
        nome = request.POST.get('nome')
        localizacao = request.POST.get('localizacao')
        gerente_id = request.POST.get('gerente')
        gerente = get_object_or_404(Gerente, pk=gerente_id)
        try:
            predio.nome = nome
            predio.localizacao = localizacao
            predio.gerente = gerente
            predio.save()
            messages.success(request, 'Prédio atualizado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar o prédio: {e}')
        return redirect('editar_predio', predio_id=predio_id)
    context = {'predio': predio, 'gerentes': gerentes}
    return render(request, 'administrador/editar_predio.html', context)

# Views de Deleção
@user_passes_test(is_admin, login_url='login_admin')
def deletar_gerente(request, gerente_id):
    """
    Deleta um gerente via requisição POST.
    """
    if request.method == 'POST':
        gerente_perfil = get_object_or_404(Gerente, pk=gerente_id)
        try:
            gerente_perfil.user.delete()
            messages.success(request, 'Gerente deletado com sucesso!')
        except ProtectedError:
            messages.error(request, 'Este gerente não pode ser deletado porque está associado a um ou mais prédios.')
        except Exception as e:
            messages.error(request, f'Erro ao deletar o gerente: {e}')
    return redirect('ver_gerentes')

@user_passes_test(is_admin, login_url='login_admin')
def deletar_predio(request, predio_id):
    """
    Deleta um prédio via requisição POST.
    """
    if request.method == 'POST':
        predio = get_object_or_404(Predio, pk=predio_id)
        try:
            predio.delete()
            messages.success(request, 'Prédio deletado com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao deletar o prédio: {e}')
    return redirect('ver_predios')