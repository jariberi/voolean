# -*- coding: utf-8 -*-
# Create your views here.
import json
import logging
from decimal import Decimal
from StringIO import StringIO

from django.db.models.query_utils import Q
from django.shortcuts import render_to_response
from django.template.context_processors import csrf
from django.utils.datetime_safe import datetime
from django.views.generic.base import TemplateView, View
from django.views.generic.dates import timezone_today
from geraldo.generators.pdf import PDFGenerator

from afip_ws.wsfev1 import WSFEv1
from core import utils
from ventas.forms import ArticulosForm, ClientesForm, RubrosForm, SubrubrosForm, LineasForm, CondicionesVentaForm, \
    VentaForm, ItemVenta, ItemArticuloCompuesto, \
    SubdiarioIVAVentPeriodoFecha, ReciboForm, DetalleCobroForm, ValoresReciboForm, ReciboContadoForm, \
    DetalleCobroContadoForm
from core.models import FunctionHit, Periodo, Dinero, ChequeTercero, TransferenciaBancariaEntrante
from ventas.models import Cliente, Condicion_venta, Linea, Rubro, Articulo, Venta, SubRubro, Item_almacenados, \
    Item_personalizados, Item_compuesto, Item_compuesto_personalizado, Item_compuesto_almacenado, Detalle_cobro, Recibo
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse_lazy, reverse
from django.http.response import HttpResponseRedirect, HttpResponse, JsonResponse
from django.forms.formsets import BaseFormSet, formset_factory

from ventas.reports import IVAVentas
from voolean.settings import USA_FACTURA_ELECTRONICA, ES_MONOTRIBUTO, CUIT, DEBUG

logger = logging.getLogger("voolean")

class RubrosList(TemplateView):
    template_name = "rubros/rubros_list.html"


class RubrosNuevo(CreateView):
    model = Rubro
    form_class = RubrosForm
    template_name = "rubros/rubros_form.html"
    success_url = reverse_lazy("listaRubros")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.modificado_por = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse_lazy('listaRubros'))


class RubrosModificar(UpdateView):
    model = Rubro
    form_class = RubrosForm
    template_name = "rubros/rubros_form.html"
    success_url = reverse_lazy("listaRubros")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.modificado_por = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse_lazy('listaRubros'))


class SubrubrosList(TemplateView):
    template_name = "subrubros/subrubros_list.html"


class SubrubrosNuevo(CreateView):
    model = SubRubro
    form_class = SubrubrosForm
    template_name = "subrubros/subrubros_form.html"
    success_url = reverse_lazy("listaSubrubros")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.modificado_por = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse_lazy('listaSubrubros'))


class SubrubrosModificar(UpdateView):
    model = SubRubro
    form_class = SubrubrosForm
    template_name = "subrubros/subrubros_form.html"
    success_url = reverse_lazy("listaSubrubros")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.modificado_por = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse_lazy('listaSubrubros'))


class LineasList(TemplateView):
    template_name = "lineas/lineas_list.html"


class LineasNuevo(CreateView):
    model = Linea
    form_class = LineasForm
    template_name = "lineas/lineas_form.html"
    success_url = reverse_lazy("listaLineas")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.modificado_por = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse_lazy('listaLineas'))


class LineasModificar(UpdateView):
    model = Linea
    form_class = LineasForm
    template_name = "lineas/lineas_form.html"
    success_url = reverse_lazy("listaLineas")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.modificado_por = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse_lazy('listaLineas'))


class ArticulosList(TemplateView):
    template_name = "articulos/articulos_list.html"

    def dispatch(self, request, *args, **kwargs):
        hit = FunctionHit.objects.get(usuario=self.request.user, funcion="ARTIC")
        hit.hit += 1
        hit.save()
        return super(ArticulosList, self).dispatch(request, *args, **kwargs)


class ArticulosNuevo(CreateView):
    model = Articulo
    form_class = ArticulosForm
    template_name = "articulos/articulos_form.html"
    success_url = reverse_lazy("listaArticulos")

    def form_valid(self, form):
        art = form.save(commit=False)
        art.modificado_por = self.request.user
        art.ultima_actualizacion_precio = timezone_today()
        art.save()
        return HttpResponseRedirect(self.success_url)


class ArticulosModificar(UpdateView):
    model = Articulo
    form_class = ArticulosForm
    template_name = "articulos/articulos_form.html"
    success_url = reverse_lazy("listaArticulos")


def articulosSuspender(request, pk):
    articulo = Articulo.objects.get(pk=pk)
    articulo.suspendido = True
    articulo.save()
    return HttpResponseRedirect(reverse_lazy('listaArticulos'))


def articulosHabilitar(request, pk):
    articulo = Articulo.objects.get(pk=pk)
    articulo.suspendido = False
    articulo.save()
    return HttpResponseRedirect(reverse_lazy('listaArticulos'))


class CondicionesVentaList(TemplateView):
    template_name = "condiciones_venta/condiciones_venta_list.html"

    def dispatch(self, request, *args, **kwargs):
        hit = FunctionHit.objects.get(usuario=self.request.user, funcion="CONDV")
        hit.hit += 1
        hit.save()
        return super(CondicionesVentaList, self).dispatch(request, *args, **kwargs)


class CondicionesVentaNuevo(CreateView):
    model = Condicion_venta
    form_class = CondicionesVentaForm
    template_name = "condiciones_venta/condiciones_venta_form.html"
    success_url = reverse_lazy("listaCondicionesLinea")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.modificado_por = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse_lazy('listaCondicionesVenta'))


class CondicionesVentaModificar(UpdateView):
    model = Condicion_venta
    form_class = CondicionesVentaForm
    template_name = "condiciones_venta/condiciones_venta_form.html"
    success_url = reverse_lazy("listaCondicionesVenta")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.modificado_por = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse_lazy('listaCondicionesVenta'))


class ClientesList(TemplateView):
    template_name = "clientes/clientes_list.html"


class ClientesNuevo(CreateView):
    model = Cliente
    form_class = ClientesForm
    template_name = "clientes/clientes_form.html"
    success_url = reverse_lazy("listaClientes")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.modificado_por = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse_lazy('listaClientes'))


class ClientesModificar(UpdateView):
    model = Cliente
    form_class = ClientesForm
    template_name = "clientes/clientes_form.html"
    success_url = reverse_lazy("listaClientes")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.modificado_por = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse_lazy('listaClientes'))


def clientesSuspender(request, pk):
    cliente = Cliente.objects.get(pk=pk)
    cliente.suspendido = True
    cliente.save()
    return HttpResponseRedirect(reverse_lazy('listaClientes'))


def clientesHabilitar(request, pk):
    cliente = Cliente.objects.get(pk=pk)
    cliente.suspendido = False
    cliente.save()
    return HttpResponseRedirect(reverse_lazy('listaClientes'))


class VentasList(TemplateView):
    template_name = "ventas/ventas_list.html"


