# -*- coding: utf-8 -*-
import re

import django
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from core.models import Periodo, Transporte, BaseModel
from django.contrib.auth.models import User
from django.db.models.aggregates import Sum
from decimal import Decimal

IVA_CHOICES = (
    ("IVA00", "EXENTO"),
    ("IVA21", "IVA 21%"),
    ("IV105", "IVA 10.5%"),
    ("IVA27", "IVA 27%"),
)

IVA_CALC = {'IVA00': Decimal(0), 'IV105': Decimal(0.105), 'IVA21': Decimal(0.21), 'IVA27': Decimal(0.27)}


class Rubro(models.Model):
    cod = models.IntegerField(help_text="Código del rubro", verbose_name="Código", unique=True)
    nombre = models.CharField(max_length=50, help_text="Nombre del rubro", unique=True)
    iva = models.CharField(max_length=5, choices=IVA_CHOICES, help_text="Alícuota de IVA asociada al rubro",
                           verbose_name="Alícuota IVA")

    def __unicode__(self):
        return self.nombre


class SubRubro(models.Model):
    rubro = models.ForeignKey(Rubro)
    nombre = models.CharField(max_length=50, help_text="Nombre del subrubro")
    iva = models.CharField(max_length=5, choices=IVA_CHOICES,
                           help_text="Alícuota de IVA asociada al subrubro. Si no selecciona ninguna usa la del rubro correspondiente.",
                           verbose_name="Alícuota IVA", blank=True)

    class Meta:
        unique_together = ('rubro', 'nombre')

    def __unicode__(self):
        return "%s (%s)" % (self.nombre, self.rubro.nombre)


class Linea(models.Model):
    nombre = models.CharField(max_length=50, help_text="Nombre de la línea", unique=True)

    def __unicode__(self):
        return self.nombre


