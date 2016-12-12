# -*- coding: utf-8 -*-
import re

from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import RadioSelect

from core.forms import MDLBaseModelForm, customize_field, AutoCompleteMDLFKField, AutoCompleteFKMultiWidget, \
    MDLBaseForm, IntegerFieldMDL
from core.models import Periodo, Bancos, CuentasBanco
from ventas.models import Articulo, Cliente, Rubro, SubRubro, Linea, Condicion_venta, Venta, IVA_CHOICES, Recibo
import core.widgets


class RubrosForm(MDLBaseModelForm):
    formfield_callback = customize_field

    class Meta:
        model = Rubro
        fields = '__all__'


class SubrubrosForm(MDLBaseModelForm):
    formfield_callback = customize_field

    class Meta:
        model = SubRubro
        fields = '__all__'


class LineasForm(MDLBaseModelForm):
    formfield_callback = customize_field

    class Meta:
        model = Linea
        fields = '__all__'


class ArticulosForm(MDLBaseModelForm):
    formfield_callback = customize_field

    class Meta:
        model = Articulo
        fields = '__all__'
        exclude = ['suspendido', 'modificado_por']


class CondicionesVentaForm(MDLBaseModelForm):
    class Meta:
        model = Condicion_venta
        fields = '__all__'


class ClientesForm(MDLBaseModelForm):
    formfield_callback = customize_field

    def clean(self):
        cd = super(ClientesForm, self).clean()
        blank_dni = True if cd['dni'] == '' else False
        cero_dni = False
        if not blank_dni:
            cero_dni = True if int(reduce(lambda x, y: int(x) + int(y), [l for l in cd['dni']])) == 0 else False
        blank_cuit = True if cd['cuit'] == '' else False
        cero_cuit = False
        if not blank_cuit:
            cero_cuit = True if int(
                reduce(lambda x, y: int(x) + int(y), [l for l in cd['cuit'].replace("-", "")])) == 0 else False
        if (blank_dni or cero_dni) and (blank_cuit or cero_cuit):
            raise ValidationError('Debe ingresar el DNI o el CUIT')
        else:
            if not blank_dni and not cero_dni and len(Cliente.objects.filter(dni=cd['dni'])) > 0 and not self.instance == Cliente.objects.get(dni=cd['dni']):
                raise ValidationError('El DNI ingresado ya se encuentra cargado')
            if not (cero_cuit or blank_cuit):
                if len(Cliente.objects.filter(cuit=cd['cuit'])) > 0 and not self.instance == Cliente.objects.get(cuit=cd['cuit']):
                    raise ValidationError('El CUIT ingresado ya se encuentra cargado')
                if not re.match(r'\d{2}-\d{8}-\d{1}', cd['cuit']):
                    raise ValidationError('CUIT incorrecto')
        if cd['cond_iva'] == "RI" and (blank_cuit or cero_cuit):
            raise ValidationError("Para un cliente Resposable Inscripto debe ingresar un CUIT")

    class Meta:
        model = Cliente
        fields = '__all__'
        exclude = ['suspendido', 'modificado_por']


class VentaForm(MDLBaseModelForm):
    formfield_callback = customize_field
    condicion_venta = forms.ModelChoiceField(queryset=Condicion_venta.objects.all(), initial=2)

    TIPODISPLAYCHOICES = (("FA", "Factura"),
                          ("NC", "Nota de crédito"),
                          ("ND", "Nota de débito"))

    tipoDisplay = forms.ChoiceField(choices=TIPODISPLAYCHOICES, label="Tipo", label_suffix="")

    class Meta:
        model = Venta
        exclude = ('periodo', 'tipo', 'subtotal')