def vender(request):
    formsets_compuestos = {}
    if request.method == 'POST':  # If the form has been submitted...
        # Paso todos los campos en POST de cantidad que esten en tiempo a decimal
        CPOST = request.POST.copy()
        for k, v in CPOST.iteritems():
            if "cantidad" in k and ":" in v:
                entero = int(CPOST[k].split(":")[0])
                decimal = float(CPOST[k].split(":")[1]) / 60
                decimal = Decimal("%.3f" % decimal)
                CPOST[k] = "%s" % (entero + decimal)
        # Instancio los form para validacion
        facturaForm = VentaForm(CPOST)
        DetalleFormset = formset_factory(ItemVenta, extra=0)
        detalleFormset = DetalleFormset(CPOST, prefix='detalle')
        detalleFormset.is_valid()
        CompuestoFormset = formset_factory(ItemArticuloCompuesto, extra=0)
        all_formsets_compuestos_valid = True
        for i, detalleItem in enumerate(detalleFormset):
            if detalleItem.cleaned_data['tipo'] == 'AC':
                formsets_compuestos[i] = CompuestoFormset(CPOST, prefix='compuesto-' + str(i))
                all_formsets_compuestos_valid = all_formsets_compuestos_valid and formsets_compuestos[i].is_valid()
        if facturaForm.is_valid() and detalleFormset.is_valid() and all_formsets_compuestos_valid:
            factura = facturaForm.save(commit=False)
            periodo = Periodo.objects.filter(mes=factura.fecha.month, ano=factura.fecha.year)[0]
            factura.periodo = periodo
            if factura.descuento is None:
                factura.descuento = 0
            if not ES_MONOTRIBUTO:
                if factura.cliente.cond_iva == "RI":
                    factura.tipo = facturaForm.cleaned_data['tipoDisplay'] + "A"
                else:
                    factura.tipo = facturaForm.cleaned_data['tipoDisplay'] + "B"
            else:
                factura.tipo = facturaForm.cleaned_data['tipoDisplay'] + "C"
            # FIN PROCESO EN FACTURA, FALTAN LOS TOTALES
            factura.save()
            for i, detalleItem in enumerate(detalleFormset.forms):
                if detalleItem.cleaned_data['descuento'] is None:
                    detalleItem.cleaned_data['descuento'] = 0
                if detalleItem.cleaned_data['tipo'] == 'AA':
                    # ARTICULO ALMACENADO
                    item = Item_almacenados(venta=factura,
                                            cantidad=detalleItem.cleaned_data['cantidad'],
                                            articulo=detalleItem.cleaned_data['articulo_almacenado'],
                                            descuento=detalleItem.cleaned_data['descuento'],
                                            renglon=i)
                    item.save()
                elif detalleItem.cleaned_data['tipo'] == 'AP':
                    item = Item_personalizados(venta=factura,
                                               descripcion=detalleItem.cleaned_data['descripcion'],
                                               cantidad=detalleItem.cleaned_data['cantidad'],
                                               linea=detalleItem.cleaned_data['linea'],
                                               iva=detalleItem.cleaned_data['iva'],
                                               precio_unitario=detalleItem.cleaned_data['precio_unitario'],
                                               descuento=detalleItem.cleaned_data['descuento'],
                                               renglon=i)
                    item.save()
                elif detalleItem.cleaned_data['tipo'] == 'AC':
                    item = Item_compuesto(venta=factura,
                                          descripcion=detalleItem.cleaned_data['descripcion'],
                                          cantidad=detalleItem.cleaned_data['cantidad'],
                                          linea=detalleItem.cleaned_data['linea'],
                                          iva=detalleItem.cleaned_data['iva'],
                                          descuento=detalleItem.cleaned_data['descuento'],
                                          renglon=i)
                    item.save()
                    # Busco los compuestos
                    compuestoFormset = formsets_compuestos[i]
                    for compuesto in compuestoFormset.forms:
                        if compuesto.cleaned_data['pers']:
                            item_c = Item_compuesto_personalizado(item_compuesto=item,
                                                                  descripcion=compuesto.cleaned_data[
                                                                      'descripcion'],
                                                                  cantidad=compuesto.cleaned_data['cantidad'],
                                                                  precio_unitario=compuesto.cleaned_data[
                                                                      'precio_unitario'])
                            item_c.save()
                        else:
                            item_c = Item_compuesto_almacenado(item_compuesto=item,
                                                               cantidad=compuesto.cleaned_data['cantidad'],
                                                               articulo=compuesto.cleaned_data[
                                                                   'articulo_almacenado'])
                            item_c.save()
            subtotal = neto = Decimal("0")
            iva = {'IVA00': Decimal("0"), 'IV105': Decimal("0"), 'IVA21': Decimal("0"), 'IVA27': Decimal("0")}
            for item_a in factura.almacenado_venta.all():
                subtotal += item_a.subtotal()
                neto += item_a.neto()
                iva[item_a.articulo.iva] += item_a.iva_value()
            for item_p in factura.personalizado_venta.all():
                subtotal += item_p.subtotal()
                neto += item_p.neto()
                iva[item_p.iva] += item_p.iva_value()
            for item_c in factura.compuesto_venta.all():
                subtotal += item_c.subtotal()
                neto += item_c.neto()
                iva[item_c.iva] += item_c.iva_value()
            factura.subtotal = subtotal - (subtotal * factura.descuento / Decimal(100))
            factura.neto = neto - (neto * factura.descuento / Decimal(100))
            factura.iva21 = iva['IVA21'] - (iva['IVA21'] * factura.descuento / Decimal(100))
            factura.iva27 = iva['IVA27'] - (iva['IVA27'] * factura.descuento / Decimal(100))
            factura.iva105 = iva['IV105'] - (iva['IV105'] * factura.descuento / Decimal(100))
            factura.total = factura.saldo = factura.neto + factura.iva21 + factura.iva105 + factura.iva27
            factura.save()
            if factura.tipo.startswith("FA") or factura.tipo.startswith("ND"):
                saldo_temp = factura.saldo
                if factura.cliente.saldo < 0:  # Esto significa que hay NC con saldos a descontar
                    otros_comp = Venta.objects.filter(Q(cliente=factura.cliente), Q(tipo__startswith="NC"),
                                                      ~Q(saldo=0)).order_by('fecha', 'numero')
                    if otros_comp:
                        for comp in otros_comp:
                            if factura.saldo == 0:
                                break
                            if factura.saldo >= comp.saldo:
                                factura.saldo -= comp.saldo
                                comp.saldo = 0
                                comp.save()
                            else:
                                comp.saldo -= factura.saldo
                                factura.saldo = 0
                                comp.save()
                factura.cliente.saldo += saldo_temp
            if factura.tipo.startswith("NC"):
                saldo_temp = factura.saldo
                factura.pagado = True
                # if factura.comprobante_relacionado.total - Decimal(
                #         '0.009') < factura.total < factura.comprobante_relacionado.total + Decimal('0.009'):
                #     factura.comprobante_relacionado.pagado = True
                #     factura.comprobante_relacionado.save()
                # Resto de los saldos de otros comprobantes
                if factura.cliente.saldo > 0:  # Esto significa que hay FA o ND con saldos a descontar
                    otros_comp = Venta.objects.filter(Q(cliente=factura.cliente),
                                                      Q(tipo__startswith="FA") | Q(tipo__startswith="ND"),
                                                      ~Q(saldo=0)).order_by('fecha', 'numero')
                    if otros_comp:
                        for comp in otros_comp:
                            if factura.saldo == 0:
                                break
                            if factura.saldo >= comp.saldo:
                                factura.saldo -= comp.saldo
                                comp.saldo = 0
                                comp.pagado = True
                                comp.save()
                            else:
                                comp.saldo -= factura.saldo
                                factura.saldo = 0
                                comp.save()
                factura.cliente.saldo -= saldo_temp
                factura.save()
                factura.cliente.save()
                # factura.comprobante_relacionado.save()

            if not USA_FACTURA_ELECTRONICA:
                factura.aprobado = True
                factura.punto_venta = utils.get_pto_vta(factura)
                factura.numero = utils.get_num_comp(factura)
                factura.save()
            # return HttpResponseRedirect(reverse_lazy('nuevaVenta'))
            contado = Condicion_venta.objects.get(pk=1)
            if factura.condicion_venta == contado:
                data = {'pk': factura.pk, 'redirect': reverse('nuevoReciboContado', args=[factura.pk])}
            else:
                data = {'pk': factura.pk, 'redirect': reverse('nuevaVenta')}
            return JsonResponse(data)

    else:
        facturaForm = VentaForm()
        DetalleFormset = formset_factory(ItemVenta)
        detalleFormset = DetalleFormset(prefix='detalle')
        CompuestoFormset = formset_factory(ItemArticuloCompuesto, extra=0)
        formsets_compuestos[0] = CompuestoFormset(prefix='compuesto-0')
    # comp_forms_array=[]
    # for key,value in formsets_compuestos.iteritems():
    #     comp_forms_array.append(value)
    c = {'usa_factura_electronica': USA_FACTURA_ELECTRONICA,
         'ventaForm': facturaForm,
         'detalleFormset': detalleFormset,
         'formsets_compuestos': formsets_compuestos
         }

    c.update(csrf(request))

    return render_to_response('ventas/ventas_form.html', c)


