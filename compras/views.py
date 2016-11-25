# Create your views here.
from django.core.urlresolvers import reverse_lazy
from django.db.models.query_utils import Q
from django.forms.formsets import BaseFormSet, formset_factory
from django.http.response import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template.context_processors import csrf
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from compras.forms import ProveedoresForm, DetalleCompraForm, ComprobanteCompraForm
from compras.models import Proveedor, Compra


class ProveedoresList(TemplateView):
    template_name = "proveedores/proveedores_list.html"
  

class ProveedoresNuevo(CreateView):
    model = Proveedor
    form_class = ProveedoresForm
    template_name = "proveedores/proveedores_form.html"
    success_url = reverse_lazy("listaProveedores")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.modificado_por = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse_lazy('listaProveedores'))


class ProveedoresModificar(UpdateView):
    model = Proveedor
    form_class = ProveedoresForm
    template_name = "proveedores/proveedores_form.html"
    success_url = reverse_lazy("listaProveedores")

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.modificado_por = self.request.user
        obj.save()
        return HttpResponseRedirect(reverse_lazy('listaProveedores'))


def proveedoresSuspender(request, pk):
    proveedor = Proveedor.objects.get(pk=pk)
    proveedor.suspendido = True
    proveedor.save()
    return HttpResponseRedirect(reverse_lazy('listaProveedores'))


def proveedoresHabilitar(request, pk):
    proveedores = Proveedor.objects.get(pk=pk)
    proveedores.suspendido = False
    proveedores.save()
    return HttpResponseRedirect(reverse_lazy('listaProveedores'))


def get_num_prox_orden_pago(request):
    return HttpResponse(get_num_orden_pago(), content_type='text/plain')


def get_facturas_pendiente_pago_prov(request, proveedor):
    pro = Proveedor.objects.get(pk=proveedor)
    cpras = Compra.objects.filter(Q(proveedor=pro), ~Q(saldo=0), ~Q(tipo__startswith='NC'))
    data = serializers.serialize("json", cpras, fields=('fecha', 'punto_venta', 'numero', 'tipo'),
                                 extras=('saldo', 'total'))
    return HttpResponse(data, content_type="text/plain")

#TODO: Pasar vista a class-based view
def compra_new(request):
    class RequiredFormSet(BaseFormSet):
        def __init__(self, *args, **kwargs):
            super(RequiredFormSet, self).__init__(*args, **kwargs)
            for form in self.forms:
                form.empty_permitted = False

    DetalleFormSet = formset_factory(DetalleCompraForm, formset=RequiredFormSet)
    if request.method == 'POST':
        facturaForm = ComprobanteCompraForm(request.POST)
        detalleCompraFormset = DetalleFormSet(request.POST, prefix="detalle_compra")
        if facturaForm.is_valid() and detalleCompraFormset.is_valid():
            factura = facturaForm.save(commit=False)
            subtotal = 0
            iva = {None: 0, 10.5: 0, 21: 0, 27: 0}
            for form in detalleCompraFormset.forms:
                detalleItem = form.save(commit=False)
                sub = detalleItem.cantidad * detalleItem.precio_unitario
                subtotal += sub
                iva[detalleItem.iva_alicuota] += detalleItem.iva_valor
            factura.neto = subtotal
            factura.iva21 = iva[21]
            factura.iva105 = iva[10.5]
            factura.iva27 = iva[27]
            saldo = factura.neto + factura.iva21 + factura.iva105 + factura.iva27 + \
                    factura.percepcion_iva + factura.exento + factura.ingresos_brutos + \
                    factura.impuesto_interno + factura.redondeo
            # set_trace()
            if factura.tipo.startswith("NC"):
                factura.neto = factura.neto * -1
                factura.iva105 = factura.iva105 * -1
                factura.iva21 = factura.iva21 * -1
                factura.iva27 = factura.iva27 * -1
                factura.percepcion_iva = factura.percepcion_iva * -1
                factura.exento = factura.exento * -1
                factura.ingresos_brutos = factura.ingresos_brutos * -1
                factura.impuesto_interno = factura.impuesto_interno * -1
                factura.redondeo = factura.redondeo * -1
                subtotal = subtotal * -1
                saldo = saldo * -1
                # Resto de los saldos de otros comprobantes
                otros_comp = Compra.objects.filter(Q(proveedor=factura.proveedor), ~Q(saldo=0)).order_by('fecha', 'numero')
                if otros_comp:
                    if (otros_comp[0].tipo.startswith('NC') and factura.tipo.startswith('NC'))\
                            or (not otros_comp[0].tipo.startswith('NC') and not factura.tipo.startswith('NC')):
                        factura.saldo = saldo
                    else:
                        for comp in otros_comp:
                            if saldo == 0:
                                break
                            if abs(saldo) >= abs(comp.saldo):
                                saldo += comp.saldo
                                comp.saldo = 0
                            else:
                                comp.saldo += saldo
                                saldo = 0
                            comp.save()
                        factura.saldo = saldo
            else:
                factura.saldo = saldo
            factura.save()
            for form in detalleCompraFormset.forms:
                detalleItem = form.save(commit=False)
                detalleItem.compra = factura
                detalleItem.save()
            # set_trace()
            if factura.condicion_compra.descripcion == "Contado" and factura.tipo.startswith("FA"):
                return HttpResponseRedirect(reverse_lazy('nuevaOrdenPagoContado', kwargs={'compra': factura.pk}))
            else:
                return HttpResponseRedirect(reverse_lazy('nuevaCompra'))
    else:
        facturaForm = ComprobanteCompraForm()
        detalleCompraFormset = DetalleFormSet(prefix="detalle_compra")
    # For CSRF protection
    # See http://docs.djangoproject.com/en/dev/ref/contrib/csrf/ 
    # set_trace()
    c = {'compraForm': facturaForm,
         'detalleCompraFormset': detalleCompraFormset,
         }
    c.update(csrf(request))

    return render_to_response('compras/compras_form.html', c)