class Articulo(BaseModel):
    UNIDADES_CHOICES = (
        ("UN", "Unidades"),
        ("KG", "Kilogramos"),
        ("HS", "Horas"),
        ("MT", "Metros"),
    )

    codigo = models.CharField(max_length=60, unique=True, help_text="Codigo de inventario.")
    codigo_fabrica = models.CharField(max_length=70, blank=True,
                                      help_text="Código de fabrica. <strong>Opcional.</strong>")
    denominacion = models.CharField(max_length=200, help_text="Denominación del artículo")
    informacion_adicional = models.TextField(blank=True,
                                             help_text="Información adicional del artículo. <strong>Opcional.</strong>")
    subrubro = models.ForeignKey('ventas.SubRubro',
                                 help_text="Subrubro del artículo. Recuerde que este pertenece a un rubro.")
    proveedor_primario = models.ForeignKey('compras.Proveedor', related_name="proveedor_primario",
                                           help_text="Proveedor primario de este artículo. <strong>Opcional.</strong>",
                                           blank=True, null=True)
    proveedor_secundario = models.ForeignKey('compras.Proveedor', related_name="proveedor_secundario", blank=True,
                                             null=True,
                                             help_text="Proveedor secundario de este artículo. <strong>Opcional.</strong>")
    unidad_medida = models.CharField(max_length=2, choices=UNIDADES_CHOICES, default="UN")
    costo_compra = models.DecimalField(max_digits=13, decimal_places=2, help_text="Precio de compra")
    descuento_compra = models.DecimalField(max_digits=13, decimal_places=2,
                                           help_text="Porcentaje descuento sobre precio compra.")
    ganancia_venta = models.DecimalField(max_digits=13, decimal_places=2,
                                         help_text="Porcentaje de ganancia del artículo")
    linea = models.ForeignKey('ventas.Linea', help_text="Línea del artículo.")
    fecha_ultima_compra = models.DateField(editable=False, blank=True, null=True)
    proveedor_ultima_compra = models.ForeignKey('compras.Proveedor', related_name="ultimo_proveedor", editable=False,
                                                blank=True, null=True)
    ultima_actualizacion_precio = models.DateField(editable=False, blank=True, null=True)
    modificado_por = models.ForeignKey(User, blank=True, editable=False)
    iva = models.CharField(max_length=5, choices=IVA_CHOICES, help_text="Alícuota de IVA asociada al articulo",
                           verbose_name="Alícuota IVA")

    def __unicode__(self):
        return self.denominacion_ampliada()

    def denominacion_ampliada(self):
        return "%s - %s - %s" % (self.codigo, self.codigo_fabrica, self.denominacion)

    def _descuento_sobre_costo_compra(self):
        '''
        @return: Valor del descuento sobre el costo de compra
        @rtype: Decimal
        '''

        return self.costo_compra * self.descuento_compra / 100

    def descuento_sobre_costo_compra(self):
        '''
        @return: Valor del descuento sobre el costo de compra
        @rtype: String
        '''

        return "%.2f" % self._descuento_sobre_costo_compra()

    def _costo_compra_real(self):
        '''
        @return: Costo de compra con descuento
        @rtype: Decimal
        '''

        return self.costo_compra - self._descuento_sobre_costo_compra()

    def costo_compra_real(self):
        '''
        @return: Costo de compra con descuento
        @rtype: String
        '''

        return "%.2f" % self._costo_compra_real()

    def _ganancia_real(self):
        '''
        @return: Valor de ganancia del articulo
        @rtype: Decimal
        '''

        return Decimal(1) + (self.ganancia_venta / Decimal(100))

    def ganancia_real(self):
        '''
        @return: Valor de ganancia del articulo
        @rtype: String
        '''

        return "%.2f" % self._ganancia_real()

    def _precio_venta(self):
        '''
        @return: Valor del precio de venta del articulo
        @rtype: Decimal
        '''
        pv = self._costo_compra_real() * self._ganancia_real()
        return pv

    @property
    def precio_venta(self):
        '''
        @return: Valor del precio de venta del articulo
        @rtype: String
        '''
        pv = self._costo_compra_real() * self._ganancia_real()
        return "%.2f" % pv

    def alicuota_iva(self):
        if self.iva:
            return self.iva
        elif self.subrubro.iva:
            return self.subrubro.iva
        else:
            return self.subrubro.rubro.iva

    def _iva_articulo(self):
        '''
        @return: Valor de IVA del articulo
        @rtype: Decimal
        '''
        return self._precio_venta() * Decimal(IVA_CALC[self.iva])

    def iva_articulo(self):
        '''
        @return: Valor de IVA del articulo
        @rtype: String
        '''
        return "%.2f" % self._iva_articulo()

    def _precio_venta_iva_inc(self):
        '''
        @return: Valor precio del articulo iva incluido
        @rtype: Decimal
        '''
        pvii = self._precio_venta() + self._iva_articulo()
        return pvii

    @property
    def precio_venta_iva_inc(self):
        '''
        @return: Valor precio del articulo iva incluido
        @rtype: String
        '''
        return "%.2f" % self._precio_venta_iva_inc()


class Condicion_venta(models.Model):
    descripcion = models.CharField(max_length=50, help_text="Descripcion", unique=True)

    def __unicode__(self):
        return self.descripcion