# TODO: terminar esta funcion para la proxima version
# def modificarVenta(request, pk):
#     if request.method == 'POST':  # If the form has been submitted...
#         Paso todos los campos en POST de cantidad que esten en tiempo a decimal
# CPOST = request.POST.copy()
# for k, v in CPOST.iteritems():
#     if "cantidad" in k and ":" in v:
#         entero = int(CPOST[k].split(":")[0])
#         decimal = float(CPOST[k].split(":")[1]) / 60
#         decimal = Decimal("%.3f" % decimal)
#         CPOST[k] = "%s" % (entero + decimal)
# venta_a_modificar = Venta.objects.get(pk=pk)
# articuloCompuestoFormset = iEditarArticuloCompuestoFormset(CPOST, prefix='art_comp')
# facturaForm = VentaForm(CPOST, instance=venta_a_modificar)
# detalleFormset = NuevoDetalleFormset(CPOST, prefix='det_venta')
# i = 0
# dict_formsets_ac = {}
# for detalle in venta_a_modificar.detalle_venta_set.all().order_by('pk'):
#     if detalle.tipo_articulo == 'AC':
#         dict_formsets_ac[i] = iEditarArticuloCompuestoFormset(CPOST, prefix='art_comp-' + str(i),
#                                                               instance=detalle)
#     i += 1
# if facturaForm.is_valid() and detalleFormset.is_valid() and articuloCompuestoFormset.is_valid():
#     factura = facturaForm.save(commit=False)
#     periodo = Periodo.objects.filter(mes=factura.fecha.month, ano=factura.fecha.year)[0]
#     factura.periodo = periodo
#     if not ES_MONOTRIBUTO:
#         if factura.cliente.cond_iva == "RI":
#             factura.tipo = facturaForm.cleaned_data['tipoDisplay'] + "A"
#         else:
#             factura.tipo = facturaForm.cleaned_data['tipoDisplay'] + "B"
#     else:
#         factura.tipo = facturaForm.cleaned_data['tipoDisplay'] + "C"
#     factura.save()
#     subtotal = 0
#     for form in detalleFormset.forms:
#         detalleItem = form.save(commit=False)
#         if factura.tipo.endswith('A') or factura.tipo.endswith('C'):
#             sub = detalleItem.cantidad * detalleItem.precio_unitario
#             subtotal += sub - (sub * detalleItem.descuento / Decimal(100))
#         elif factura.tipo.endswith('B'):
#             sub = detalleItem.cantidad * (detalleItem.precio_unitario / Decimal(1.21))
#             subtotal += sub - (sub * detalleItem.descuento / Decimal(100))
#     factura.subtotal = subtotal
#     factura.neto = subtotal - (subtotal * factura.descuento / Decimal(100))
#     factura.iva21 = 0 if factura.tipo.endswith('C') else factura.neto * Decimal("0.21")
#     factura.iva105 = 0
#     factura.total = factura.saldo = factura.neto + factura.iva21
#     factura.save()
# set_trace()
# if factura.tipo.startswith("FA") or factura.tipo.startswith("ND"):
#     saldo_temp = factura.saldo
#     if factura.cliente.saldo < 0:  # Esto significa que hay NC con saldos a descontar
#         otros_comp = Venta.objects.filter(Q(cliente=factura.cliente), Q(tipo__startswith="NC"),
#                                           ~Q(saldo=0)).order_by('fecha', 'numero')
#         if otros_comp:
#             for k, comp in otros_comp.iteritems():
#                 if factura.saldo == 0:
#                     break
#                 if factura.saldo >= comp.saldo:
#                     factura.saldo -= comp.saldo
#                     comp.saldo = 0
#                     comp.save()
#                 else:
#                     comp.saldo -= factura.saldo
#                     factura.saldo = 0
#                     comp.save()
#     factura.save()
#     factura.cliente.saldo += saldo_temp
#     factura.cliente.save()
# if factura.tipo.startswith("NC"):
#     saldo_temp = factura.saldo
#     factura.pagado = True
#     if factura.comprobante_relacionado.total - Decimal(
#             '0.009') < factura.total < factura.comprobante_relacionado.total + Decimal('0.009'):
#         factura.comprobante_relacionado.pagado = True
#         factura.comprobante_relacionado.save()
# Resto de los saldos de otros comprobantes
# if factura.cliente.saldo > 0:  # Esto significa que hay FA o ND con saldos a descontar
#     otros_comp = Venta.objects.filter(Q(cliente=factura.cliente),
#                                       Q(tipo__startswith="FA") | Q(tipo__startswith="ND"),
#                                       ~Q(saldo=0)).order_by('fecha', 'numero')
#     if otros_comp:
#         for k, comp in otros_comp.iteritems():
#             if factura.saldo == 0:
#                 break
#             if factura.saldo >= comp.saldo:
#                 factura.saldo -= comp.saldo
#                 comp.saldo = 0
#                 comp.pagado = True
#                 comp.save()
#             else:
#                 comp.saldo -= factura.saldo
#                 factura.saldo = 0
#                 comp.save()
# factura.save()
# factura.cliente.saldo -= saldo_temp
# factura.cliente.save()
# factura.comprobante_relacionado.save()
# dict_forms = {}
# i = 0
# for form in detalleFormset.forms:
#     detalleItem = form.save(commit=False)
#     if factura.tipo.endswith('B'):
#         detalleItem.precio_unitario = detalleItem.precio_unitario / Decimal(1.21)
#     detalleItem.venta = factura
#     if detalleItem.tipo_articulo == "AA":
#         detalleItem.articulo_personalizado = ""
#         detalleItem.linea_articulo_personalizado = None
#     else:
#         detalleItem.articulo = None
#     detalleItem.save()
#     dict_forms[i] = detalleItem
#     i += 1
# for form in articuloCompuestoFormset.forms:
#     if len(form.cleaned_data) > 0:
#         id_deta = form.cleaned_data['id_detalle_venta']
#         articuloCompuesto = form.save(commit=False)
# Si es factura B, quito el iva.
# articuloCompuesto.detalle_venta = dict_forms[int(id_deta)]
# articuloCompuesto.precio_unitario = articuloCompuesto.precio_unitario / Decimal('1.21') if \
#     articuloCompuesto.detalle_venta.venta.tipo[-1:] == 'B' else articuloCompuesto.precio_unitario
# articuloCompuesto.descuento = dict_forms[int(id_deta)].descuento
# articuloCompuesto.save()
# if not USA_FACTURA_ELECTRONICA:
#     factura.aprobado = True
#     factura.punto_venta = utils.get_pto_vta(factura)
#     factura.numero = utils.get_num_comp(factura)
#     factura.save()
# return HttpResponseRedirect(reverse_lazy('nuevaVenta'))
#
# else:
#     obj_venta = Venta.objects.get(pk=pk)
#     facturaForm = VentaForm(instance=obj_venta, initial={'clienteDisplay': obj_venta.cliente.razon_social,
#                                                          'tipoDisplay': obj_venta.tipo[0:2]})
#     initial_detalle = []
#     initial_compuestos = []
#     detalles = Detalle_venta.objects.filter(venta=obj_venta)
#     i = 0
#     for det in detalles:
#         dict_det = {}
#         for field in Detalle_venta._meta.get_fields():
#             if field.name != "venta" and not field.one_to_many and not field.primary_key:
#                 dict_det[field.name] = getattr(det, field.name)
#         if det.tipo_articulo == 'AA':
#             denominacion_articulo = det.articulo.denominacion_ampliada()
#             dict_det['denominacion_articulo_ro'] = denominacion_articulo
#         elif det.tipo_articulo == 'AC':
#             componer_articulo = det.articulo_personalizado
#             dict_det['componer_articulo_ro'] = componer_articulo
#         initial_detalle.append(dict_det)
#         compuestos = DetalleArticuloCompuesto.objects.filter(detalle_venta=det)
#         if compuestos:
#             for compuesto in compuestos:
#                 dict_comp = {}
#                 for field in DetalleArticuloCompuesto._meta.get_fields():
#                     if not field.primary_key and (
#                                     field.name != "detalle_venta" or field.name != "descuento") and not field.one_to_many:
#                         dict_comp[field.name] = getattr(compuesto, field.name)
#                 dict_comp['id_detalle_venta'] = i
#                 if not compuesto.pers:
#                     dict_comp["denominacion_articulo_ro"] = compuesto.articulo.denominacion_ampliada()
#                 initial_compuestos.append(dict_comp)
#         i += 1
#
#     print initial_detalle
#     print initial_compuestos
#
#     detalleFormset = iEditarDetalleFormset(prefix='det_venta', instance=obj_venta)
# articuloCompuestoFormset = EditarArticuloCompuestoFormset(prefix='art_comp', initial=initial_compuestos)
# For CSRF protection
# See http://docs.djangoproject.com/en/dev/ref/contrib/csrf/
# set_trace()
# c = {'usa_factura_electronica': USA_FACTURA_ELECTRONICA,
#      'ventaForm': facturaForm,
#      'detalleFormset': detalleFormset,
# 'articuloCompuestoFormset': articuloCompuestoFormset,
# }
# c.update(csrf(request))
#
# return render_to_response('ventas/ventas_form.html', c)


class VentaDelete(DeleteView):
    model = Venta
    success_url = reverse_lazy('listaVentas')
    template_name = "ventas/ventas_delete.html"


def afip_aprob(request, pk):
    venta = Venta.objects.get(pk=pk)
    if venta.aprobado:
        err = ['Este comprobante ya ha sido aprobado.']
        print "Len de err: " + str(len(err))
        return render_to_response('ventas/rechazado.html', {'err': err})

    tc = utils.get_tipo_comp_afip(venta)
    pv = str(utils.get_pto_vta(venta))
    cd = ch = utils.get_num_comp(venta)
    fec = venta.fecha.strftime('%Y%m%d')
    imt = "%.2f" % venta.total
    imn = "%.2f" % venta.neto
    imi = "%.2f" % (venta.iva105 + venta.iva21 + venta.iva27)
    fact = WSFEv1(produccion=not DEBUG)##Ruso:: Crear settoeken, sign, y cuit
    if venta.cliente.cuit:
        if venta.cliente.cuit == '00-00000000-0':
            tdoc = 99
            ndo = 0
        else:
            tdoc = 80
            ndo = venta.cliente.cuit.replace('-', '')
    elif venta.cliente.dni:
        tdoc = 96
        ndo = venta.cliente.dni
    else:
        tdoc = 99
        ndo = 0
    fact.CrearFactura(concepto=1, tipo_doc=tdoc, nro_doc=ndo, tipo_cbte=tc,
                      punto_vta=pv, cbt_desde=cd, cbt_hasta=ch, imp_total=imt,
                      imp_tot_conc=0.00, imp_neto=imn, imp_iva=imi,
                      fecha_cbte=fec, fecha_venc_pago="", fecha_serv_hasta=None,
                      moneda_id="PES", moneda_ctz="1.0000")
    codigo_iva = {'IVA00': 3, 'IV105': 4, 'IVA21': 5, 'IVA27': 6}
    iva21 = "%.2f" % venta.iva21
    iv105 = "%.2f" % venta.iva105
    iva27 = "%.2f" % venta.iva27
    if venta.iva105 > Decimal("0"):
        fact.AgregarIva(4, round(venta.iva105 / Decimal("0.105"), 2), venta.iva105)
    if venta.iva21 > Decimal("0"):
        fact.AgregarIva(5, round(venta.iva21 / Decimal("0.21"), 2), venta.iva21)
    if venta.iva27 > Decimal("0"):
        fact.AgregarIva(6, round(venta.iva27 / Decimal("0.27"),2 ), venta.iva27)
    # fact.SetParametros(cuit="20149443984", token=token, sign=sign)
    # Asociar comprobantes!! 
    # if venta.comprobante_relacionado:
    #     tcca = utils.get_tipo_comp_afip(venta.comprobante_relacionado)
    #     pvca = str(utils.get_pto_vta(venta.comprobante_relacionado))
    #     fact.agregarCmpAsoc(tcca, pvca, venta.comprobante_relacionado.numero)
    # fact.Conectar(wsdl=WSFEV1)
    # print fact.CompUltimoAutorizado(3, 3)
    fact.Conectar()
    if fact.CAESolicitar():
        cae = fact.CAE
        cae_venc = fact.Vencimiento
        venta.punto_venta = utils.get_pto_vta(venta)
        venta.numero = utils.get_num_comp(venta)
        venta.aprobado = True
        venta.cae = cae
        venta.fvto_cae = datetime.strptime(cae_venc, "%Y%m%d").date()
        venta.save()
        obs = fact.Observaciones if fact.Observaciones else None
        return JsonResponse({'result': 'OK',
                             'obs': obs,
                             'err': None,
                             'cae': cae,
                             'venc': venta.fvto_cae.strftime("%d/%m/%Y")})
    else:
        obs = fact.Observaciones if fact.Observaciones else None
        err = fact.Errores if fact.Errores else None
        return JsonResponse({'result': 'ER',
                             'obs': obs,
                             'err': err,
                             'cae': None,
                             'venc': None})