class ComprasList(TemplateView):
    template_name = "compras/compras_list.html"


def subdiario_iva_compras(request):
    if request.method == 'POST':
        subdiario = SubdiarioIVAPeriodoFecha(request.POST)
        if subdiario.is_valid():
            per = subdiario.cleaned_data['periodo']
            fd = subdiario.cleaned_data['fecha_desde']
            fh = subdiario.cleaned_data['fecha_hasta']
            fi = subdiario.cleaned_data['folio_inicial']
            resp = HttpResponse(mimetype='application/pdf')
            if per:
                compras = Compra.objects.filter(periodo=per).order_by('fecha')
                # set_trace()
                # ivav = IVAVentas(queryset=ventas,periodo=per,folio_inicial=fi)
                ivac = IVACompras(queryset=compras)
                # ivav.first_page_number = fi
                ivac.generate_by(PDFGenerator, filename=resp, variables={'periodo': per.periodo_full()})
                return resp
            else:
                if fh and fd:
                    compras = Compra.objects.filter(fecha__range=(fd, fh)).order_by('fecha')
                    ivac = IVACompras(queryset=compras)
                    ivac.generate_by(PDFGenerator, filename=resp, variables={'periodo': 'N/A'})
                    return resp
    else:
        subdiario = SubdiarioIVAPeriodoFecha()

    # For CSRF protection
    # See http://docs.djangoproject.com/en/dev/ref/contrib/csrf/ 
    c = {'subdiario': subdiario,
         }
    c.update(csrf(request))

    return render_to_response('informes/sub_iva_form.html', c)