class Cliente(BaseModel):
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
    COND_IVA_CHOICES = (
        ("RI", "Responsable Inscripto"),
        ("MO", "Monotributo"),
        ("CF", "Consumidor Final"),
    )
    razon_social = models.CharField(max_length=100, help_text="Razón social del cliente")
    direccion = models.CharField(max_length=100, help_text="Dirección del cliente", blank=True)
    localidad = models.CharField(max_length=100, help_text="Localidad de residencia del cliente", blank=True)
    codigo_postal = models.CharField(max_length=8, help_text="CP del cliente", blank=True)
    provincia = models.CharField(max_length=30, help_text="Provincia de residencia del cliente",
                                 choices=PROVINCIA_CHOICES, blank=True)
    telefono = models.CharField(max_length=60, help_text="Telefono de contacto del cliente", blank=True)
    fax = models.CharField(max_length=60, help_text="Fax del cliente", blank=True)
    email = models.EmailField(max_length=254, blank=True)
    cuit = models.CharField(max_length=13, blank=True)
    dni = models.CharField(max_length=8, blank=True)
    codigo_iva = models.CharField(max_length=25, blank=True)
    cond_iva = models.CharField(max_length=40, blank=True, choices=COND_IVA_CHOICES)
    codigo_ingresos_brutos = models.CharField(max_length=15, blank=True)
    transporte_preferido = models.ForeignKey(Transporte, help_text="Transporte preferido por el cliente", blank=True,
                                             null=True)
    ultima_compra = models.DateField(help_text="Fecha de última compra", editable=False, blank=True, null=True)
    ultimo_pago = models.DateField(help_text="Fecha último pago", editable=False, blank=True, null=True)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0)
    notas = models.CharField(max_length=400, blank=True)
    modificado_por = models.ForeignKey(User, editable=False, blank=True)

    class Meta:
        ordering = ['razon_social']

    def __unicode__(self):
        return self.razon_social

    '''
    @return: Decimal - Saldo total a la fecha del cliente.
    '''

    def saldo_total(self):
        cli = Q(cliente=self)
        fact = Q(tipo__startswith="FA")
        nd = Q(tipo__startswith="ND")
        apr = Q(aprobado=True)
        factynd = Venta.objects.filter(cli, apr, fact | nd).aggregate(total=Sum("total"))
        nc = Q(tipo__startswith="NC")
        ncrs = Venta.objects.filter(cli, apr, nc).aggregate(total=Sum("total"))
        recibos = Detalle_cobro.objects.filter(recibo__cliente=self).aggregate(total=Sum("monto"))
        ret = 0
        if factynd['total']:
            ret += factynd['total']
        if ncrs['total']:
            ret -= ncrs['total']
        if recibos['total']:
            ret -= recibos['total']
        return ret

    def saldo_anterior(self, fecha):
        cli = Q(cliente=self)
        fact = Q(tipo__startswith="FA")
        nd = Q(tipo__startswith="ND")
        apr = Q(aprobado=True)
        # fer=Q(recibo__fecha__lt=fecha)
        fef = Q(fecha__lt=fecha)
        factynd = Venta.objects.filter(cli, apr, fef, fact | nd).aggregate(total=Sum("total"))
        nc = Q(tipo__startswith="NC")
        ncrs = Venta.objects.filter(cli, apr, fef, nc).aggregate(total=Sum("total"))
        recibos = Detalle_cobro.objects.filter(recibo__cliente=self, recibo__fecha__lte=fecha).aggregate(
            total=Sum("monto"))
        ret = 0
        if factynd['total']:
            ret += factynd['total']
        if ncrs['total']:
            ret -= ncrs['total']
        if recibos['total']:
            ret -= recibos['total']
        return ret