def subdiario_iva_ventas(request):
    if request.method == 'POST':
        subdiario = SubdiarioIVAVentPeriodoFecha(request.POST)
        if subdiario.is_valid():
            per = subdiario.cleaned_data['periodo']
            fd = subdiario.cleaned_data['fecha_desde']
            fh = subdiario.cleaned_data['fecha_hasta']
            fi = subdiario.cleaned_data['folio_inicial']
            resp = HttpResponse(content_type='application/pdf')
            if per:
                ventas = Venta.objects.filter(periodo=per, aprobado=True).order_by('fecha', 'tipo', 'numero')
                # set_trace()
                # ivav = IVAVentas(queryset=ventas,periodo=per,folio_inicial=fi)
                ivav = IVAVentas(queryset=ventas, fpn=fi)
                # ivav.first_page_number = fi
                ivav.generate_by(PDFGenerator, filename=resp, variables={'periodo': per.periodo_full})
                return resp
            else:
                if fh and fd:
                    ventas = Venta.objects.filter(fecha__range=(fd, fh), aprobado=True).order_by('fecha', 'tipo',
                                                                                                 'numero')
                    ivav = IVAVentas(queryset=ventas, fpn=fi)
                    ivav.generate_by(PDFGenerator, filename=resp, variables={'periodo': 'N/A'})
                    return resp
    else:
        subdiario = SubdiarioIVAVentPeriodoFecha()

    # For CSRF protection
    # See http://docs.djangoproject.com/en/dev/ref/contrib/csrf/ 
    c = {'subdiario': subdiario,
         }
    c.update(csrf(request))

    return render_to_response('ventas/subdiario_iva_ventas.html', c)


class CobrosList(TemplateView):
    template_name = "cobros/cobros_list.html"


class CobroNew(View):
    class RequiredFormSet(BaseFormSet):
        def __init__(self, *args, **kwargs):
            super(BaseFormSet, self).__init__(*args, **kwargs)
            for form in self.forms:
                form.empty_permitted = False

    def get(self, request):
        reciboForm = ReciboForm()
        DetalleCobroFormset = formset_factory(DetalleCobroForm, extra=0)
        detalleCobroFormset = DetalleCobroFormset(prefix='cobros')
        ValoresFormset = formset_factory(ValoresReciboForm, extra=1)
        valoresFormset = ValoresFormset(prefix='valores')

        c = {'reciboForm': reciboForm,
             'cobroFormset': detalleCobroFormset,
             'valoresFormset': valoresFormset,
             }
        c.update(csrf(request))

        return render_to_response('cobros/cobros_form.html', c)

    def post(self, request):
        reciboForm = ReciboForm(request.POST)  # A form bound to the POST data
        # Create a formset from the submitted data
        DetalleCobroFormset = formset_factory(DetalleCobroForm, extra=0)
        detalleCobroFormset = DetalleCobroFormset(request.POST, prefix='cobros')
        ValoresFormset = formset_factory(ValoresReciboForm, extra=0)
        valoresFormset = ValoresFormset(request.POST, prefix='valores')
        if reciboForm.is_valid() and detalleCobroFormset.is_valid() and valoresFormset.is_valid():
            # Inicializo variables de trabajo
            total_comprobantes = 0  # Suma de comprobantes cancelados, se usa en para calculo de credito a favor o vuelto
            for detalle_cobro in detalleCobroFormset.forms:
                if detalle_cobro.cleaned_data['pagar'] and Decimal(detalle_cobro.cleaned_data['pagar']) > 0:
                    total_comprobantes += detalle_cobro.cleaned_data['pagar']
            recibo = reciboForm.save(commit=False)
            saldo_cliente = recibo.cliente.saldo  # Si el saldo es negativo, es porque tiene un cheque con saldo a favor del cliente
            try:
                cheq = Dinero.objects.filter(Q(recibo__cliente=recibo.cliente), ~Q(pendiente_para_recibo=0))[0]
                if total_comprobantes > cheq.pendiente_para_recibo:
                    cred_ant = cheq.pendiente_para_recibo
                    cheq.pendiente_para_recibo = 0
                    a_cta = 0
                else:
                    cred_ant = cheq.pendiente_para_recibo
                    a_cta = total_comprobantes - cred_ant
                cheq.save()
            except IndexError:
                cred_ant = 0
                a_cta = 0
                pass
            list_recibo = Recibo.objects.all().order_by('-numero')
            if len(list_recibo) != 0:
                recibo.numero = list_recibo[0].numero + 1
            else:
                recibo.numero = 1
            recibo.credito_anterior = cred_ant
            recibo.a_cuenta = a_cta
            recibo.save()
            '''
            Para cada uno de los detalles de cobro ingresados, creo el registro y verifico si el comprobante esta
            pagado, para ello busco todos los detalles de este comprobante y los sumo.
            '''
            for detalle_cobro in detalleCobroFormset.forms:
                if detalle_cobro.cleaned_data['pagar'] and Decimal(detalle_cobro.cleaned_data['pagar']) > 0:
                    ve = Venta.objects.get(pk=detalle_cobro.cleaned_data['id_factura'])
                    Detalle_cobro.objects.create(recibo=recibo, venta=ve, monto=detalle_cobro.cleaned_data['pagar'])
                    # Ya estan creados todos detalle de cobro de esta factura. Reviso si la factura esta completamente pagada.
                    ve.saldo -= detalle_cobro.cleaned_data['pagar']
                    ve.save()
                    if ve.saldo == 0:
                        ve.pagado = True
                        ve.save()

            total_comp = total_comprobantes
            recibo.cliente.saldo -= total_comp
            recibo.cliente.save()
            total_val = 0
            for valor in valoresFormset.forms:
                total_val += valor.cleaned_data['monto']
                if valor.cleaned_data['monto'] <= total_comprobantes - cred_ant:
                    total_comprobantes -= valor.cleaned_data['monto']
                    if valor.cleaned_data['tipo'] == 'CHT':
                        ChequeTercero.objects.create(recibo=recibo,
                                                     numero=valor.cleaned_data['cheque_numero'],
                                                     fecha=valor.cleaned_data['cheque_fecha'],
                                                     cobro=valor.cleaned_data['cheque_cobro'],
                                                     paguese_a=valor.cleaned_data['cheque_paguese_a'],
                                                     titular=valor.cleaned_data['cheque_titular'],
                                                     cuit_titular=valor.cleaned_data['cheque_cuit_titular'],
                                                     banco=valor.cleaned_data['cheque_banco'],
                                                     en_cartera=True,
                                                     domicilio_de_pago=valor.cleaned_data['cheque_domicilio_de_pago'],
                                                     pendiente_para_recibo=0,
                                                     pendiente_para_orden_pago=0,
                                                     monto=valor.cleaned_data['monto'])
                    elif valor.cleaned_data['tipo'] == 'EFE':
                        Dinero.objects.create(monto=valor.cleaned_data['monto'], recibo=recibo,
                                              pendiente_para_recibo=0,
                                              pendiente_para_orden_pago=0)
                    elif valor.cleaned_data['tipo'] == 'TRB':
                        TransferenciaBancariaEntrante.objects.create(recibo=recibo,
                                                                     banco_origen=valor.cleaned_data[
                                                                         'transferencia_banco_origen'],
                                                                     cuenta_origen=valor.cleaned_data[
                                                                         'transferencia_cuenta_origen'],
                                                                     numero_operacion=valor.cleaned_data[
                                                                         'transferencia_numero_operacion'],
                                                                     cuenta_destino=valor.cleaned_data[
                                                                         'transferencia_cuenta_destino'],
                                                                     monto=valor.cleaned_data['monto'],
                                                                     pendiente_para_recibo=0,
                                                                     pendiente_para_orden_pago=0)
                else:
                    total_comprobantes -= cred_ant
                    if reciboForm.cleaned_data['que_hago_con_diferencia'] == 'vuelto':
                        if valor.cleaned_data['tipo'] == 'CHT':
                            ChequeTercero.objects.create(recibo=recibo,
                                                         numero=valor.cleaned_data['cheque_numero'],
                                                         fecha=valor.cleaned_data['cheque_fecha'],
                                                         cobro=valor.cleaned_data['cheque_cobro'],
                                                         paguese_a=valor.cleaned_data['cheque_paguese_a'],
                                                         titular=valor.cleaned_data['cheque_titular'],
                                                         cuit_titular=valor.cleaned_data['cheque_cuit_titular'],
                                                         banco=valor.cleaned_data['cheque_banco'],
                                                         en_cartera=True,
                                                         domicilio_de_pago=valor.cleaned_data[
                                                             'cheque_domicilio_de_pago'],
                                                         pendiente_para_recibo=0,
                                                         pendiente_para_orden_pago=0,
                                                         monto=valor.cleaned_data['monto'])
                        elif valor.cleaned_data['tipo'] == 'EFE':
                            Dinero.objects.create(monto=valor.cleaned_data['monto'], recibo=recibo,
                                                  pendiente_para_recibo=0,
                                                  pendiente_para_orden_pago=0)
                        elif valor.cleaned_data['tipo'] == 'TRB':
                            TransferenciaBancariaEntrante.objects.create(recibo=recibo, \
                                                                         banco_origen=valor.cleaned_data[
                                                                             'transferencia_banco_origen'],
                                                                         cuenta_origen=valor.cleaned_data[
                                                                             'transferencia_cuenta_origen'],
                                                                         numero_operacion=valor.cleaned_data[
                                                                             'transferencia_numero_operacion'],
                                                                         cuenta_destino=valor.cleaned_data[
                                                                             'transferencia_cuenta_destino'],
                                                                         monto=valor.cleaned_data['monto'],
                                                                         pendiente_para_recibo=0,
                                                                         pendiente_para_orden_pago=0)
                        Dinero.objects.create(recibo=recibo,
                                              monto=(valor.cleaned_data['monto'] - total_comprobantes) * -1)
                    elif reciboForm.cleaned_data['que_hago_con_diferencia'] == 'credito':
                        if valor.cleaned_data['tipo'] == 'CHT':
                            ChequeTercero.objects.create(recibo=recibo,
                                                         numero=valor.cleaned_data['cheque_numero'],
                                                         fecha=valor.cleaned_data['cheque_fecha'],
                                                         cobro=valor.cleaned_data['cheque_cobro'],
                                                         paguese_a=valor.cleaned_data['cheque_paguese_a'],
                                                         titular=valor.cleaned_data['cheque_titular'],
                                                         cuit_titular=valor.cleaned_data['cheque_cuit_titular'],
                                                         banco=valor.cleaned_data['cheque_banco'],
                                                         en_cartera=True,
                                                         domicilio_de_pago=valor.cleaned_data[
                                                             'cheque_domicilio_de_pago'],
                                                         pendiente_para_recibo=valor.cleaned_data[
                                                                                   'monto'] - total_comprobantes,
                                                         pendiente_para_orden_pago=0,
                                                         monto=valor.cleaned_data['monto'])
                        elif valor.cleaned_data['tipo'] == 'EFE':
                            Dinero.objects.create(monto=valor.cleaned_data['monto'], recibo=recibo,
                                                  pendiente_para_recibo=valor.cleaned_data[
                                                                            'monto'] - total_comprobantes,
                                                  pendiente_para_orden_pago=0)
                        elif valor.cleaned_data['tipo'] == 'TRB':
                            TransferenciaBancariaEntrante.objects.create(recibo=recibo,
                                                                         banco_origen=valor.cleaned_data[
                                                                             'transferencia_banco_origen'],
                                                                         cuenta_origen=valor.cleaned_data[
                                                                             'transferencia_cuenta_origen'],
                                                                         numero_operacion=valor.cleaned_data[
                                                                             'transferencia_numero_operacion'],
                                                                         cuenta_destino=valor.cleaned_data[
                                                                             'transferencia_cuenta_destino'],
                                                                         monto=valor.cleaned_data['monto'],
                                                                         pendiente_para_recibo=valor.cleaned_data[
                                                                                                   'monto'] - total_comprobantes,
                                                                         pendiente_para_orden_pago=0)
                        # recibo.cliente.saldo=valor.cleaned_data['monto']-total_comprobantes
                        # recibo.cliente.save()
                        recibo.a_cuenta = total_val - total_comp - cred_ant
                        recibo.save()
            obj = {'id': recibo.id}
            s = StringIO()
            json.dump(obj, s)
            s.seek(0)
            return HttpResponse(s.read())