def orden_pago_new(request):
    # This class is used to make empty formset forms required
    # See http://stackoverflow.com/questions/2406537/django-formsets-make-first-required/4951032#4951032
    class RequiredFormSet(BaseFormSet):
        def __init__(self, *args, **kwargs):
            super(RequiredFormSet, self).__init__(*args, **kwargs)
            for form in self.forms:
                form.empty_permitted = False

    DetallePagoFormSet = formset_factory(DetallePagoForm, formset=RequiredFormSet)
    ValoresFormSet = formset_factory(ValoresOPForm, formset=RequiredFormSet)
    if request.method == 'POST':  # If the form has been submitted...
        ordenPagoForm = OrdenPagoForm(request.POST)  # A form bound to the POST data
        # Create a formset from the submitted data
        pagoFormset = DetallePagoFormSet(request.POST, prefix='pagos')
        valoresFormset = ValoresFormSet(request.POST, prefix='valores')
        # set_trace()
        if ordenPagoForm.is_valid() and pagoFormset.is_valid() and valoresFormset.is_valid():
            orden_pago = ordenPagoForm.save(commit=False)
            orden_pago.numero = get_num_orden_pago()
            # cred_ant=orden_pago.proveedor.saldo
            # Dejo en 0 el cheque del credito, si hubiera:
            try:
                cheq = ChequeTercero.objects.filter(orden_pago__proveedor=orden_pago.proveedor,
                                                    pendiente_para_orden_pago__gt=0)[0]
                cred_ant = cheq.pendiente_para_orden_pago
                cheq.pendiente_para_orden_pago = 0
                cheq.save()
            except IndexError:
                pass
                cred_ant = 0

            print "CREDITO ANTERIOR: %s" % cred_ant
            orden_pago.credito_anterior = cred_ant
            orden_pago.save()
            # if Decimal(ordenPagoForm.cleaned_data['credito_anterior']) > 0:
            #    Cobranza_credito_anterior.objects.create(orden_pago=orden_pago,monto=ordenPagoForm.cleaned_data['credito_anterior'])
            total_comprobantes = 0
            for detalle_pago in pagoFormset.forms:
                if detalle_pago.cleaned_data['pagar']:
                    if Decimal(detalle_pago.cleaned_data['pagar']) != 0:
                        total_comprobantes += detalle_pago.cleaned_data['pagar']
                        co = Compra.objects.get(pk=detalle_pago.cleaned_data['id_factura_compra'])
                        Detalle_pago.objects.create(orden_pago=orden_pago, compra=co,
                                                    monto=detalle_pago.cleaned_data['pagar'])
                        co.saldo -= detalle_pago.cleaned_data['pagar']
                        co.save()
                        # pagado_total = Detalle_pago.objects.filter(compra=co).aggregate(Sum('monto'))['monto__sum']
                        # nc_total = Venta.objects.filter(comprobante_relacionado=co).aggregate(Sum('total'))
                        # todo = pagado_total['monto__sum'] if pagado_total['monto__sum'] else 0.00 +nc_total['total__sum'] if nc_total['total__sum'] else 0.00
                        # if (co.total-Decimal(0.009) <= todo <= co.total+Decimal(0.009)):
                        # set_trace()
                        # if co.tipo.startswith("NC"):
                        #    co.pagado=True
                        #    co.save()
                        # elif co.total-Decimal(0.009) <= pagado_total <= co.total+Decimal(0.009):
                        #    co.pagado=True
                        #    co.save()
            print total_comprobantes
            for valor in valoresFormset.forms:
                # set_trace()
                if valor.cleaned_data['monto'] <= total_comprobantes + Decimal(0.009) - cred_ant:
                    total_comprobantes -= valor.cleaned_data['monto']
                    if valor.cleaned_data['tipo'] == 'CHT':
                        cheque3 = ChequeTercero.objects.get(pk=valor.cleaned_data['id_cheque_tercero'])
                        cheque3.pendiente_para_orden_pago = 0
                        cheque3.en_cartera = False
                        cheque3.orden_pago = orden_pago
                        cheque3.save()
                    elif valor.cleaned_data['tipo'] == 'CHP':
                        ChequePropio.objects.create(orden_pago=orden_pago, \
                                                    numero=valor.cleaned_data['cheque_numero'], \
                                                    fecha=valor.cleaned_data['cheque_fecha'], \
                                                    cobro=valor.cleaned_data['cheque_cobro'], \
                                                    paguese_a=valor.cleaned_data['cheque_paguese_a'], \
                                                    pendiente_para_orden_pago=0, \
                                                    monto=valor.cleaned_data['monto'])
                    elif valor.cleaned_data['tipo'] == 'EFE':
                        Dinero.objects.create(monto=valor.cleaned_data['monto'], orden_pago=orden_pago)
                    elif valor.cleaned_data['tipo'] == 'TRB':
                        TransferenciaBancariaSaliente.objects.create(orden_pago=orden_pago, \
                                                                     cuenta_origen=valor.cleaned_data[
                                                                         'transferencia_cuenta_origen'], \
                                                                     numero_operacion=valor.cleaned_data[
                                                                         'transferencia_numero_operacion'], \
                                                                     cuenta_destino=valor.cleaned_data[
                                                                         'transferencia_cuenta_destino'], \
                                                                     monto=valor.cleaned_data['monto'])
                else:
                    total_comprobantes -= cred_ant
                    print "TOTAL COMPROBANTES ULTIMO COMP: %s" % total_comprobantes
                    print "DIF: %s" % (valor.cleaned_data['monto'] - total_comprobantes)
                    if ordenPagoForm.cleaned_data['que_hago_con_diferencia'] == 'credito':
                        if valor.cleaned_data['tipo'] == "CHT":
                            cheque3 = ChequeTercero.objects.get(pk=valor.cleaned_data['id_cheque_tercero'])
                            cheque3.pendiente_para_orden_pago = valor.cleaned_data['monto'] - total_comprobantes
                            cheque3.en_cartera = False
                            cheque3.orden_pago = orden_pago
                            cheque3.save()
                        elif valor.cleaned_data['tipo'] == "CHP":
                            ChequePropio.objects.create(orden_pago=orden_pago, \
                                                        numero=valor.cleaned_data['cheque_numero'], \
                                                        fecha=valor.cleaned_data['cheque_fecha'], \
                                                        cobro=valor.cleaned_data['cheque_cobro'], \
                                                        paguese_a=valor.cleaned_data['cheque_paguese_a'], \
                                                        pendiente_para_orden_pago=valor.cleaned_data[
                                                                                      'monto'] - total_comprobantes, \
                                                        monto=valor.cleaned_data['monto'])
                            # orden_pago.proveedor.saldo=valor.cleaned_data['monto']-total_comprobantes
                            # orden_pago.proveedor.save()
                    elif ordenPagoForm.cleaned_data['que_hago_con_diferencia'] == 'vuelto':
                        if valor.cleaned_data['tipo'] == "CHT":
                            cheque3 = ChequeTercero.objects.get(pk=valor.cleaned_data['id_cheque_tercero'])
                            cheque3.pendiente_para_orden_pago = valor.cleaned_data['monto'] - total_comprobantes
                            cheque3.en_cartera = False
                            cheque3.orden_pago = orden_pago
                            cheque3.save()
                        elif valor.cleaned_data['tipo'] == "CHP":
                            ChequePropio.objects.create(orden_pago=orden_pago, \
                                                        numero=valor.cleaned_data['cheque_numero'], \
                                                        fecha=valor.cleaned_data['cheque_fecha'], \
                                                        cobro=valor.cleaned_data['cheque_cobro'], \
                                                        paguese_a=valor.cleaned_data['cheque_paguese_a'], \
                                                        pendiente_para_orden_pago=valor.cleaned_data[
                                                                                      'monto'] - total_comprobantes, \
                                                        monto=valor.cleaned_data['monto'])
                        Dinero.objects.create(orden_pago=orden_pago,
                                              monto=(valor.cleaned_data['monto'] - total_comprobantes) * -1)
                        # orden_pago.proveedor.saldo=0
                        # orden_pago.proveedor.save()
            obj = {'id': orden_pago.id}
            s = StringIO()
            json.dump(obj, s)
            s.seek(0)
            return HttpResponse(s.read())

    else:
        ordenPagoForm = OrdenPagoForm()
        pagoFormset = DetallePagoFormSet(prefix='pagos')
        valoresFormset = ValoresFormSet(prefix='valores')

    # For CSRF protection
    # See http://docs.djangoproject.com/en/dev/ref/contrib/csrf/ 
    # set_trace()
    c = {'ordenPagoForm': ordenPagoForm,
         'pagoFormset': pagoFormset,
         'valoresFormset': valoresFormset,
         }
    c.update(csrf(request))

    return render_to_response('compras/orden_pago_new.html', c)