class Venta(models.Model):
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
    punto_venta = models.IntegerField(blank=True, null=True, editable=False)
    numero = models.IntegerField(blank=True, null=True, editable=False)
    fecha = models.DateField(default=django.utils.timezone.now, verbose_name="Fecha")
    cliente = models.ForeignKey(Cliente)
    condicion_venta = models.ForeignKey(Condicion_venta, verbose_name="Condición de venta", default=2)
    # transporte = models.ForeignKey(Transporte, blank=True, null=True)
    # vendedor = models.ForeignKey(User)
    #########################################articulos = models.ManyToManyField(Articulo, through='Detalle_venta')
    # flete = models.DecimalField(max_digits=13, decimal_places=3, default=Decimal('0.000'))
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, editable=False, blank=True, null=True)
    neto = models.DecimalField(max_digits=12, decimal_places=2, editable=False, blank=True, null=True)
    iva21 = models.DecimalField(max_digits=12, decimal_places=2, editable=False, blank=True, null=True)
    iva105 = models.DecimalField(max_digits=12, decimal_places=2, editable=False, blank=True, null=True)
    iva27 = models.DecimalField(max_digits=13, decimal_places=3, editable=False, blank=True, null=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, editable=False, blank=True, null=True)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, blank=True, default=Decimal("0.00"))
    aprobado = models.BooleanField(default=False, editable=False)
    periodo = models.ForeignKey(Periodo)
    cae = models.CharField(max_length=50, blank=True, null=True, editable=False)
    fvto_cae = models.DateField(blank=True, editable=False, null=True)
    # comprobantes_relacionados = models.ManyToManyField('self', blank=True, null=True, default=None, symmetrical=False, related_name="crs")
    pagado = models.BooleanField(editable=False, default=False)
    # comprobante_relacionado = models.ForeignKey('self', blank=True, null=True, default=None)
    # comprobantes_relacionados = models.ManyToManyField('self', blank=True, default=None)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, editable=False, blank=True, null=True)

    def __unicode__(self):
        return "%s, %s-%s --- Fecha: %s" % (
            self.tipo_full(), self.pto_vta_full(), self.num_comp_full(), self.fecha_dd_mm_aaaa())

    def estado(self):
        return "Aprobado" if self.aprobado else "Borrador"

    def descuento_importe(self):
        return self.subtotal * self.descuento / Decimal(100)

    def tipo_full(self):
        if self.tipo == "FAA":
            return "Factura A"
        elif self.tipo == "FAB":
            return "Factura B"
        elif self.tipo == "FAC":
            return "Factura C"
        elif self.tipo == "NCA":
            return "Nota de crédito A"
        elif self.tipo == "NCB":
            return "Nota de crédito B"
        elif self.tipo == "NCC":
            return "Nota de crédito C"
        elif self.tipo == "NDA":
            return "Nota de débito A"
        elif self.tipo == "NDB":
            return "Nota de débito B"
        elif self.tipo == "NDC":
            return "Nota de débito C"
        else:
            return "N/A"

    @property
    def info_completa(self):
        if self.pto_vta_full() and self.num_comp_full():
            return "%s %s-%s" % (self.tipo_full(), self.pto_vta_full(), self.num_comp_full())
        else:
            return "%s (NO ASIGNADO AUN)" % self.tipo_full()

    @property
    def info_completa_informe(self):
        return "%s %s-%s" % (self.tipo, self.pto_vta_full(), self.num_comp_full())

    @property
    def pto_vta_num_full(self):
        if self.pto_vta_full() and self.num_comp_full():
            return "%s - %s" % (self.pto_vta_full(), self.num_comp_full())
        else:
            return "NO ASIGNADO AUN"

    def neto_2dec(self):
        return "%.2f" % self.neto

    def iva21_2dec(self):
        return "%.2f" % self.iva21

    @property
    def TOTAL(self):
        return round(self.total, 2)

    def total_2dec(self):
        return "%.2f" % self.total

    def fecha_dd_mm_aaaa(self):
        return self.fecha.strftime('%d/%m/%Y')

    def vto_cae_dd_mm_aaaa(self):
        return self.fvto_cae.strftime('%d/%m/%Y')

    def pto_vta_full(self):
        if self.punto_venta:
            return str(self.punto_venta).rjust(4, "0")
        else:
            return None

    def num_comp_full(self):
        if self.numero:
            return str(self.numero).rjust(8, "0")
        else:
            return None

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

    @property
    def codigo_moneda_segun_afip(self):
        # Devuelve $ (pesos argentinos)
        return 'PES'

    def items_set(self):
        # Devuelve todos los items en un array, ordenado por el numero de renglon
        items = []
        almacenados = self.almacenado_venta.all()
        personalizados = self.personalizado_venta.all()
        compuestos = self.compuesto_venta.all()
        if almacenados:
            map(lambda x: items.append(x), almacenados)
        if personalizados:
            map(lambda x: items.append(x), personalizados)
        if compuestos:
            map(lambda x: items.append(x), compuestos)
        items = sorted(items, key=lambda obj: obj.renglon)
        return items