def recibo_contado(request, venta):
    DetalleCobroFormSet = formset_factory(DetalleCobroContadoForm, extra=0)
    ValoresFormSet = formset_factory(ValoresReciboForm)
    if request.method == 'POST':  # If the form has been submitted...
        reciboForm = ReciboForm(request.POST)  # A form bound to the POST data
        # Create a formset from the submitted data
        DetalleCobroFormset = formset_factory(DetalleCobroContadoForm, extra=0)
        detalleCobroFormset = DetalleCobroFormset(request.POST, prefix='cobros')
        ValoresFormset = formset_factory(ValoresReciboForm, extra=0)
        valoresFormset = ValoresFormset(request.POST, prefix='valores')
        reciboForm.is_valid()
        detalleCobroFormset.is_valid()
        valoresFormset.is_valid()
        if reciboForm.is_valid() and detalleCobroFormset.is_valid() and valoresFormset.is_valid():
            # Inicializo variables de trabajo
            venta = Venta.objects.get(pk=detalleCobroFormset.forms[0].cleaned_data['id_factura'])
            total_comprobantes = venta.total  # Suma de comprobantes cancelados, se usa en para calculo de credito a favor o vuelto
            recibo = reciboForm.save(commit=False)
            try:
                cheq = Dinero.objects.filter(Q(recibo__cliente=recibo.cliente), ~Q(pendiente_para_recibo=0))[0]
                if total_comprobantes > cheq.pendiente_para_recibo:
                    cred_ant = cheq.pendiente_para_recibo
                    cheq.pendiente_para_recibo = 0
                    a_cta = 0
                else:
                    cred_ant = cheq.pendiente_para_recibo
                    a_cta = total_comprobantes - cred_ant
                cheq.save()
            except IndexError:
                cred_ant = 0
                a_cta = 0
                pass
            list_recibo = Recibo.objects.all().order_by('-numero')
            if len(list_recibo) != 0:
                recibo.numero = list_recibo[0].numero + 1
            else:
                recibo.numero = 1
            recibo.credito_anterior = cred_ant
            recibo.a_cuenta = a_cta
            recibo.save()
            '''
            Para cada uno de los detalles de cobro ingresados, creo el registro y verifico si el comprobante esta
            pagado, para ello busco todos los detalles de este comprobante y los sumo.
            '''
            for detalle_cobro in detalleCobroFormset.forms:
                ve = Venta.objects.get(pk=detalle_cobro.cleaned_data['id_factura'])
                Detalle_cobro.objects.create(recibo=recibo, venta=ve, monto=total_comprobantes)
                # Ya estan creados todos detalle de cobro de esta factura. Reviso si la factura esta completamente pagada.
                ve.saldo -= total_comprobantes
                ve.save()
                if ve.saldo == 0:
                    ve.pagado = True
                    ve.save()

            total_comp = total_comprobantes
            recibo.cliente.saldo -= total_comp
            recibo.cliente.save()
            total_val = 0
            for valor in valoresFormset.forms:
                total_val += valor.cleaned_data['monto']
                if valor.cleaned_data['monto'] <= total_comprobantes - cred_ant:
                    total_comprobantes -= valor.cleaned_data['monto']
                    if valor.cleaned_data['tipo'] == 'CHT':
                        ChequeTercero.objects.create(recibo=recibo,
                                                     numero=valor.cleaned_data['cheque_numero'],
                                                     fecha=valor.cleaned_data['cheque_fecha'],
                                                     cobro=valor.cleaned_data['cheque_cobro'],
                                                     paguese_a=valor.cleaned_data['cheque_paguese_a'],
                                                     titular=valor.cleaned_data['cheque_titular'],
                                                     cuit_titular=valor.cleaned_data['cheque_cuit_titular'],
                                                     banco=valor.cleaned_data['cheque_banco'],
                                                     en_cartera=True,
                                                     domicilio_de_pago=valor.cleaned_data['cheque_domicilio_de_pago'],
                                                     pendiente_para_recibo=0,
                                                     pendiente_para_orden_pago=0,
                                                     monto=valor.cleaned_data['monto'])
                    elif valor.cleaned_data['tipo'] == 'EFE':
                        Dinero.objects.create(monto=valor.cleaned_data['monto'], recibo=recibo,
                                              pendiente_para_recibo=0,
                                              pendiente_para_orden_pago=0)
                    elif valor.cleaned_data['tipo'] == 'TRB':
                        TransferenciaBancariaEntrante.objects.create(recibo=recibo,
                                                                     banco_origen=valor.cleaned_data[
                                                                         'transferencia_banco_origen'],
                                                                     cuenta_origen=valor.cleaned_data[
                                                                         'transferencia_cuenta_origen'],
                                                                     numero_operacion=valor.cleaned_data[
                                                                         'transferencia_numero_operacion'],
                                                                     cuenta_destino=valor.cleaned_data[
                                                                         'transferencia_cuenta_destino'],
                                                                     monto=valor.cleaned_data['monto'],
                                                                     pendiente_para_recibo=0,
                                                                     pendiente_para_orden_pago=0)
                else:
                    total_comprobantes -= cred_ant
                    if reciboForm.cleaned_data['que_hago_con_diferencia'] == 'vuelto':
                        if valor.cleaned_data['tipo'] == 'CHT':
                            ChequeTercero.objects.create(recibo=recibo,
                                                         numero=valor.cleaned_data['cheque_numero'],
                                                         fecha=valor.cleaned_data['cheque_fecha'],
                                                         cobro=valor.cleaned_data['cheque_cobro'],
                                                         paguese_a=valor.cleaned_data['cheque_paguese_a'],
                                                         titular=valor.cleaned_data['cheque_titular'],
                                                         cuit_titular=valor.cleaned_data['cheque_cuit_titular'],
                                                         banco=valor.cleaned_data['cheque_banco'],
                                                         en_cartera=True,
                                                         domicilio_de_pago=valor.cleaned_data[
                                                             'cheque_domicilio_de_pago'],
                                                         pendiente_para_recibo=0,
                                                         pendiente_para_orden_pago=0,
                                                         monto=valor.cleaned_data['monto'])
                        elif valor.cleaned_data['tipo'] == 'EFE':
                            Dinero.objects.create(monto=valor.cleaned_data['monto'], recibo=recibo,
                                                  pendiente_para_recibo=0,
                                                  pendiente_para_orden_pago=0)
                        elif valor.cleaned_data['tipo'] == 'TRB':
                            TransferenciaBancariaEntrante.objects.create(recibo=recibo,
                                                                         banco_origen=valor.cleaned_data[
                                                                             'transferencia_banco_origen'],
                                                                         cuenta_origen=valor.cleaned_data[
                                                                             'transferencia_cuenta_origen'],
                                                                         numero_operacion=valor.cleaned_data[
                                                                             'transferencia_numero_operacion'],
                                                                         cuenta_destino=valor.cleaned_data[
                                                                             'transferencia_cuenta_destino'],
                                                                         monto=valor.cleaned_data['monto'],
                                                                         pendiente_para_recibo=0,
                                                                         pendiente_para_orden_pago=0)
                        Dinero.objects.create(recibo=recibo,
                                              monto=(valor.cleaned_data['monto'] - total_comprobantes) * -1)
                    elif reciboForm.cleaned_data['que_hago_con_diferencia'] == 'credito':
                        if valor.cleaned_data['tipo'] == 'CHT':
                            ChequeTercero.objects.create(recibo=recibo,
                                                         numero=valor.cleaned_data['cheque_numero'],
                                                         fecha=valor.cleaned_data['cheque_fecha'],
                                                         cobro=valor.cleaned_data['cheque_cobro'],
                                                         paguese_a=valor.cleaned_data['cheque_paguese_a'],
                                                         titular=valor.cleaned_data['cheque_titular'],
                                                         cuit_titular=valor.cleaned_data['cheque_cuit_titular'],
                                                         banco=valor.cleaned_data['cheque_banco'],
                                                         en_cartera=True,
                                                         domicilio_de_pago=valor.cleaned_data[
                                                             'cheque_domicilio_de_pago'],
                                                         pendiente_para_recibo=valor.cleaned_data[
                                                                                   'monto'] - total_comprobantes,
                                                         pendiente_para_orden_pago=0,
                                                         monto=valor.cleaned_data['monto'])
                        elif valor.cleaned_data['tipo'] == 'EFE':
                            Dinero.objects.create(monto=valor.cleaned_data['monto'], recibo=recibo,
                                                  pendiente_para_recibo=valor.cleaned_data[
                                                                            'monto'] - total_comprobantes,
                                                  pendiente_para_orden_pago=0)
                        elif valor.cleaned_data['tipo'] == 'TRB':
                            TransferenciaBancariaEntrante.objects.create(recibo=recibo,
                                                                         banco_origen=valor.cleaned_data[
                                                                             'transferencia_banco_origen'],
                                                                         cuenta_origen=valor.cleaned_data[
                                                                             'transferencia_cuenta_origen'],
                                                                         numero_operacion=valor.cleaned_data[
                                                                             'transferencia_numero_operacion'],
                                                                         cuenta_destino=valor.cleaned_data[
                                                                             'transferencia_cuenta_destino'],
                                                                         monto=valor.cleaned_data['monto'],
                                                                         pendiente_para_recibo=valor.cleaned_data[
                                                                                                   'monto'] - total_comprobantes,
                                                                         pendiente_para_orden_pago=0)
                        # recibo.cliente.saldo=valor.cleaned_data['monto']-total_comprobantes
                        # recibo.cliente.save()
                        recibo.a_cuenta = total_val - total_comp - cred_ant
                        recibo.save()
            obj = {'id': recibo.id}
            s = StringIO()
            json.dump(obj, s)
            s.seek(0)
            return HttpResponse(s.read())

    else:
        venta = Venta.objects.get(pk=venta)
        reciboForm = ReciboContadoForm(initial={'cliente': venta.cliente})
        cobroFormset = DetalleCobroFormSet(prefix='cobros', initial=[{'id_factura': venta.pk, 'pagar': venta.total}])
        valoresFormset = ValoresFormSet(prefix='valores')

    # For CSRF protection
    # See http://docs.djangoproject.com/en/dev/ref/contrib/csrf/ 
    # set_trace()
    c = {'reciboForm': reciboForm,
         'cobroFormset': cobroFormset,
         'valoresFormset': valoresFormset,
         'venta': venta,
         }
    c.update(csrf(request))

    return render_to_response('cobros/cobro_contado_form.html', c)