class ItemVenta(forms.Form):
    tipo = forms.CharField(widget=forms.HiddenInput(attrs={'class': 'detalle-tipo'}), initial='AA')
    cantidad = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'detalle-cantidad'}))
    articulo_almacenado = AutoCompleteMDLFKField(queryset=Articulo.objects.all(), widget=AutoCompleteFKMultiWidget(
        attrs={'class': 'detalle-articulo_almacenado', 'style': 'width:100%;'}), required=False)
    descripcion = forms.CharField(max_length=60, widget=forms.TextInput(
        attrs={'class': 'detalle-descripcion'}), required=False)
    iva = forms.ChoiceField(choices=IVA_CHOICES, initial='IVA21', widget=forms.Select(attrs={'class': 'detalle-iva'}),
                            required=False)
    linea = forms.ModelChoiceField(queryset=Linea.objects.all(), empty_label=None,
                                   widget=forms.Select(attrs={'class': 'detalle-linea'}), required=False)
    precio_unitario = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'detalle-precio_unitario'}))
    descuento = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'detalle-descuento'}), required=False)

    def clean_articulo_almacenado(self):
        aa = self.cleaned_data['articulo_almacenado']
        tipo = self.cleaned_data['tipo']
        if tipo == 'AA' and (aa == '' or aa is None):
            raise ValidationError('Seleccione un artículo')
        return aa

    def clean_descripcion(self):
        desc = self.cleaned_data['descripcion']
        tipo = self.cleaned_data['tipo']
        if (desc == '' or desc is None) and (tipo == 'AP' or tipo == 'AC'):
            raise ValidationError('Ingrese la descripción')
        return desc


class ItemArticuloCompuesto(forms.Form):
    pers = forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': 'compuesto-pers'}), required=False)
    cantidad = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'compuesto-cantidad'}))
    articulo_almacenado = AutoCompleteMDLFKField(queryset=Articulo.objects.all(), widget=AutoCompleteFKMultiWidget(
        attrs={'class': 'compuesto-articulo_almacenado', 'style': 'width:100%;'}), required=False)
    descripcion = forms.CharField(max_length=60, widget=forms.TextInput(
        attrs={'class': 'compuesto-descripcion', 'style': 'width:100%;'}), required=False)
    precio_unitario = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'compuesto-precio_unitario'}))

    def clean_articulo_almacenado(self):
        aa = self.cleaned_data['articulo_almacenado']
        pers = self.cleaned_data['pers']
        if not pers and (aa is None or aa == ''):
            raise ValidationError('Seleccione un artículo')
        return aa

    def clean_descripcion(self):
        desc = self.cleaned_data['descripcion']
        pers = self.cleaned_data['pers']
        if pers and (desc == '' or desc is None):
            raise ValidationError('Ingrese la descripción')
        return desc


class SubdiarioIVAVentPeriodoFecha(MDLBaseForm):
    folio_inicial = IntegerFieldMDL(min_value=1, label="Folio Inicial")
    por = forms.ChoiceField(choices=(('periodo', 'Periodo'), ('fecha', 'Fecha')), initial='periodo', widget=RadioSelect)
    periodo = AutoCompleteMDLFKField(queryset=Periodo.objects.all(), required=False)
    fecha_desde = forms.DateField(required=False)
    fecha_hasta = forms.DateField(required=False)

    def clean(self):
        cleaned_data = super(SubdiarioIVAVentPeriodoFecha, self).clean()
        periodo = cleaned_data.get("periodo")
        fd = cleaned_data.get("fecha_desde")
        fh = cleaned_data.get("fecha_hasta")

        if fd and fh:
            if periodo:
                raise forms.ValidationError(
                    "Debe seleccionar o un periodo o las fechas desde y hasta. No ambas condiciones.")
        elif periodo:
            if fd or fh:
                raise forms.ValidationError(
                    "Debe seleccionar o un periodo o las fechas desde y hasta. No ambas condiciones.")
        elif not fd and not fh and not periodo:
            raise forms.ValidationError("Debe seleccionar un periodo o las fechas desde y hasta.")

        return cleaned_data


class ReciboForm(MDLBaseModelForm):
    que_hago_con_diferencia = forms.ChoiceField(widget=forms.RadioSelect(),
                                                choices=(('credito', 'Dejar a crédito'), ('vuelto', 'Dar vuelto')),
                                                initial='credito')
    formfield_callback = customize_field

    class Meta:
        model = Recibo
        exclude = ('venta', 'credito_anterior', 'a_cuenta', 'numero')


