# -*- coding: utf-8 -*-
from django.contrib.auth.models import User

from django.db import models
from voolean.settings import CUIT


# Create your models here.

class FunctionHit(models.Model):
    FUNCION_CHOICES = (('BANCO', 'BANCOS'),
                       ('TRANS', 'TRANSPORTE'),
                       ('PERIO', 'PERIODO'))

    usuario = models.ForeignKey(User)
    funcion = models.CharField(max_length=5, choices=FUNCION_CHOICES)
    name = models.CharField(max_length=100, default="")
    hit = models.IntegerField(default=1)


class BaseModel(models.Model):
    suspendido = models.BooleanField(default=False)

    class Meta:
        abstract = True


class Periodo(models.Model):
    mes = models.IntegerField(help_text="Mes del Período, dos dígitos. Ej: 09")
    ano = models.IntegerField(help_text="Año del Período, cuatro dígitos. Ej: 2013")

    class Meta:
        unique_together = ('mes', 'ano')

    def __unicode__(self):
        return "%s/%s" % (self.mes, self.ano)

    @property
    def periodo_full(self):
        mes = str(self.mes)
        if 0 < len(mes) < 3:
            restante = 2 - len(mes)
            if restante != 0:
                for i in range(restante):
                    mes = '0' + mes
        return "%s/%s" % (mes, self.ano)

    @property
    def mes_display(self):
        return str(self.mes).rjust(2, '0')