class Item_almacenados(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE,
                              related_name='almacenado_venta')  # Puede ser una venta o un Item_compuesto
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    articulo = models.ForeignKey(Articulo, blank=True, null=True)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, blank=True)
    comprobante_relacionado = models.ForeignKey(Venta, related_name='almacenado_comprobante_relacionado', blank=True,
                                                null=True)
    renglon = models.IntegerField()

    def descuento_value(self):
        if self.venta.tipo.endswith('B'):
            return self.articulo._precio_venta_iva_inc() * self.descuento / 100
        else:
            return self.articulo._precio_venta() * self.descuento / 100

    def subtotal(self):
        if self.venta.tipo.endswith('B'):
            return self.cantidad * (
                self.articulo._precio_venta_iva_inc() - (self.articulo._precio_venta_iva_inc() * self.descuento / 100))
        else:
            return self.cantidad * (
                self.articulo._precio_venta() - (self.articulo._precio_venta() * self.descuento / 100))

    def neto(self):
        if self.venta.tipo.endswith('B'):
            return self.subtotal() / (1 + IVA_CALC[self.articulo.iva])
        else:
            return self.subtotal()

    def iva_value(self):
        if self.venta.tipo.endswith('C'):
            return Decimal("0")
        else:
            return self.neto() * IVA_CALC[self.articulo.iva]


class Item_personalizados(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE,
                              related_name='personalizado_venta')  # Puede ser una venta o un Item_compuesto
    descripcion = models.TextField(max_length=60)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    linea = models.ForeignKey(Linea, null=True, blank=True)
    iva = models.CharField(max_length=5, choices=IVA_CHOICES, blank=True)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, blank=True)
    comprobante_relacionado = models.ForeignKey(Venta, related_name='personalizado_comprobante_relacionado', blank=True,
                                                null=True)
    renglon = models.IntegerField()

    def subtotal(self):
        return self.cantidad * (self.precio_unitario - (self.precio_unitario * self.descuento / 100))

    def neto(self):
        if self.venta.tipo.endswith('B'):
            return self.subtotal() / (1 + IVA_CALC[self.iva])
        else:
            return self.subtotal()

    def iva_value(self):
        if self.venta.tipo.endswith('C'):
            return Decimal("0")
        else:
            return self.neto() * IVA_CALC[self.iva]

    def descuento_value(self):
        return self.precio_unitario * self.descuento / 100