def orden_pago_contado_new(request, compra):
    # This class is used to make empty formset forms required
    # See http://stackoverflow.com/questions/2406537/django-formsets-make-first-required/4951032#4951032
    class RequiredFormSet(BaseFormSet):
        def __init__(self, *args, **kwargs):
            super(RequiredFormSet, self).__init__(*args, **kwargs)
            for form in self.forms:
                form.empty_permitted = False

    DetallePagoFormSet = formset_factory(DetallePagoContadoForm, extra=0)
    ValoresFormSet = formset_factory(ValoresOPForm, formset=RequiredFormSet)
    if request.method == 'POST':  # If the form has been submitted...
        ordenPagoForm = OrdenPagoForm(request.POST)  # A form bound to the POST data
        # Create a formset from the submitted data
        pagoFormset = DetallePagoFormSet(request.POST, prefix='pagos')
        valoresFormset = ValoresFormSet(request.POST, prefix='valores')
        # set_trace()
        if ordenPagoForm.is_valid() and pagoFormset.is_valid() and valoresFormset.is_valid():
            orden_pago = ordenPagoForm.save(commit=False)
            orden_pago.numero = get_num_orden_pago()
            # Dejo en 0 el cheque del credito, si hubiera:
            try:
                cheq = ChequeTercero.objects.filter(orden_pago__proveedor=orden_pago.proveedor,
                                                    pendiente_para_orden_pago__gt=0)[0]
                cred_ant = cheq.pendiente_para_orden_pago
                cheq.pendiente_para_orden_pago = 0
                cheq.save()
            except IndexError:
                pass
                cred_ant = 0
            # cred_ant=orden_pago.proveedor.saldo
            print "CREDITO ANTERIOR: %s" % cred_ant
            orden_pago.credito_anterior = cred_ant
            orden_pago.save()

            # if Decimal(ordenPagoForm.cleaned_data['credito_anterior']) > 0:
            #    Cobranza_credito_anterior.objects.create(orden_pago=orden_pago,monto=ordenPagoForm.cleaned_data['credito_anterior'])
            total_comprobantes = 0
            for detalle_pago in pagoFormset.forms:
                co = Compra.objects.get(pk=detalle_pago.cleaned_data['id_factura_compra'])
                Detalle_pago.objects.create(orden_pago=orden_pago, compra=co, monto=co.total)
                # co.pagado=True
                co.saldo = 0
                total_comprobantes = co.total
                co.save()
            print total_comprobantes
            for valor in valoresFormset.forms:
                # set_trace()
                if valor.cleaned_data['monto'] <= total_comprobantes + Decimal(0.009) - cred_ant:
                    total_comprobantes -= valor.cleaned_data['monto']
                    if valor.cleaned_data['tipo'] == 'CHT':
                        cheque3 = ChequeTercero.objects.get(pk=valor.cleaned_data['id_cheque_tercero'])
                        cheque3.pendiente_para_orden_pago = 0
                        cheque3.en_cartera = False
                        cheque3.orden_pago = orden_pago
                        cheque3.save()
                    elif valor.cleaned_data['tipo'] == 'CHP':
                        ChequePropio.objects.create(orden_pago=orden_pago, \
                                                    numero=valor.cleaned_data['cheque_numero'], \
                                                    fecha=valor.cleaned_data['cheque_fecha'], \
                                                    cobro=valor.cleaned_data['cheque_cobro'], \
                                                    paguese_a=valor.cleaned_data['cheque_paguese_a'], \
                                                    pendiente_para_orden_pago=0, \
                                                    monto=valor.cleaned_data['monto'])
                    elif valor.cleaned_data['tipo'] == 'EFE':
                        Dinero.objects.create(monto=valor.cleaned_data['monto'], orden_pago=orden_pago)
                    elif valor.cleaned_data['tipo'] == 'TRB':
                        TransferenciaBancariaSaliente.objects.create(orden_pago=orden_pago, \
                                                                     cuenta_origen=valor.cleaned_data[
                                                                         'transferencia_cuenta_origen'], \
                                                                     numero_operacion=valor.cleaned_data[
                                                                         'transferencia_numero_operacion'], \
                                                                     cuenta_destino=valor.cleaned_data[
                                                                         'transferencia_cuenta_destino'], \
                                                                     monto=valor.cleaned_data['monto'])
                else:
                    print "-----------------------------SOBRANTE------------------------"
                    total_comprobantes -= cred_ant
                    print "TOTAL COMPROBANTES ULTIMO COMP: %s" % total_comprobantes
                    print "DIF: %s" % (valor.cleaned_data['monto'] - total_comprobantes)
                    if ordenPagoForm.cleaned_data['que_hago_con_diferencia'] == 'credito':
                        print "---------------------!!!---!!!------A CREDITO-------------------"
                        if valor.cleaned_data['tipo'] == "CHT":
                            cheque3 = ChequeTercero.objects.get(pk=valor.cleaned_data['id_cheque_tercero'])
                            cheque3.pendiente_para_orden_pago = valor.cleaned_data['monto'] - total_comprobantes
                            cheque3.en_cartera = False
                            cheque3.orden_pago = orden_pago
                            cheque3.save()
                        elif valor.cleaned_data['tipo'] == "CHP":
                            ChequePropio.objects.create(orden_pago=orden_pago, \
                                                        numero=valor.cleaned_data['cheque_numero'], \
                                                        fecha=valor.cleaned_data['cheque_fecha'], \
                                                        cobro=valor.cleaned_data['cheque_cobro'], \
                                                        paguese_a=valor.cleaned_data['cheque_paguese_a'], \
                                                        pendiente_para_orden_pago=valor.cleaned_data[
                                                                                      'monto'] - total_comprobantes, \
                                                        monto=valor.cleaned_data['monto'])
                            # orden_pago.proveedor.saldo=valor.cleaned_data['monto']-total_comprobantes
                            # orden_pago.proveedor.save()
                    elif ordenPagoForm.cleaned_data['que_hago_con_diferencia'] == 'vuelto':
                        if valor.cleaned_data['tipo'] == "CHT":
                            cheque3 = ChequeTercero.objects.get(pk=valor.cleaned_data['id_cheque_tercero'])
                            cheque3.pendiente_para_orden_pago = valor.cleaned_data['monto'] - total_comprobantes
                            cheque3.en_cartera = False
                            cheque3.orden_pago = orden_pago
                            cheque3.save()
                        elif valor.cleaned_data['tipo'] == "CHP":
                            ChequePropio.objects.create(orden_pago=orden_pago, \
                                                        numero=valor.cleaned_data['cheque_numero'], \
                                                        fecha=valor.cleaned_data['cheque_fecha'], \
                                                        cobro=valor.cleaned_data['cheque_cobro'], \
                                                        paguese_a=valor.cleaned_data['cheque_paguese_a'], \
                                                        pendiente_para_orden_pago=valor.cleaned_data[
                                                                                      'monto'] - total_comprobantes, \
                                                        monto=valor.cleaned_data['monto'])
                        Dinero.objects.create(orden_pago=orden_pago,
                                              monto=(valor.cleaned_data['monto'] - total_comprobantes) * -1)
                        # orden_pago.proveedor.saldo=0
                        # orden_pago.proveedor.save()
            obj = {'id': orden_pago.id}
            s = StringIO()
            json.dump(obj, s)
            s.seek(0)
            return HttpResponse(s.read())

    else:
        cp = Compra.objects.get(pk=compra)
        ordenPagoForm = OrdenPagoContadoForm(initial={'proveedor': cp.proveedor})
        pagoFormset = DetallePagoFormSet(prefix='pagos', initial=[{'id_factura_compra': cp.pk}])
        valoresFormset = ValoresFormSet(prefix='valores')

    # For CSRF protection
    # See http://docs.djangoproject.com/en/dev/ref/contrib/csrf/ 
    # set_trace()
    c = {'ordenPagoForm': ordenPagoForm,
         'pagoFormset': pagoFormset,
         'valoresFormset': valoresFormset,
         'compra': cp,
         }
    c.update(csrf(request))

    return render_to_response('compras/orden_pago_contado_new.html', c)


