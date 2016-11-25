from django.db import models

class AFIP_Datos_Autenticacion(models.Model):
    sign = models.TextField()
    token = models.TextField()
    expiration = models.DateTimeField()
    produccion = models.BooleanField()
