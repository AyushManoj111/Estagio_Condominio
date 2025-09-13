from django.db import models
from django.contrib.auth.models import User, Group
from datetime import date
from gerente.models import Contratos

class PagamentoRenda(models.Model):
    ESTADO_CHOICES = [
        ('pago', 'Pago'),
        ('nao_pago', 'Não Pago'),
    ]

    contrato = models.ForeignKey(Contratos, on_delete=models.CASCADE, related_name='pagamentos')
    mes_referencia = models.DateField(verbose_name='Mês de Referência')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    entidade = models.CharField(max_length=4, default='9501')
    referencia = models.CharField(max_length=20, unique=True, verbose_name='Referência')
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='nao_pago')

    def __str__(self):
        return f'Pagamento de {self.mes_referencia.strftime("%B/%Y")} para {self.contrato.inquilino.user.username}'
    
    class Meta:
        # Garante que não haja duplicatas para um mesmo contrato e mês de referência
        unique_together = ('contrato', 'mes_referencia',)