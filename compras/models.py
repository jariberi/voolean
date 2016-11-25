# -*- coding: utf-8 -*-
import django
from decimal import Decimal
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.db.models.aggregates import Sum
from django.utils.timezone import now
from datetime import datetime
from core.models import Periodo, BaseModel


# Create your models here.
class Condicion_compra(models.Model):
    descripcion = models.CharField(max_length=50, help_text="Descripcion")
    usa_cuenta_corriente = models.BooleanField(default=True)

    def __unicode__(self):
        return self.descripcion


class Proveedor(BaseModel):
    _PROVINCIA_CHOICES = (
        ("BA", "Buenos Aires"),
        ("CT", "Corrientes"),
        ("CC", "Chaco"),
        ("CP", "Capital Federal"),
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
    _COND_IVA_CHOICES = (
        ("RI", "Responsable Inscripto"),
        ("RE", "Responsable Exento"),
        ("MO", "Monotributo"),
    )
    razon_social = models.CharField(max_length=150, help_text="Razón Social del proveedor")
    direccion = models.CharField(max_length=150, help_text="Dirección del proveedor. <strong>Opcional.</strong>", blank=True)
    localidad = models.CharField(max_length=80, help_text="Localidad del proveedor. <strong>Opcional.</strong>", blank=True)
    codigo_postal = models.CharField(max_length=8, blank=True, help_text="Código postal del proveedor. <strong>Opcional.</strong>")
    provincia = models.CharField(max_length=30, blank=True, choices=_PROVINCIA_CHOICES, help_text="Provincia de residencia.  <strong>Opcional.</strong>")
    pais = models.CharField(max_length=30, blank=True, default="Argentina", help_text="País de residencia de la casa matriz.  <strong>Opcional.</strong>")
    telefono = models.CharField(max_length=30, blank=True, help_text="Teléfono de contacto. <strong>Opcional.</strong>")
    fax = models.CharField(max_length=30, help_text="Fax del proveedor. <strong>Opcional.</strong>", blank=True)
    email = models.EmailField(max_length=254, blank=True, help_text="E-mail del proveedor. <strong>Opcional.</strong>", verbose_name="E-mail")
    cuit = models.CharField(max_length=13, help_text="CUIT del proveedor.", verbose_name="CUIT")
    condicion_iva = models.CharField(max_length=30, choices=_COND_IVA_CHOICES, default="RI", help_text="Condición fiscal del proveedor", verbose_name="Condición fiscal")
    codigo_ingresos_brutos = models.CharField(max_length=15, blank=True, help_text="Número de ingresos brutos. <strong>Opcional.</strong>", verbose_name="Nro. Ingresos brutos")
    contacto = models.CharField(max_length=50, blank=True, help_text="Persona de contacto. <strong>Opcional.</strong>")
    condicion_pago = models.CharField(max_length=60, blank=True, help_text="Condición pago aclaratorio. <strong>Opcional.</strong>", verbose_name="Condición de pago")
    saldo = models.DecimalField(max_digits=13, decimal_places=2, editable=False, default=0)
    notas = models.CharField(max_length=400, blank=True, help_text="Observaciones. <strong>Opcional.</strong>")
    modificado_por = models.ForeignKey(User, editable=False, default=None)
    modificado_el = models.DateField(editable=False, auto_now=True)

    def __unicode__(self):
        return self.razon_social

    def saldo_anterior(self, fecha):
        pro = Q(proveedor=self)
        fef = Q(fecha__lte=fecha)
        fact = Compra.objects.filter(pro, fef)
        ret = 0
        for f in fact:
            ret += f.total
        ops = Detalle_pago.objects.filter(orden_pago__proveedor=self, orden_pago__fecha__lte=fecha).aggregate(
            total=Sum("monto"))
        if ops['total']:
            ret -= ops['total']
        return ret

    def saldo_total(self):
        pro = Q(proveedor=self)
        fact = Compra.objects.filter(pro).aggregate(total=Sum("total"))
        ops = Detalle_pago.objects.filter(orden_pago__proveedor=self).aggregate(total=Sum("monto"))
        ret = 0
        if fact['total']:
            ret += fact['total']
        if ops['total']:
            ret -= ops['total']
        return ret


class Compra(models.Model):
    TIPOS_CHOICES = (
        ("FAA", "FAA"),
        ("FAB", "FAB"),
        ("FAC", "FAC"),
        ("NCA", "NCA"),
        ("NCB", "NCB"),
        ("NCC", "NCC"),
        ("NDA", "NDA"),
        ("NDB", "NDB"),
        ("NDC", "NDC"),
    )
    fecha_hora = models.DateTimeField(default=django.utils.timezone.now, editable=False)
    tipo = models.CharField(max_length=3, choices=TIPOS_CHOICES)
    punto_venta = models.IntegerField()
    numero = models.IntegerField()
    fecha = models.DateField(default=django.utils.timezone.now)
    condicion_compra = models.ForeignKey(Condicion_compra)
    proveedor = models.ForeignKey(Proveedor)
    # flete = models.DecimalField(max_digits=13, decimal_places=3, default=Decimal('0.000'))
    neto = models.DecimalField(max_digits=12, decimal_places=2, editable=False, blank=True, null=True)
    iva21 = models.DecimalField(max_digits=12, decimal_places=2, editable=False, blank=True, null=True)
    iva105 = models.DecimalField(max_digits=12, decimal_places=2, editable=False, blank=True, null=True)
    iva27 = models.DecimalField(max_digits=12, decimal_places=2, editable=False, blank=True, null=True)
    percepcion_iva = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    exento = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    ingresos_brutos = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    impuesto_interno = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    redondeo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    # total = models.DecimalField(max_digits=12, decimal_places=2, editable=False, blank=True, null=True)
    periodo = models.ForeignKey(Periodo)
    # pagado = models.BooleanField(editable=False, default=False)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def __unicode__(self):
        return "Comprobante %s con fecha %s" % (self.identificador_completo, self.fecha_dd_mm_aaaa)

    @property
    def pagado(self):
        print self.saldo
        return True if self.saldo == 0 else False

    @property
    def total(self):
        return self.neto + self.iva + self.percepcion_iva + self.exento + self.ingresos_brutos + self.impuesto_interno + self.redondeo

    @property
    def estado(self):
        return "Pagado" if self.pagado else "Pendiente"

    def fechs_dd_mm_aaaa(self):
        return self.fecha.strftime('%d/%m/%Y')


    def pto_vta_formateado(self):
        ptovta = str(self.punto_venta)
        if (0 < len(ptovta) < 5):
            restante = 4 - len(ptovta)
            if (restante != 0):
                for i in range(restante):
                    ptovta = '0' + ptovta
        return ptovta

    def num_comp_formateado(self):
        num = str(self.numero)
        if (0 < len(num) < 9):
            restante = 8 - len(num)
            if (restante != 0):
                for i in range(restante):
                    num = '0' + num
        return num

    @property
    def identificador(self):
        return "%s - %s" % (self.pto_vta_formateado(), self.num_comp_formateado())

    @property
    def identificador_completo(self):
        return "%s %s - %s" % (self.tipo, self.pto_vta_formateado(), self.num_comp_formateado())

    @property
    def iva(self):
        return self.iva105 + self.iva21 + self.iva27

    @property
    def fecha_dd_mm_aaaa(self):
        return self.fecha.strftime('%d/%m/%Y')

    @property
    def SALDO(self):
        resto = self.total
        pagos = Detalle_pago.objects.filter(compra=self)
        for pago in pagos:
            resto -= pago.monto
        return resto

    '''
    @return: [String] Codigo segun tabla comprobantes AFIP
    '''

    @property
    def codigo_comprobante_segun_afip(self):
        if self.tipo == "FAA":
            return "001"
        elif self.tipo == "FAB":
            return "006"
        elif self.tipo == "NCA":
            return "003"
        elif self.tipo == "NCB":
            return "008"
        elif self.tipo == "NDA":
            return "005"
        elif self.tipo == "NDB":
            return "007"
        elif self.tipo == "FAC":
            return "011"
        elif self.tipo == "NDC":
            return "012"
        elif self.tipo == "NCC":
            return "013"

    @property
    def codigo_moneda_segun_afip(self):
        # Devuelve $ (pesos argentinos)
        return 'PES'


class Detalle_compra(models.Model):
    IVA_CHOICES = (
        (0, "No Aplica"),
        (10.5, "10.5%"),
        (21, "21%"),
        (27, "27%")
    )
    compra = models.ForeignKey(Compra)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    detalle = models.TextField(max_length=200)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    iva_alicuota = models.FloatField(choices=IVA_CHOICES, default=21, blank=True, null=True)
    iva_valor = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def total(self):
        return self.precio_unitario + self.iva_valor


class OrdenPago(models.Model):
    fecha_hora = models.DateTimeField(auto_now_add=True, editable=False)
    fecha = models.DateField(auto_now_add=True)
    numero = models.IntegerField(blank=True, null=True)
    proveedor = models.ForeignKey(Proveedor)
    compra = models.ManyToManyField(Compra, through='Detalle_pago')
    credito_anterior = models.DecimalField(max_digits=12, decimal_places=2)

    def __unicode__(self):
        return "Orden Pago nro: %s -> %s" % (self.numero_full, self.proveedor.razon_social)

    def fecha_dd_mm_aaaa(self):
        return self.fecha.strftime('%d/%m/%Y')

    @property
    def numero_full(self):
        num = str(self.numero)
        if (0 < len(num) < 9):
            restante = 8 - len(num)
            if (restante != 0):
                for i in range(restante):
                    num = '0' + num
        return num

    @property
    def total(self):
        total = self.dinero_set.all().aggregate(Sum('monto'))['monto__sum']
        return total

    @property
    def total_str(self):
        return "%.2f" % self.total

    @property
    def saldo_a_cuenta(self):
        dinero = self.dinero_set.all().aggregate(Sum('monto'))['monto__sum']
        compro = self.detalle_pago_set.all().aggregate(Sum('monto'))['monto__sum']

        return dinero + self.credito_anterior - compro or 0


class Detalle_pago(models.Model):
    compra = models.ForeignKey(Compra)
    orden_pago = models.ForeignKey(OrdenPago)
    monto = models.DecimalField(max_digits=12, decimal_places=2)

    def __unicode__(self):
        return "%s, compra: %s, monto %s" % (self.orden_pago, self.compra, self.monto)

    def monto_2d(self):
        return "%.2f" % self.monto