class ReciboContadoForm(MDLBaseModelForm):
    que_hago_con_diferencia = forms.ChoiceField(widget=forms.RadioSelect(),
                                                choices=(('credito', 'Dejar a crédito'), ('vuelto', 'Dar vuelto')),
                                                initial='credito')
    # cliente = AutoCompleteMDLFKField(widget=AutoCompleteFKMultiWidget(attrs={'disabled': 'disabled'}))
    formfield_callback = customize_field

    class Meta:
        model = Recibo
        exclude = ('venta', 'credito_anterior', 'a_cuenta', 'numero')
        # widgets = {
        #     'cliente': AutoCompleteFKMultiWidget(attrs={'disabled': 'disabled'}),
        # }


class DetalleCobroForm(MDLBaseForm):
    pagar = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'entrega_input'}))
    id_factura = forms.CharField(widget=forms.HiddenInput(attrs={'class': 'id_factura'}))


class DetalleCobroContadoForm(MDLBaseForm):
    id_factura = forms.CharField(widget=forms.HiddenInput(attrs={'class': 'id_factura'}))


class ValoresReciboForm(MDLBaseForm):
    TIPOS_CHOICES = (
        ("CHT", "Cheque Tercero"),
        ("EFE", "Efectivo"),
        ("TRB", "Transferencia Bancaria"),
    )
    tipo = forms.ChoiceField(choices=TIPOS_CHOICES, widget=forms.Select(attrs={'class': 'tipo_valor_select'}))
    cheque_numero = forms.CharField(widget=forms.TextInput(attrs={'class': 'cheque_numero_input mdl-textfield__input', 'maxlength': '12'}),
                                    required=False)
    cheque_banco = forms.ModelChoiceField(queryset=Bancos.objects.all(),
                                          widget=forms.Select(attrs={'class': 'cheque_banco_select  mdl-textfield__input'}),
                                          required=False)
    cheque_fecha = forms.DateField(widget=forms.TextInput(attrs={'class': 'cheque_fecha_input  mdl-textfield__input'}),
                                   required=False)
    cheque_cobro = forms.DateField(widget=forms.TextInput(attrs={'class': 'cheque_cobro_input  mdl-textfield__input'}),
                                   required=False)
    cheque_titular = forms.CharField(widget=forms.TextInput(attrs={'class': 'cheque_titular_input  mdl-textfield__input'}),
                                     required=False)
    cheque_cuit_titular = forms.CharField(widget=forms.TextInput(attrs={'class': 'cheque_cuit_titular_input  mdl-textfield__input'}),
                                          required=False)
    cheque_paguese_a = forms.CharField(widget=forms.TextInput(attrs={'class': 'cheque_paguese_a_input  mdl-textfield__input'}),
                                       required=False)
    cheque_domicilio_de_pago = forms.CharField(widget=forms.TextInput(attrs={'class': 'cheque_domicilio_pago_input mdl-textfield__input'}),
                                               required=False)
    transferencia_banco_origen = forms.ModelChoiceField(queryset=Bancos.objects.all(), widget=forms.Select(
        attrs={'class': 'transferencia_banco_origen_select mdl-textfield__input'}), required=False)
    transferencia_cuenta_origen = forms.CharField(widget=forms.TextInput(attrs={'class': 'transferencia_cuenta_origen mdl-textfield__input'}),
                                                  required=False)
    transferencia_numero_operacion = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'transferencia_numero_operacion_input mdl-textfield__input'}),
        required=False)
    transferencia_cuenta_destino = forms.ModelChoiceField(queryset=CuentasBanco.objects.all(), widget=forms.Select(
        attrs={'class': 'transferencia_cuenta_destino_select mdl-textfield__input'}), required=False)
    monto = forms.DecimalField(widget=forms.TextInput(attrs={'class': 'monto_input mdl-textfield__input'}))