def get_num_prox_recibo(request):
    # list_recibo = Venta.objects.filter(tipo__exact=tipo_comprobante,aprobado__exact=True).order_by('-numero')
    list_recibo = Recibo.objects.all().order_by('-numero')
    if len(list_recibo) != 0:
        return HttpResponse(list_recibo[0].numero + 1, content_type='text/plain')
    else:
        return HttpResponse(1, content_type='text/plain')


def actualizarPreciosRubro(request, rubro):
    if request.method == 'POST':
        actualizador = ActualizarPrecioRubrosForm(request.POST)
        if actualizador.is_valid():
            rub = Rubro.objects.get(pk=actualizador.cleaned_data['rubro'])
            porc = actualizador.cleaned_data['porcentaje']
            arts = Articulo.objects.filter(rubro=rub)
            for art in arts:
                nuevo_precio = art.costo_compra + (art.costo_compra * Decimal(porc) / Decimal(100))
                art.ultima_actualizacion_precio = datetime.today().date()
                art.costo_compra = nuevo_precio
                art.save()
            return HttpResponseRedirect(reverse_lazy('home'))

    else:
        actualizador = ActualizarPrecioRubrosForm(initial={'rubro': rubro})
        nombre_rubro = Rubro.objects.get(pk=rubro).nombre
    # For CSRF protection
    # See http://docs.djangoproject.com/en/dev/ref/contrib/csrf/ 
    c = {'actualizador': actualizador,
         'nombre_rubro': nombre_rubro
         }
    c.update(csrf(request))

    return render_to_response('articulos/actualizar_precio.html', c)


class ComprobantesList(TemplateView):
    template_name = "ventas/cobros_list.html"


class CobrosList(TemplateView):
    template_name = "cobros/cobros_list.html"