class PagosList(TemplateView):
    template_name = "pagos/cobros_list.html"


def imprimirOrdenPago(request, pk):
    ops = OrdenPago.objects.get(pk=pk)
    qs = []
    orp = {'numero_full': ops.numero_full, 'fecha_dd_mm_aaaa': ops.fecha_dd_mm_aaaa,
           'proveedor_razon_social': ops.proveedor.razon_social, \
           'proveedor_direccion': ops.proveedor.direccion, 'proveedor_localidad': ops.proveedor.localidad, \
           'proveedor_condicion_iva': ops.proveedor.get_condicion_iva_display(), 'proveedor_cuit': ops.proveedor.cuit, \
           'proveedor_codigo_ingresos_brutos': ops.proveedor.codigo_ingresos_brutos, 'detalle_pago_set': [], \
           'dinero_set': []}
    for deta in ops.detalle_pago_set.all():
        orp['detalle_pago_set'].append({'compra_fecha_dd_mm_aaaa': deta.compra.fecha_dd_mm_aaaa, \
                                        'compra_identificador_completo': deta.compra.identificador_completo, \
                                        'monto': round(deta.monto, 2)})
    if ops.saldo_a_cuenta > 0:
        orp['detalle_pago_set'].insert(0, {'compra_fecha_dd_mm_aaaa': "", \
                                           'compra_identificador_completo': "    A CUENTA", \
                                           'monto': round(ops.saldo_a_cuenta, 2)})
    if ops.credito_anterior > 0:
        orp['detalle_pago_set'].insert(0, {'compra_fecha_dd_mm_aaaa': "", \
                                           'compra_identificador_completo': "CREDITO ANTERIOR", \
                                           'monto': -round(ops.credito_anterior, 2)})
    for dine in ops.dinero_set.all():
        orp['dinero_set'].append(
            {'tipo_valor': dine.tipo_valor, 'entidad': dine.entidad, 'num_comprobante': dine.num_comprobante, \
             'CUIT': dine.CUIT, 'FECHA': dine.FECHA, 'monto': round(dine.monto, 2)})
    qs.append(orp)
    print qs
    resp = HttpResponse(mimetype='application/pdf')
    op = OrdenPagoReport(queryset=qs)
    op.generate_by(PDFGenerator, filename=resp)
    return resp