class Item_compuesto(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE,
                              related_name='compuesto_venta')  # Necesariamente es una venta
    descripcion = models.TextField(max_length=60, blank=True)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    linea = models.ForeignKey(Linea, null=True, blank=True)
    iva = models.CharField(max_length=5, choices=IVA_CHOICES, blank=True)
    descuento = models.DecimalField(max_digits=5, decimal_places=2, blank=True)
    comprobante_relacionado = models.ForeignKey(Venta, related_name='compuesto_comprobante_relacionado', blank=True,
                                                null=True)
    renglon = models.IntegerField()

    def precio_unitario(self):
        pu = reduce(lambda x, y: x + y, [item.subtotal() for item in
                                         self.item_compuesto_almacenado_set.all()]) if self.item_compuesto_almacenado_set.all() else 0
        pu += reduce(lambda x, y: x + y, [item.subtotal() for item in
                                          self.item_compuesto_personalizado_set.all()]) if self.item_compuesto_personalizado_set.all() else 0
        return pu

    def subtotal(self):
        subtotal = reduce(lambda x, y: x + y, [item.subtotal() for item in
                                               self.item_compuesto_almacenado_set.all()]) if self.item_compuesto_almacenado_set.all() else 0
        subtotal += reduce(lambda x, y: x + y, [item.subtotal() for item in
                                                self.item_compuesto_personalizado_set.all()]) if self.item_compuesto_personalizado_set.all() else 0
        return self.cantidad * (subtotal - (subtotal * self.descuento / 100))

    def neto(self):
        if self.venta.tipo.endswith('B'):
            return self.subtotal() / (1 + IVA_CALC[self.iva])
        else:
            return self.subtotal()

    def iva_value(self):
        if self.venta.tipo.endswith('C'):
            return Decimal("0")
        else:
            return self.neto() * IVA_CALC[self.iva]

    def descuento_value(self):
        subtotal = reduce(lambda x, y: x + y, [item.subtotal() for item in
                                               self.item_compuesto_almacenado_set.all()]) if self.item_compuesto_almacenado_set.all() else 0
        subtotal += reduce(lambda x, y: x + y, [item.subtotal() for item in
                                                self.item_compuesto_personalizado_set.all()]) if self.item_compuesto_personalizado_set.all() else 0
        return subtotal * self.descuento / 100


class Item_compuesto_almacenado(models.Model):
    item_compuesto = models.ForeignKey(Item_compuesto, on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    articulo = models.ForeignKey(Articulo, blank=True, null=True)

    def subtotal(self):
        if self.item_compuesto.venta.tipo.endswith('B'):
            return self.cantidad * self.articulo._precio_venta_iva_inc()
        else:
            return self.cantidad * self.articulo._precio_venta()


class Item_compuesto_personalizado(models.Model):
    item_compuesto = models.ForeignKey(Item_compuesto, on_delete=models.CASCADE)
    descripcion = models.TextField(max_length=60)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio_unitario


class Recibo(models.Model):
    fecha_hora = models.DateTimeField(default=django.utils.timezone.now, editable=False)
    fecha = models.DateField(default=django.utils.timezone.now)
    numero = models.IntegerField(blank=True, null=True)
    cliente = models.ForeignKey(Cliente)
    venta = models.ManyToManyField(Venta, through='Detalle_cobro')
    credito_anterior = models.DecimalField(max_digits=13, decimal_places=3, default=0.000)
    a_cuenta = models.DecimalField(max_digits=13, decimal_places=3, default=0.000)

    def __unicode__(self):
        return "Recibo nro: %s -> %s" % (self.numero_full, self.cliente.razon_social)

    def get_a_credito(self):
        '''
        @return: Decimal o 0, dependiendo si hay credito.
        '''
        # total_comprobantes = self.detalle_cobro_set.all().aggregate(Sum('monto'))['monto__sum']
        # total_valores = self.dinero_set.all().aggregate(Sum('monto'))['monto__sum']
        # print (total_comprobantes,total_valores)
        return self.cliente.saldo or 0
        # return total_valores-total_comprobantes or 0

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
        # detalles = Detalle_cobro.objects.filter(recibo__id=self.id)
        # total = 0
        # for det in detalles:
        #    total += det.monto
        # a_cuenta = Cobranza_a_cuenta.objects.filter(recibo__id=self.id)
        # if a_cuenta:
        ##    total += a_cuenta[0].monto
        ##cred_ant = Cobranza_credito_anterior.objects.filter(recibo__id=self.id)
        # if cred_ant:
        #    total -= cred_ant[0].monto
        return total

    @property
    def total_str(self):
        return "%.2f" % self.total


class Detalle_cobro(models.Model):
    venta = models.ForeignKey(Venta)
    recibo = models.ForeignKey(Recibo)
    monto = models.DecimalField(max_digits=13, decimal_places=3)

    def __unicode__(self):
        return "%s, venta: %s, monto %.2f" % (self.recibo, self.venta, self.monto)

    def monto_2d(self):
        return "%.2f" % self.monto