class Bancos(BaseModel):
    nombre = models.CharField(max_length=80, help_text="Nombre del banco", verbose_name="Nombre")

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.title()
        super(Bancos, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.nombre


class CuentasBanco(BaseModel):
    cbu = models.CharField(max_length=22)
    banco = models.ForeignKey(Bancos)

    def __unicode__(self):
        return "CBU %s (%s)" % (self.cbu, self.banco.nombre)


class Transporte(BaseModel):
    PROVINCIA_CHOICES = (
        ("BA", "Buenos Aires"),
        ("CT", "Corrientes"),
        ("CC", "Chaco"),
        ("CH", "Chubut"),
        ("CD", "Córdoba"),
        ("CR", "Corrientes"),
        ("ER", "Entre Ríos"),
        ("FO", "Formosa"),
        ("JY", "Jujuy"),
        ("LP", "La Pampa"),
        ("LR", "La Rioja"),
        ("MZ", "Mendoza"),
        ("MN", "Misiones"),
        ("NQ", "Neuquén"),
        ("RN", "Río Negro"),
        ("SA", "Salta"),
        ("SJ", "San Juan"),
        ("SL", "San Luis"),
        ("SC", "Santa Cruz"),
        ("SF", "Santa Fe"),
        ("SE", "Santiago del Estero"),
        ("TF", "Tierra del Fuego, Antártida e Islas del Atlántico Sur"),
        ("TM", "Tucumán")
    )

    nombre = models.CharField(max_length=50, help_text="Nombre del transporte.", verbose_name="Nombre")
    direccion = models.CharField(max_length=50, blank=True,
                                 help_text="Dirección del transporte. <strong>Opcional.</strong>",
                                 verbose_name="Dirección")
    localidad = models.CharField(max_length=40, blank=True,
                                 help_text="Localidad de residencia del transporte. <strong>Opcional.</strong>",
                                 verbose_name="Ciudad")
    codigo_postal = models.CharField(max_length=40, blank=True, help_text="Codigo postal. <strong>Opcional.</strong>",
                                     verbose_name="Código Postal")
    provincia = models.CharField(max_length=2, blank=True, choices=PROVINCIA_CHOICES,
                                 help_text="Provincia de residencia. <strong>Opcional.</strong>",
                                 verbose_name="Provincia")
    pais = models.CharField(max_length=20, blank=True, help_text="País de residencia. <strong>Opcional.</strong>",
                            verbose_name="País")
    telefono = models.CharField(max_length=30, blank=True, help_text="Teléfono de contacto. <strong>Opcional.</strong>",
                                verbose_name="Teléfono")
    fax = models.CharField(max_length=30, blank=True, help_text="Fax del transporte. <strong>Opcional.</strong>",
                           verbose_name="FAX")
    email = models.EmailField(max_length=254, blank=True, help_text="E-mail del transporte. <strong>Opcional.</strong>",
                              verbose_name="E-mail")
    cuit = models.CharField(max_length=13, blank=True, help_text="CUIT del transporte. <strong>Opcional.</strong>",
                            verbose_name="CUIT")
    # saldo_transporte = models.DecimalField(max_digits=13, decimal_places=3)
    notas = models.CharField(max_length=400, blank=True, help_text="Observaciones. <strong>Opcional.</strong>",
                             verbose_name="Notas")

    # modificado_por = models.ForeignKey(User)

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.title()
        self.direccion = self.direccion.title()
        self.localidad = self.localidad.title()
        self.pais = self.pais.title()
        super(Transporte, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.nombre


class Dinero(models.Model):
    monto = models.DecimalField(max_digits=13, decimal_places=3)
    recibo = models.ForeignKey('ventas.Recibo', blank=True, null=True)
    orden_pago = models.ForeignKey('compras.OrdenPago', blank=True, null=True)
    pendiente_para_recibo = models.DecimalField(max_digits=13, decimal_places=3, default=0)
    pendiente_para_orden_pago = models.DecimalField(max_digits=13, decimal_places=3, default=0)

    def __unicode__(self):
        try:
            return "Cheque tercero N %s" % self.chequetercero.numero
        except self.DoesNotExist:
            try:
                return "Cheque propio N %s" % self.chequepropio.numero
            except self.DoesNotExist:
                return "EFECTIVO por %s" % self.monto

    @property
    def tipo_valor(self):
        try:
            if self.chequetercero:
                return "Ch. Tercero"
        except self.DoesNotExist:
            try:
                if self.chequepropio:
                    return "Ch. Propio"
            except self.DoesNotExist:
                try:
                    if self.transferenciabancariasaliente:
                        return "Transferencia"
                except self.DoesNotExist:
                    return "Efectivo"

    @property
    def entidad(self):
        try:
            if self.chequetercero:
                return self.chequetercero.banco
        except self.DoesNotExist:
            try:
                if self.chequepropio or self.transferenciabancariasaliente:
                    return "BANCO LOCAL"
            except self.DoesNotExist:
                return ""

    @property
    def num_comprobante(self):
        try:
            if self.chequetercero:
                return self.chequetercero.numero
        except self.DoesNotExist:
            try:
                if self.chequepropio:
                    return self.chequepropio.numero
            except self.DoesNotExist:
                try:
                    if self.transferenciabancariasaliente:
                        return self.transferenciabancariasaliente.numero_operacion
                except self.DoesNotExist:
                    return ""

    @property
    def CUIT(self):
        try:
            if self.chequetercero:
                return self.chequetercero.cuit_titular
        except self.DoesNotExist:
            try:
                if self.chequepropio:
                    return CUIT
            except self.DoesNotExist:
                try:
                    if self.transferenciabancariasaliente:
                        return ""
                except self.DoesNotExist:
                    return ""

    @property
    def FECHA(self):
        try:
            if self.chequetercero:
                return self.chequetercero.cobro.strftime('%d/%m/%Y')
        except self.DoesNotExist:
            try:
                if self.chequepropio:
                    return self.chequepropio.cobro.strftime('%d/%m/%Y')
            except self.DoesNotExist:
                try:
                    if self.transferenciabancariasaliente:
                        return ""
                except self.DoesNotExist:
                    return ""


class ChequeTercero(Dinero):
    numero = models.CharField(max_length=12, blank=True, null=True)
    fecha = models.DateField(blank=True, null=True)
    cobro = models.DateField(blank=True, null=True)
    paguese_a = models.CharField(max_length=80, blank=True, null=True)
    # pendiente_para_recibo=models.DecimalField(max_digits=13, decimal_places=3)
    # pendiente_para_orden_pago=models.DecimalField(max_digits=13, decimal_places=3)
    titular = models.CharField(max_length=80, blank=True, null=True)
    cuit_titular = models.CharField(max_length=13, blank=True, null=True)
    banco = models.ForeignKey(Bancos, blank=True, null=True, related_name='cheques1')
    en_cartera = models.BooleanField(default=True)
    domicilio_de_pago = models.CharField(max_length=200, blank=True, null=True)
    observaciones = models.CharField(max_length=200, blank=True, null=True)

    def __unicode__(self):
        return "Cheque de terceros N %s" % self.numero

    def fecha_dd_mm_aaaa(self):
        return self.fecha.strftime('%d/%m/%Y')


class ChequePropio(Dinero):
    numero = models.CharField(max_length=12)
    fecha = models.DateField()
    cobro = models.DateField()
    paguese_a = models.CharField(max_length=60)

    # banco = models.ForeignKey(Bancos, blank=True, null=True, related_name = 'cheques1')
    # cheque_domicilio_de_pago = models.CharField(max_length=200, blank=True, null=True)
    # pendiente_para_orden_pago=models.DecimalField(max_digits=13, decimal_places=3)

    def __unicode__(self):
        return "Cheque propio N° %s" % self.numero

    def fecha_dd_mm_aaaa(self):
        return self.fecha.strftime('%d/%m/%Y')


class TransferenciaBancariaEntrante(Dinero):
    banco_origen = models.ForeignKey(Bancos, blank=True, null=True)
    cuenta_origen = models.CharField(max_length=22, blank=True, null=True)
    numero_operacion = models.CharField(max_length=22)
    cuenta_destino = models.ForeignKey(CuentasBanco)


class TransferenciaBancariaSaliente(Dinero):
    banco_origen = models.ForeignKey(Bancos, blank=True, null=True)
    cuenta_origen = models.ForeignKey(CuentasBanco)
    numero_operacion = models.CharField(max_length=22)
    cuenta_destino = models.CharField(max_length=22, blank=True, null=True)