def proveedores_resumen_cuenta(request):
    if request.method == 'POST':
        resumen = ProveedoresResumenCuentaForm(request.POST)
        if resumen.is_valid():
            lis = resumen.cleaned_data['listar']
            if lis == "UNO":
                pro = resumen.cleaned_data['proveedor']
            fd = resumen.cleaned_data['desde']
            fh = resumen.cleaned_data['hasta']
            resp = HttpResponse(mimetype='application/pdf')
            # detalle=[{'id':pro.id,'razon_social':pro.razon_social,'detalle_comprobantes':[]}]
            detalle = []
            # Defino las consultas Q
            fact = Q(tipo__startswith="FA")
            nd = Q(tipo__startswith="ND")
            # apr=Q(aprobado=True)
            fe = Q(fecha__range=(fd, fh))
            nc = Q(tipo__startswith="NC")
            if lis == "UNO":
                proq = Q(proveedor=pro)
                factynd = Compra.objects.filter(proq, fe, fact | nd)
                ncrs = Compra.objects.filter(proq, fe, nc)
                ops = OrdenPago.objects.filter(proq, fe)
            elif lis == "TODOS":
                factynd = Compra.objects.filter(fe, fact | nd).order_by('proveedor__razon_social')
                ncrs = Compra.objects.filter(fe, nc)
                ops = OrdenPago.objects.filter(fe)
            array_proveedores = []
            for el in factynd.values():
                if not el['proveedor_id'] in array_proveedores:
                    array_proveedores.append(el['proveedor_id'])
            for proveedor in array_proveedores:
                deta_comp = []
                factynd_c = factynd.filter(proveedor__id=proveedor)
                ncrs_c = ncrs.filter(proveedor__id=proveedor)
                ops_c = ops.filter(proveedor__id=proveedor)
                for jorge in factynd_c:
                    deta_comp.append(
                        {'proveedor_id': proveedor, 'razon_social': Proveedor.objects.get(id=proveedor).razon_social, \
                         'fecha': jorge.fecha, 'tipo': jorge.tipo, 'numero': jorge.identificador, \
                         'debe': jorge.total, 'haber': Decimal("0.00"), "saldo": Decimal("0.00")})
                for jorge in ncrs_c:
                    deta_comp.append(
                        {'proveedor_id': proveedor, 'razon_social': Proveedor.objects.get(id=proveedor).razon_social, \
                         'fecha': jorge.fecha, 'tipo': jorge.tipo, 'numero': jorge.identificador, \
                         'debe': Decimal("0.00"), 'haber': jorge.total * -1, "saldo": Decimal("0.00")})
                for op in ops_c:
                    deta_comp.append(
                        {'proveedor_id': proveedor, 'razon_social': Proveedor.objects.get(id=proveedor).razon_social, \
                         'fecha': op.fecha, 'tipo': 'REC', 'numero': op.numero_full, \
                         'debe': Decimal("0.00"), 'haber': op.total, "saldo": Decimal("0.00")})
                deta_comp = sorted(deta_comp, key=itemgetter('fecha'))
                deta_comp.insert(0, {'proveedor_id': proveedor,
                                     'razon_social': Proveedor.objects.get(id=proveedor).razon_social, \
                                     'fecha': 'Saldo anterior', 'tipo': '', 'numero': '', 'debe': '', 'haber': '', \
                                     'saldo': Proveedor.objects.get(id=proveedor).saldo_anterior(fd)})
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
            resumen_cuenta = ResumenCuentaProveedores(queryset=detalle)
            # ivav.first_page_number = fi
            resumen_cuenta.generate_by(PDFGenerator, filename=resp)
            return resp
    else:
        resumen = ProveedoresResumenCuentaForm()

    # For CSRF protection
    # See http://docs.djangoproject.com/en/dev/ref/contrib/csrf/ 
    c = {'resumen': resumen,
         }
    c.update(csrf(request))

    return render_to_response('informes/proveedores_resumen_cuenta.html', c)


def proveedores_comp_saldo(request):
    if request.method == 'POST':
        comp = ProveedoresComposicionSaldoForm(request.POST)
        if comp.is_valid():
            lis = comp.cleaned_data['listar']
            tip = comp.cleaned_data['tipo']
            if lis == "UNO":
                pro = comp.cleaned_data['proveedor']
            resp = HttpResponse(mimetype='application/pdf')
            # detalle=[{'id':pro.id,'razon_social':pro.razon_social,'detalle_comprobantes':[]}]
            detalle = []
            # Defino las consultas Q
            # fact=Q(tipo__startswith="FA")
            # nd=Q(tipo__startswith="ND")
            npag = Q(pagado=False)
            if lis == "UNO":
                proq = Q(proveedor=pro)
                factynd = Compra.objects.filter(proq, npag)
            elif lis == "TODOS":
                factynd = Compra.objects.filter(npag).order_by('proveedor__razon_social')
            array_proveedores = []
            for el in factynd.values():
                if not el['proveedor_id'] in array_proveedores:
                    array_proveedores.append(el['proveedor_id'])
            for proveedor in array_proveedores:
                deta_comp = []
                factynd_c = factynd.filter(proveedor__id=proveedor)
                saldo_t = 0
                for jorge in factynd_c:
                    saldo_t += jorge.saldo
                    deta_comp.append(
                        {'proveedor_id': proveedor, 'razon_social': Proveedor.objects.get(id=proveedor).razon_social, \
                         'fecha': jorge.fecha, 'tipo': jorge.tipo, 'numero': jorge.identificador, \
                         'total_c': jorge.total, 'saldo_c': jorge.saldo, "saldo_t": saldo_t})
                    deta_comp[len(deta_comp) - 1]['detalle_compra'] = []
                    if tip == "DETALLADO":
                        for det in jorge.detalle_compra_set.all():
                            dc = {'cantidad': det.cantidad, 'articulo': det.detalle, 'total': det.total}
                            deta_comp[len(deta_comp) - 1]['detalle_venta'].append(dc)
                detalle.extend(deta_comp)
            print detalle
            comp_saldo = ComposicionSaldoProveedores(queryset=detalle)
            # ivav.first_page_number = fi
            comp_saldo.generate_by(PDFGenerator, filename=resp)
            return resp
    else:
        comp = ProveedoresComposicionSaldoForm()

    # For CSRF protection
    # See http://docs.djangoproject.com/en/dev/ref/contrib/csrf/ 
    c = {'comp': comp,
         }
    c.update(csrf(request))

    return render_to_response('informes/proveedores_comp_saldo.html', c)