def ventas_totales_fecha(request):
    lineas_neto = {}
    lineas_iva = {}
    lineas_total = {}
    if request.method == 'POST':
        ventast = VentasTotalesForm(request.POST)
        if ventast.is_valid():
            fd = ventast.cleaned_data['fecha_desde']
            fh = ventast.cleaned_data['fecha_hasta']
            response = HttpResponse(mimetype='application/pdf')
            if fh and fd:
                lineas = Linea.objects.all()
                for linea in lineas:
                    lineas_neto[linea.nombre] = 0
                    lineas_iva[linea.nombre] = 0
                    lineas_total[linea.nombre] = 0
                print lineas_neto
                detalle_venta = Detalle_venta.objects.filter(venta__fecha__range=(fd, fh))
                print "CANTIDAD DE DETALLES DE VENTA: %s" % len(detalle_venta)
                id = 0
                for detalle in detalle_venta:
                    desc = detalle.venta.descuento / 100
                    print "Iteracion %s" % id

                    print "Tipo Articulo --> %s" % detalle.tipo_articulo
                    if detalle.tipo_articulo == 'AA':
                        if detalle.articulo is not None:
                            if detalle.venta.tipo.startswith("NC"):
                                print "Resto %s" % detalle.total_con_descuento_factura
                                lineas_neto[detalle.articulo.linea.nombre] -= detalle.total_con_descuento_factura
                                lineas_iva[detalle.articulo.linea.nombre] -= detalle.iva_con_descuento_factura
                            else:
                                print "Sumo %s" % detalle.total_con_descuento_factura
                                lineas_neto[detalle.articulo.linea.nombre] += detalle.total_con_descuento_factura
                                lineas_iva[detalle.articulo.linea.nombre] += detalle.iva_con_descuento_factura
                    elif detalle.tipo_articulo == 'AP':
                        if detalle.linea_articulo_personalizado is not None:
                            if detalle.venta.tipo.startswith("NC"):
                                print "Resto %s" % detalle.total_con_descuento_factura
                                lineas_neto[
                                    detalle.linea_articulo_personalizado.nombre] -= detalle.total_con_descuento_factura
                                lineas_iva[
                                    detalle.linea_articulo_personalizado.nombre] -= detalle.iva_con_descuento_factura
                            else:
                                print "Sumo %s" % detalle.total_con_descuento_factura
                                lineas_neto[
                                    detalle.linea_articulo_personalizado.nombre] += detalle.total_con_descuento_factura
                                lineas_iva[
                                    detalle.linea_articulo_personalizado.nombre] += detalle.iva_con_descuento_factura
                    elif detalle.tipo_articulo == 'AC':
                        if detalle.venta.tipo.startswith("NC"):
                            print "Resto %s" % detalle.total_con_descuento_factura
                            lineas_neto[u'Prestación de Servicios'] -= detalle.total_con_descuento_factura
                            lineas_iva[u'Prestación de Servicios'] -= detalle.iva_con_descuento_factura
                        else:
                            print "Sumo %s" % detalle.total_con_descuento_factura
                            lineas_neto[u'Prestación de Servicios'] += detalle.total_con_descuento_factura
                            lineas_iva[u'Prestación de Servicios'] += detalle.iva_con_descuento_factura
                        '''isu=0
                        cant=detalle.cantidad
                        for artcomp in detalle.detallearticulocompuesto_set.all():
                            print "    -> Subiteracion %s de %s" %(isu,len(detalle.detallearticulocompuesto_set.all()))
                            if artcomp.detalle_venta.venta.tipo.startswith("NC"):
                                if artcomp.articulo:
                                    print "Resto %s" %artcomp.total_con_descuento_factura_e_item
                                    lineas_neto[artcomp.articulo.linea.nombre]-=artcomp.total_con_descuento_factura_e_item
                                    lineas_iva[artcomp.articulo.linea.nombre]-=artcomp.iva*cant
                                elif artcomp.linea_articulo_personalizado:
                                    print "Resto %s" %(artcomp.neto*cant)
                                    lineas_neto[artcomp.linea_articulo_personalizado.nombre]-=artcomp.total_con_descuento_factura_e_item
                                    lineas_iva[artcomp.linea_articulo_personalizado.nombre]-=artcomp.iva*cant
                                else:
                                    print "Resto %s" %artcomp.total_con_descuento_factura_e_item
                                    lineas_neto[u'Prestación de Servicios']-=artcomp.neto*cant
                                    lineas_iva[u'Prestación de Servicios']-=artcomp.iva*cant
                            else:
                                if artcomp.articulo:
                                    print "Sumo %s" %artcomp.total_con_descuento_factura_e_item
                                    lineas_neto[artcomp.articulo.linea.nombre]+=artcomp.total_con_descuento_factura_e_item
                                    lineas_iva[artcomp.articulo.linea.nombre]+=artcomp.iva*cant
                                elif artcomp.linea_articulo_personalizado:
                                    print "Sumo %s" %artcomp.total_con_descuento_factura_e_item
                                    lineas_neto[artcomp.linea_articulo_personalizado.nombre]+=artcomp.total_con_descuento_factura_e_item
                                    lineas_iva[artcomp.linea_articulo_personalizado.nombre]+=artcomp.iva*cant
                                else:
                                    print "Sumo %s" %artcomp.total_con_descuento_factura_e_item
                                    lineas_neto[u'Prestación de Servicios']+=artcomp.total_con_descuento_factura_e_item
                                    lineas_iva[u'Prestación de Servicios']+=artcomp.iva*cant
                            print "B Uso        Fab        P.Serv.        Productos"
                            print "%s            %s        %s             %s"\
                            %(lineas_neto['Bienes de Uso'],lineas_neto[u'Fabricación'],lineas_neto[u'Prestación de Servicios'],lineas_neto['Productos'])
                            isu+=1'''
                        lineas_neto
                    else:
                        if detalle.venta.tipo.startswith("NC"):
                            print "Resto %s" % detalle.total_con_descuento_factura
                            lineas_neto[u'Prestación de Servicios'] -= detalle.total_con_descuento_factura
                            lineas_iva[u'Prestación de Servicios'] -= detalle.iva_con_descuento_factura
                        else:
                            print "Sumo %s" % detalle.total_con_descuento_factura
                            lineas_neto[u'Prestación de Servicios'] += detalle.total_con_descuento_factura
                            lineas_iva[u'Prestación de Servicios'] += detalle.iva_con_descuento_factura
                    print "B Uso        Fab        P.Serv.        Productos"
                    print "%s            %s        %s             %s" \
                          % (lineas_neto['Bienes de Uso'], lineas_neto[u'Fabricación'],
                             lineas_neto[u'Prestación de Servicios'], lineas_neto['Productos'])
                    id += 1
                    # print lineas_neto.values()
                # //////////VENTAS TOTALES//////////////
                response['Content-Disposition'] = 'filename="ventas_totales.pdf"'
                p = Canvas(response, pagesize=A4)
                p.setFont('Helvetica', 11)
                p.drawString(19 * cm, 28.2 * cm, datetime.today().strftime("%d/%m/%Y"))
                p.setFont('Helvetica-Bold', 15)
                p.drawString(2 * cm, 27.5 * cm, RAZON_SOCIAL_EMPRESA)
                p.drawString(7 * cm, 26.2 * cm, "VENTAS TOTALES")
                p.drawString(6 * cm, 25.5 * cm, "Desde %s hasta %s" % (
                    datetime.strftime(fd, "%d/%m/%Y"), datetime.strftime(fh, "%d/%m/%Y")))
                p.line(0, 24.8 * cm, 21 * cm, 24.8 * cm)
                p.setFont('Helvetica-Bold', 14)
                p.drawString(3 * cm, 24.2 * cm, "Linea")
                p.drawString(11 * cm, 24.2 * cm, "Neto")
                p.drawString(15 * cm, 24.2 * cm, "IVA")
                p.drawString(17.5 * cm, 24.2 * cm, "Total")
                p.line(0, 24 * cm, 21 * cm, 24 * cm)
                inicio_y = 22
                alto_item = 0.7
                i = 0
                for linea in lineas:
                    p.setFont('Helvetica', 12)
                    p.drawString(2.8 * cm, (inicio_y - alto_item * i) * cm, linea.nombre)
                    p.drawString(11 * cm, (inicio_y - alto_item * i) * cm, "%.2f" % lineas_neto[linea.nombre])
                    p.drawString(15 * cm, (inicio_y - alto_item * i) * cm, "%.2f" % lineas_iva[linea.nombre])
                    p.drawString(17.5 * cm, (inicio_y - alto_item * i) * cm,
                                 "%.2f" % (lineas_neto[linea.nombre] + lineas_iva[linea.nombre]))
                    i = i + 1
                total_neto = 0
                for v in lineas_neto.values():
                    total_neto = total_neto + v
                total_iva = 0
                for v in lineas_iva.values():
                    total_iva = total_iva + v
                p.setFont('Helvetica-Bold', 12)
                p.drawString(2.8 * cm, ((inicio_y - alto_item * i) - 0.5) * cm, "TOTAL")
                p.drawString(11 * cm, ((inicio_y - alto_item * i) - 0.5) * cm, "%.2f" % total_neto)
                p.drawString(15 * cm, ((inicio_y - alto_item * i) - 0.5) * cm, "%.2f" % total_iva)
                p.drawString(17.5 * cm, ((inicio_y - alto_item * i) - 0.5) * cm, "%.2f" % (total_neto + total_iva))
                p.showPage()
                p.save()
                return response
    else:
        ventast = VentasTotalesForm()

    # For CSRF protection
    # See http://docs.djangoproject.com/en/dev/ref/contrib/csrf/ 
    c = {'ventast': ventast,
         }
    c.update(csrf(request))

    return render_to_response('informes/ventas_totales.html', c)


def resumen_cuenta(request):
    if request.method == 'POST':
        resumen = ResumenCuentaForm(request.POST)
        if resumen.is_valid():
            lis = resumen.cleaned_data['listar']
            if lis == "UNO":
                cli = resumen.cleaned_data['cliente']
            fd = resumen.cleaned_data['desde']
            fh = resumen.cleaned_data['hasta']
            resp = HttpResponse(mimetype='application/pdf')
            # detalle=[{'id':cli.id,'razon_social':cli.razon_social,'detalle_comprobantes':[]}]
            detalle = []
            # Defino las consultas Q
            fact = Q(tipo__startswith="FA")
            nd = Q(tipo__startswith="ND")
            apr = Q(aprobado=True)
            fe = Q(fecha__range=(fd, fh))
            nc = Q(tipo__startswith="NC")
            if lis == "UNO":
                cliq = Q(cliente=cli)
                factynd = Venta.objects.filter(cliq, apr, fe, fact | nd)
                ncrs = Venta.objects.filter(cliq, apr, fe, nc)
                recibos = Recibo.objects.filter(cliq, fe)
            elif lis == "TODOS":
                factynd = Venta.objects.filter(apr, fe, fact | nd).order_by('cliente__razon_social')
                ncrs = Venta.objects.filter(apr, fe, nc)
                recibos = Recibo.objects.filter(fe)
            array_clientes = []
            for el in factynd.values():
                if not el['cliente_id'] in array_clientes:
                    array_clientes.append(el['cliente_id'])
            for cliente in array_clientes:
                deta_comp = []
                factynd_c = factynd.filter(cliente__id=cliente)
                ncrs_c = ncrs.filter(cliente__id=cliente)
                recibos_c = recibos.filter(cliente__id=cliente)
                for jorge in factynd_c:
                    deta_comp.append(
                        {'cliente_id': cliente, 'razon_social': Cliente.objects.get(id=cliente).razon_social, \
                         'fecha': jorge.fecha, 'tipo': jorge.tipo, 'numero': jorge.pto_vta_num_full, \
                         'debe': jorge.total, 'haber': Decimal("0.00"), "saldo": Decimal("0.00")})
                for jorge in ncrs_c:
                    deta_comp.append(
                        {'cliente_id': cliente, 'razon_social': Cliente.objects.get(id=cliente).razon_social, \
                         'fecha': jorge.fecha, 'tipo': jorge.tipo, 'numero': jorge.pto_vta_num_full, \
                         'debe': Decimal("0.00"), 'haber': jorge.total, "saldo": Decimal("0.00")})
                for rec in recibos_c:
                    deta_comp.append(
                        {'cliente_id': cliente, 'razon_social': Cliente.objects.get(id=cliente).razon_social, \
                         'fecha': rec.fecha, 'tipo': 'REC', 'numero': rec.numero_full, \
                         'debe': Decimal("0.00"), 'haber': rec.total, "saldo": Decimal("0.00")})
                deta_comp = sorted(deta_comp, key=itemgetter('fecha'))
                deta_comp.insert(0,
                                 {'cliente_id': cliente, 'razon_social': Cliente.objects.get(id=cliente).razon_social,
                                  'fecha': 'Saldo anterior', 'tipo': '', 'numero': '', 'debe': '', 'haber': '',
                                  'saldo': Cliente.objects.get(id=cliente).saldo_anterior(fd)})
                for i, v in enumerate(deta_comp):
                    if i == 0:
                        saldo_ant = v['saldo']
                    else:
                        if v['tipo'].startswith("FA") or v['tipo'].startswith("ND"):
                            saldo_ant += v['debe']
                            v['saldo'] = saldo_ant
                        else:
                            saldo_ant -= v['haber']
                            v['saldo'] = saldo_ant
                detalle.extend(deta_comp)
            print detalle
            resumen_cuenta = ResumenCuenta(queryset=detalle)
            # ivav.first_page_number = fi
            resumen_cuenta.generate_by(PDFGenerator, filename=resp)
            return resp
    else:
        resumen = ResumenCuentaForm()

    # For CSRF protection
    # See http://docs.djangoproject.com/en/dev/ref/contrib/csrf/ 
    c = {'resumen': resumen,
         }
    c.update(csrf(request))

    return render_to_response('informes/resumen_cuenta.html', c)


