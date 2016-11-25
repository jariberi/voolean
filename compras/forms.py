from django import forms
from django.contrib.admin import widgets
from django.forms.widgets import TextInput
from compras.models import Proveedor, Detalle_compra, Compra
from core.forms import MDLBaseModelForm, customize_field

__author__ = 'jorge'


class ProveedoresForm(MDLBaseModelForm):
    formfield_callback = customize_field

    class Meta:
        model = Proveedor
        fields = '__all__'
        exclude = ['suspendido']


class ComprobanteCompraForm(MDLBaseModelForm):
    formfield_callback = customize_field

    class Meta:
        model = Compra
        exclude = ['saldo']


class DetalleCompraForm(MDLBaseModelForm):

    class Meta:
        model = Detalle_compra
        exclude = ['compra']