def rg3685_compras(request, periodo):
    '''
    COMPRAS
    '''
    compras = Compra.objects.filter(periodo__id=periodo).order_by("fecha")
    if compras:
        ano = str(Periodo.objects.get(id=periodo).ano)
        mes = str(Periodo.objects.get(id=periodo).mes)
        # Inicializo archivos, Uso StringIO para trabajar directo en memoria.
        z = StringIO()  # Archivo zip, adentro estaran todos los txt
        zf = ZipFile(z, 'w')
        a_comprobantes_c = StringIO()  # Archivo de comprobantes de venta
        a_alicuotas_c = StringIO()
        for v in compras:
            #
            # INICIO BLOQUE COMPROBANTES COMPRAS
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
            # 5 - Despacho de importacion
            linea_cbte += '                '
            # 6 - Codigo de documento del vendedor
            linea_cbte += '80' if v.proveedor.cuit else '96'
            # 7 - Numero de documento del proveedor
            linea_cbte += v.proveedor.cuit.replace('-', '').rjust(20, '0')
            # 8 - Apellido y nombre del comprador
            if len(v.proveedor.razon_social) >= 31:
                linea_cbte += v.proveedor.razon_social[0:30]
            else:
                linea_cbte += v.proveedor.razon_social.ljust(30, ' ')
            # 9 - Importe total de la operacion
            if v.total >= 0:
                tot = "%.2f" % v.total
                linea_cbte += tot.replace('.', '').replace('-', '').rjust(15, '0')
            else:
                tot = "%.2f" % v.total
                linea_cbte += '-' + tot.replace('.', '').replace('-', '').rjust(14, '0')
            # 10 - Total conceptos que no integran neto gravado
            linea_cbte += '000000000000000'
            # 11 - Importe de operaciones exentas
            if v.exento >= 0:
                ex = "%.2f" % v.exento
                linea_cbte += ex.replace('.', '').replace('-', '').rjust(15, '0')
            else:
                ex = "%.2f" % v.exento
                linea_cbte += '-' + ex.replace('.', '').replace('-', '').rjust(14, '0')
            # 12 - Pagos a cuenta IVA
            linea_cbte += '000000000000000'
            # 13 - Importe de percepciones o pagos a cuenta impuestos nacionales
            linea_cbte += '000000000000000'
            # 14 - Importe de percepciones de Ingresos Brutos
            if v.ingresos_brutos >= 0:
                ing = "%.2f" % v.ingresos_brutos
                linea_cbte += ing.replace('.', '').replace('-', '').rjust(15, '0')
            else:
                ing = "%.2f" % v.ingresos_brutos
                linea_cbte += '-' + ing.replace('.', '').replace('-', '').rjust(14, '0')
            # 15 - Importe de percepciones de impuestos municipales
            linea_cbte += '000000000000000'
            # 16 - Importe impuestos internos
            if v.impuesto_interno >= 0:
                imp = "%.2f" % v.impuesto_interno
                linea_cbte += imp.replace('.', '').replace('-', '').rjust(15, '0')
            else:
                imp = "%.2f" % v.impuesto_interno
                linea_cbte += '-' + imp.replace('.', '').replace('-', '').rjust(14, '0')
            # 17 - Codigo de moneda
            linea_cbte += v.codigo_moneda_segun_afip
            # 18 - Tipo de cambio
            linea_cbte += '0001000000'
            # 19 - Cantidad alicuotas de IVA
            # Reviso en el detalle de ese comprobante las distintas alicuotas de IVA
            alics = []
            if v.tipo.endswith('C'):
                linea_cbte += '0'
            else:
                for det in v.detalle_compra_set.all():
                    if det.iva not in alics:
                        alics.append(det.iva)
                linea_cbte += str(len(alics))
            # 20 - Tipo de operacion
            linea_cbte += 'N'
            # 21 - Credito fiscal computable
            if v.iva >= 0:
                iva = "%.2f" % v.iva
                linea_cbte += iva.replace('.', '').replace('-', '').rjust(15, '0')
            else:
                iva = "%.2f" % v.iva
                linea_cbte += '-' + iva.replace('.', '').replace('-', '').rjust(14, '0')
            # 22 - Otros tributos
            linea_cbte += '000000000000000'
            # 23 - CUIT emisor/corredor
            linea_cbte += '00000000000'
            # 24 - Denominacion del emisor/corredor
            linea_cbte += '                              '
            # 25 - IVA comision
            linea_cbte += '000000000000000'
            # Nueva linea_cbte
            linea_cbte += '\r'
            linea_cbte.encode('windows-1252')
            a_comprobantes_c.write(linea_cbte)
            # ////////////////////////////////////
            # FIN BLOQUE COMPROBANTES COMPRAS
            # ////////////////////////////////////

            # ////////////////////////////////////
            # INICIO BLOQUE ALICUOTAS IVA COMPRAS
            # ////////////////////////////////////
            linea_altalic = u''
            # 1 - Tipo de Comprobante
            linea_altalic += v.codigo_comprobante_segun_afip
            # 2 - Punto de venta
            linea_altalic += str(v.punto_venta).rjust(5, '0')
            # 3 - Numero de comprobante
            linea_altalic += str(v.numero).rjust(20, '0')
            # 4 - Codigo de documento del vendedor
            linea_altalic += '80' if v.proveedor.cuit else '96'
            # 5 - Numero de documento del vendedor
            linea_altalic += v.proveedor.cuit.replace('-', '').rjust(20, '0')
            neto_0 = 0
            neto_21 = 0
            neto_105 = 0
            neto_27 = 0
            for det in v.detalle_compra_set.all():
                if det.iva == 0:
                    neto_0 += det.cantidad * det.precio_unitario
                elif det.iva == 21:
                    neto_21 += det.cantidad * det.precio_unitario
                elif det.iva == 10.5:
                    neto_105 += det.cantidad * det.precio_unitario
                elif det.iva == 27:
                    neto_27 += det.cantidad * det.precio_unitario
            if neto_0 != 0:
                linea_alic = linea_altalic
                # 4 - Importe Neto gravado
                ne = "%.2f" % neto_0
                linea_alic += ne.replace('.', '').rjust(15, '0') if neto_0 >= 0 else '-' + ne.replace('.', '').replace(
                    '-', '').rjust(14, '0')
                # 6 - Alicuota de IVA
                linea_alic += '0003'  # IVA 21%
                # 7 - Impuesto liquidado
                iv0 = "0"
                linea_alic += iv0.replace('.', '').rjust(15, '0') if iv0 >= 0 else '-' + iv0.replace('.', '').replace(
                    '-', '').rjust(14, '0')
                linea_alic += '\r'
                linea_alic.encode('windows-1252')
                a_alicuotas_c.write(linea_alic)
            if v.iva21 != 0:
                linea_alic = linea_altalic
                # 4 - Importe Neto gravado
                ne = "%.2f" % neto_21
                linea_alic += ne.replace('.', '').rjust(15, '0') if v.neto >= 0 else '-' + ne.replace('.', '').replace(
                    '-', '').rjust(14, '0')
                # 6 - Alicuota de IVA
                linea_alic += '0005'  # IVA 21%
                # 7 - Impuesto liquidado
                iv21 = "%.2f" % v.iva21
                linea_alic += iv21.replace('.', '').rjust(15, '0') if v.iva21 >= 0 else '-' + iv21.replace('.',
                                                                                                           '').replace(
                    '-', '').rjust(14, '0')
                linea_alic += '\r'
                linea_alic.encode('windows-1252')
                a_alicuotas_c.write(linea_alic)
            if v.iva105 != 0:
                linea_alic = linea_altalic
                # 4 - Importe Neto gravado
                ne = "%.2f" % neto_105
                linea_alic += ne.replace('.', '').rjust(15, '0') if v.neto >= 0 else '-' + ne.replace('.', '').replace(
                    '-', '').rjust(14, '0')
                # 6 - Alicuota de IVA
                linea_alic += '0004'  # IVA 10,5%
                # 7 - Impuesto liquidado
                iv105 = "%.2f" % v.iva105
                linea_alic += iv105.replace('.', '').rjust(15, '0') if v.iva105 >= 0 else '-' + iv105.replace('.',
                                                                                                              '').replace(
                    '-', '').rjust(14, '0')
                linea_alic += '\r'
                linea_alic.encode('windows-1252')
                a_alicuotas_c.write(linea_alic)
            if v.iva27 != 0:
                linea_alic = linea_altalic
                # 4 - Importe Neto gravado
                ne = "%.2f" % neto_27
                linea_alic += ne.replace('.', '').rjust(15, '0') if v.neto >= 0 else '-' + ne.replace('.', '').replace(
                    '-', '').rjust(14, '0')
                # 6 - Alicuota de IVA
                linea_alic += '0006'  # IVA 27%
                # 7 - Impuesto liquidado
                iv27 = "%.2f" % v.iva27
                linea_alic += iv27.replace('.', '').rjust(15, '0') if v.iva27 >= 0 else '-' + iv27.replace('.',
                                                                                                           '').replace(
                    '-', '').rjust(14, '0')
                linea_alic += '\r'
                linea_alic.encode('windows-1252')
                a_alicuotas_c.write(linea_alic)

                # //////////////////////////////////////
                # FIN BLOQUE ALICUOTAS IVA VENTAS
                # //////////////////////////////////////
        zf.writestr('RG3685-Comprobantes-C-' + mes + '-' + ano + '.txt', a_comprobantes_c.getvalue().encode('cp1252'))
        zf.writestr('RG3685-Alicuotas-C-' + mes + '-' + ano + '.txt', a_alicuotas_c.getvalue().encode('cp1252'))
        a_comprobantes_c.close()  # Lo quita de memoria
        a_alicuotas_c.close()  # Lo quita de memoria
        zf.close()
        response = HttpResponse(z.getvalue(), content_type='application/zip')
        # response = HttpResponse(linea_cbte.encode('windows-1252'), content_type="text/plain")
        response['Content-Disposition'] = 'attachment; filename="RG3685-Compras-' + mes + '-' + ano + '.zip"'
        return response
    else:
        return HttpResponse()
