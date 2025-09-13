from django.db import models
from administrador.models import Predio, Gerente
from django.contrib.auth.models import User, Group

class Inquilino(models.Model):
    """
    Modelo de perfil para um Inquilino.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contacto = models.CharField(max_length=15, unique=True)
    
    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Casa(models.Model):
    # ... (código do modelo Casa, sem alterações)
    numero = models.CharField(max_length=10)
    predio = models.ForeignKey(Predio, on_delete=models.CASCADE, related_name='casas')
    inquilino = models.ForeignKey(
        Inquilino,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='casas_alugadas'
    )

    @property
    def gerente(self):
        return self.predio.gerente

    def __str__(self):
        return f'Casa {self.numero} ({self.predio.nome})'


class Manutencao(models.Model):
    # ... (código do modelo Manutencao, sem alterações)
    TIPO_CHOICES = [
        ('eletrico', 'Elétrico'),
        ('hidraulico', 'Hidráulico'),
        ('estrutural', 'Estrutural'),
        ('geral', 'Geral'),
    ]

    ESTADO_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_progresso', 'Em Progresso'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descricao = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendente')
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    casa = models.ForeignKey('Casa', on_delete=models.CASCADE, related_name='manutencoes', null=True, blank=True)
    predio = models.ForeignKey(Predio, on_delete=models.CASCADE, related_name='manutencoes_gerais', null=True, blank=True)
    solicitado_por_inquilino = models.ForeignKey(Inquilino, on_delete=models.SET_NULL, null=True, blank=True, related_name='manutencoes_solicitadas_inquilino')
    solicitado_por_gerente = models.ForeignKey(Gerente, on_delete=models.SET_NULL, null=True, blank=True, related_name='manutencoes_solicitadas_gerente')

    def __str__(self):
        if self.casa:
            return f'Manutenção em {self.casa.predio.nome} - Casa {self.casa.numero} - Tipo: {self.get_tipo_display()}'
        elif self.predio:
            return f'Manutenção Geral em {self.predio.nome} - Tipo: {self.get_tipo_display()}'
        else:
            return f'Manutenção sem local definido'

class Contratos(models.Model):
    # ... (código do modelo Contratos, sem alterações)
    data_inicio = models.DateField()
    valor_renda = models.DecimalField(max_digits=10, decimal_places=2)
    duracao_meses = models.IntegerField(verbose_name='Duração (meses)')
    inquilino = models.ForeignKey(Inquilino, on_delete=models.CASCADE, related_name='contratos')

    def __str__(self):
        return f'Contrato para {self.inquilino.nome} - Início: {self.data_inicio}'