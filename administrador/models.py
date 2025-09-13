from django.db import models
from django.contrib.auth.models import User, Group

class Gerente(models.Model):
    """
    Modelo de perfil para um Gerente.
    Extende o User do Django.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contacto = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Predio(models.Model):
    """
    Modelo para representar um Prédio, gerido por um Gerente.
    """
    nome = models.CharField(max_length=100)
    localizacao = models.CharField(max_length=255)
    gerente = models.ForeignKey(Gerente, on_delete=models.PROTECT, related_name='predios')

    def __str__(self):
        return f'{self.nome} ({self.localizacao})'