def comp_saldo(request):
    if request.method == 'POST':
        comp = ComposicionSaldoForm(request.POST)
        if comp.is_valid():
            lis = comp.cleaned_data['listar']
            tip = comp.cleaned_data['tipo']
            if lis == "UNO":
                cli = comp.cleaned_data['cliente']
            resp = HttpResponse(mimetype='application/pdf')
            # detalle=[{'id':cli.id,'razon_social':cli.razon_social,'detalle_comprobantes':[]}]
            detalle = []
            # Defino las consultas Q
            fact = Q(tipo__startswith="FA")
            nd = Q(tipo__startswith="ND")
            apr = Q(aprobado=True)
            npag = Q(pagado=False)
            if lis == "UNO":
                cliq = Q(cliente=cli)
                factynd = Venta.objects.filter(cliq, apr, npag, fact | nd)
            elif lis == "TODOS":
                factynd = Venta.objects.filter(apr, npag, fact | nd).order_by('cliente__razon_social')
            array_clientes = []
            for el in factynd.values():
                if not el['cliente_id'] in array_clientes:
                    array_clientes.append(el['cliente_id'])
            for cliente in array_clientes:
                deta_comp = []
                factynd_c = factynd.filter(cliente__id=cliente)
                saldo_t = 0
                for jorge in factynd_c:
                    saldo_t += jorge.saldo()
                    deta_comp.append(
                        {'cliente_id': cliente, 'razon_social': Cliente.objects.get(id=cliente).razon_social, \
                         'fecha': jorge.fecha, 'tipo': jorge.tipo, 'numero': jorge.pto_vta_num_full, \
                         'total_c': jorge.total, 'saldo_c': jorge.saldo(), "saldo_t": saldo_t})
                    deta_comp[len(deta_comp) - 1]['detalle_venta'] = []
                    if tip == "DETALLADO":
                        for det in jorge.detalle_venta_set.all():
                            dv = {'cantidad': det.cantidad,
                                  'articulo': det.articulo.denominacion if det.articulo else det.articulo_personalizado,
                                  'total': det.total_con_descuento + det.iva}
                            deta_comp[len(deta_comp) - 1]['detalle_venta'].append(dv)
                detalle.extend(deta_comp)
            print detalle
            comp_saldo = ComposicionSaldo(queryset=detalle)
            # ivav.first_page_number = fi
            comp_saldo.generate_by(PDFGenerator, filename=resp)
            return resp
    else:
        comp = ComposicionSaldoForm()

    # For CSRF protection
    # See http://docs.djangoproject.com/en/dev/ref/contrib/csrf/ 
    c = {'comp': comp,
         }
    c.update(csrf(request))


def rg3685_ventas(request, periodo):
    '''
    VENTAS
    '''
    ventas = Venta.objects.filter(periodo__id=periodo).order_by("fecha")
    if ventas:
        ano = str(Periodo.objects.get(id=periodo).ano)
        mes = str(Periodo.objects.get(id=periodo).mes)
        # Inicializo archivos, Uso StringIO para trabajar directo en memoria.
        z = StringIO()  # Archivo zip, adentro estaran todos los txt
        zf = ZipFile(z, 'w')
        a_comprobantes_v = StringIO()  # Archivo de comprobantes de venta
        a_alicuotas_v = StringIO()
        for v in ventas:
            #
            # INICIO BLOQUE COMPROBANTES VENTAS
            #
            linea_cbte = u''  # Unicode
            # 1 - Fecha de comprobante
            linea_cbte += v.fecha.strftime("%Y%m%d")
            # 2 - Tipo de Comprobante
            linea_cbte += v.codigo_comprobante_segun_afip
            # 3 - Punto de venta
            linea_cbte += str(v.punto_venta).rjust(5, '0')
            # 4 - Numero de comprobante
            linea_cbte += str(v.numero).rjust(20, '0')
            # 5 - Numero de comprobante hasta, igual que anterior
            linea_cbte += str(v.numero).rjust(20, '0')
            # 6 - Codigo de documento del comprador
            linea_cbte += '80' if v.cliente.cuit else '96'
            # 7 - Numero de documento del cliente
            linea_cbte += v.cliente.cuit.replace('-', '').rjust(20, '0')
            # 8 - Apellido y nombre del comprador
            if len(v.cliente.razon_social) >= 31:
                linea_cbte += v.cliente.razon_social[0:30]
            else:
                linea_cbte += v.cliente.razon_social.ljust(30, ' ')
            # 9 - Importe total de la operacion
            linea_cbte += str(v.total_2dec()).replace('.', '').rjust(15, '0')
            # 10 - Total conceptos que no integran neto gravado
            linea_cbte += '000000000000000'
            # 11 - Percepcion a no categorizados
            linea_cbte += '000000000000000'
            # 12 - Importe de operaciones exentas
            linea_cbte += '000000000000000'
            # 13 - Importe de percepciones o pagos a cuenta impuestos nacionales
            linea_cbte += '000000000000000'
            # 14 - Importe de percepciones de Ingresos Brutos
            linea_cbte += '000000000000000'
            # 15 - Importe de percepciones de impuestos municipales
            linea_cbte += '000000000000000'
            # 16 - Importe impuestos internos
            linea_cbte += '000000000000000'
            # 17 - Codigo de moneda
            linea_cbte += v.codigo_moneda_segun_afip
            # 18 - Tipo de cambio
            linea_cbte += '0001000000'
            # 19 - Cantidad alicuotas de IVA
            linea_cbte += '1'
            # 20 - Tipo de operacion
            linea_cbte += ' '
            # 21 - Otros tributos
            linea_cbte += '000000000000000'
            # 22 - Fecha vencimiento de pago
            if v.condicion_venta.id == 1:
                fpago = v.fecha + timedelta(days=15)
                linea_cbte += fpago.strftime("%Y%m%d")
            else:
                linea_cbte += v.fecha.strftime("%Y%m%d")
            # Nueva linea_cbte
            linea_cbte += '\r'
            linea_cbte.encode('windows-1252')
            a_comprobantes_v.write(linea_cbte)
            # ////////////////////////////////////
            # FIN BLOQUE COMPROBANTES VENTAS
            # ////////////////////////////////////

            # ////////////////////////////////////
            # INICIO BLOQUE ALICUOTAS IVA VENTAS
            # ////////////////////////////////////
            linea_alic = u''
            # 1 - Tipo de Comprobante
            linea_alic += v.codigo_comprobante_segun_afip
            # 2 - Punto de venta
            linea_alic += str(v.punto_venta).rjust(5, '0')
            # 3 - Numero de comprobante
            linea_alic += str(v.numero).rjust(20, '0')
            # 4 - Importe Neto gravado
            linea_alic += str(v.neto_2dec()).replace('.', '').rjust(15, '0')
            # 5 - Alicuota de IVA
            linea_alic += '0005'  # IVA 21%
            # 6 - Impuesto liquidado
            linea_alic += v.iva21_2dec().replace('.', '').rjust(15, '0')
            # Nueva linea comprobante
            linea_alic += '\r'
            linea_alic.encode('windows-1252')
            a_alicuotas_v.write(linea_alic)
            # //////////////////////////////////////
            # FIN BLOQUE ALICUOTAS IVA VENTAS
            # //////////////////////////////////////
        zf.writestr('RG3685-Comprobantes-V-' + mes + '-' + ano + '.txt', a_comprobantes_v.getvalue().encode('cp1252'))
        zf.writestr('RG3685-Alicuotas-V-' + mes + '-' + ano + '.txt', a_alicuotas_v.getvalue().encode('cp1252'))
        a_comprobantes_v.close()  # Lo quita de memoria
        a_alicuotas_v.close()  # Lo quita de memoria
        zf.close()
        response = HttpResponse(z.getvalue(), content_type='application/zip')
        # response = HttpResponse(linea_cbte.encode('windows-1252'), content_type="text/plain")
        response['Content-Disposition'] = 'attachment; filename="RG3685-Ventas-' + mes + '-' + ano + '.zip"'
        return response
    else:
        return HttpResponse()

    return render_to_response('informes/comp_saldo.html', c)
