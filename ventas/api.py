# -*- coding: utf-8 -*-
from StringIO import StringIO
from decimal import Decimal
import json

import datetime
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse, reverse_lazy
from django.db.models.query_utils import Q
from django.http.response import HttpResponse, JsonResponse
from django.utils.datastructures import MultiValueDictKeyError

from core.api import _getattr_foreingkey, filtering, ordering, make_data, ApiTableActions
from core.models import Dinero
from ventas.models import Articulo, Cliente, Rubro, SubRubro, Linea, Condicion_venta, Venta, Recibo, Detalle_cobro
from voolean.settings import PUNTO_VENTA_FAA, PUNTO_VENTA_FAB, PUNTO_VENTA_NCA, PUNTO_VENTA_NCB, PUNTO_VENTA_NDA, \
    PUNTO_VENTA_NDB, ES_MONOTRIBUTO, RAZON_SOCIAL_EMPRESA

__author__ = 'jorge'


######    FK'S    ######

def get_rubros_fk(request):
    phrase = request.GET['ph']
    rubros_qs = Rubro.objects.filter(nombre__icontains=phrase)
    rubros = []
    for rubro in rubros_qs:
        rubros.append({'nombre': rubro.nombre, 'pk': rubro.pk})
    s = StringIO()
    json.dump(rubros, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_lineas_fk(request):
    phrase = request.GET['ph']
    lineas_qs = Linea.objects.filter(nombre__icontains=phrase)
    lineas = []
    for linea in lineas_qs:
        lineas.append({'nombre': linea.nombre, 'pk': linea.pk})
    s = StringIO()
    json.dump(lineas, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_subrubros_fk(request):
    phrase = request.GET['ph']
    subrubros_qs = SubRubro.objects.filter(nombre__icontains=phrase)
    subrubros = []
    for subrubro in subrubros_qs:
        subrubros.append({'nombre': subrubro.nombre, 'pk': subrubro.pk})
    s = StringIO()
    json.dump(subrubros, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_clientes_fk(request):
    phrase = request.GET['ph']
    clientes_qs = Cliente.objects.filter(razon_social__icontains=phrase)
    clientes = []
    for cliente in clientes_qs:
        clientes.append({'razon_social': cliente.razon_social, 'pk': cliente.pk})
    s = StringIO()
    json.dump(clientes, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_articulos_fk(request):
    phrase = request.GET['ph']
    try:
        iva_inc = True if 'iva_inc' in request.GET else False
    except MultiValueDictKeyError:
        iva_inc = False
    denominacion = Q(denominacion__icontains=phrase)
    codigo = Q(codigo__icontains=phrase)
    codigo_fabrica = Q(codigo_fabrica__icontains=phrase)
    articulos_qs = Articulo.objects.filter(denominacion | codigo | codigo_fabrica)
    articulos = []
    for articulo in articulos_qs:
        if iva_inc:
            articulos.append({'articulo': articulo.denominacion, 'pk': articulo.pk, 'precio': articulo.precio_venta_iva_inc, 'iva':articulo.iva})
        else:
            articulos.append(
                {'articulo': articulo.denominacion, 'pk': articulo.pk, 'precio': articulo.precio_venta, 'iva':articulo.iva})
    s = StringIO()
    json.dump(articulos, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_rubros_table(request):
    objects = Rubro.objects.all()
    list_display = ['cod', 'nombre', 'get_iva_display()']
    list_global_search = ['nombre']
    data_struct = {0: 'cod', 1: 'nombre', 2: 'iva'}

    # Cuenta total de articulos:
    recordsTotal = objects.count()

    # Filtrado de los articulos
    objects = filtering(request.GET, objects, data_struct, list_global_search)

    # Ordenado
    objects = ordering(request.GET, objects, data_struct)

    # Conteo de articulos despues dle filtrado
    recordsFiltered = objects.count()

    # finally, slice according to length sent by dataTables:
    start = int(request.GET['start'])
    length = int(request.GET['length'])
    objects = objects[start: (start + length)]

    data = make_data(objects, list_display, 'editarRubro')
    # define response
    response = {
        'data': data,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'draw': request.GET['draw']
    }

    # serialize to json
    s = StringIO()
    json.dump(response, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_subrubros_table(request):
    objects = SubRubro.objects.all()
    list_display = ['rubro.nombre', 'nombre', 'get_iva_display()']
    list_global_search = ['rubro__nombre', 'nombre']
    data_struct = {0: 'rubro__nombre', 1: 'nombre', 2: 'iva'}

    # Cuenta total de articulos:
    recordsTotal = objects.count()

    # Filtrado de los articulos
    objects = filtering(request.GET, objects, data_struct, list_global_search)

    # Ordenado
    objects = ordering(request.GET, objects, data_struct)

    # Conteo de articulos despues dle filtrado
    recordsFiltered = objects.count()

    # finally, slice according to length sent by dataTables:
    start = int(request.GET['start'])
    length = int(request.GET['length'])
    objects = objects[start: (start + length)]

    data = make_data(objects, list_display, 'editarSubrubro')
    # define response
    response = {
        'data': data,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'draw': request.GET['draw']
    }

    # serialize to json
    s = StringIO()
    json.dump(response, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_lineas_table(request):
    objects = Linea.objects.all()
    list_display = ['nombre']
    list_global_search = ['nombre']
    data_struct = {0: 'nombre'}

    # Cuenta total de articulos:
    recordsTotal = objects.count()

    # Filtrado de los articulos
    objects = filtering(request.GET, objects, data_struct, list_global_search)

    # Ordenado
    objects = ordering(request.GET, objects, data_struct)

    # Conteo de articulos despues dle filtrado
    recordsFiltered = objects.count()

    # finally, slice according to length sent by dataTables:
    start = int(request.GET['start'])
    length = int(request.GET['length'])
    objects = objects[start: (start + length)]

    data = make_data(objects, list_display, 'editarLinea')
    # define response
    response = {
        'data': data,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'draw': request.GET['draw']
    }

    # serialize to json
    s = StringIO()
    json.dump(response, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_articulos_table(request):
    objects = Articulo.objects.all()
    desde = request.GET['desde']
    es_b = True if 'es_b' in request.GET else False
    if desde == 'seleccionArticulo':
        list_display = ['pk', 'codigo', 'codigo_fabrica', 'denominacion', 'rubro.nombre', 'precio_venta']
        # list_filter = ['codigo', 'codigo_fabrica','denominacion']
    elif desde == 'mainArticulos':
        list_display = ['codigo', 'codigo_fabrica', 'denominacion', 'linea.nombre', 'subrubro.nombre',
                        'ultima_actualizacion_precio']
        list_global_search = ['denominacion', 'codigo', 'codigo_fabrica']
        data_struct = dict(enumerate(list_display))

    # Cuenta total de articulos:
    recordsTotal = objects.count()

    # Filtrado de los articulos
    objects = filtering(request.GET, objects, data_struct, list_global_search)

    # Ordenado
    objects = ordering(request.GET, objects, data_struct)

    # Conteo de articulos despues dle filtrado
    recordsFiltered = objects.count()

    # finally, slice according to length sent by dataTables:
    start = int(request.GET['start'])
    length = int(request.GET['length'])
    objects = objects[start: (start + length)]

    # extract information
    data = make_data(objects, list_display, "editarArticulo", "suspenderArticulo", "habilitarArticulo")

    # define response
    response = {
        'data': data,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'draw': request.GET['draw']
    }

    # serialize to json
    s = StringIO()
    json.dump(response, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_condiciones_venta_table(request):
    objects = Condicion_venta.objects.all()
    list_display = ['descripcion']
    list_global_search = list_display
    data_struct = dict(enumerate(list_display))

    # Cuenta total de articulos:
    recordsTotal = objects.count()

    # Filtrado de los articulos
    objects = filtering(request.GET, objects, data_struct, list_global_search)

    # Ordenado
    objects = ordering(request.GET, objects, data_struct)

    # Conteo de articulos despues dle filtrado
    recordsFiltered = objects.count()

    # finally, slice according to length sent by dataTables:
    start = int(request.GET['start'])
    length = int(request.GET['length'])
    objects = objects[start: (start + length)]

    data = make_data(objects, list_display, 'editarCondicionVenta')
    # define response
    response = {
        'data': data,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'draw': request.GET['draw']
    }

    # serialize to json
    s = StringIO()
    json.dump(response, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_clientes_table(request):
    objects = Cliente.objects.all()
    list_display = ['cuit', 'razon_social', 'localidad', 'get_provincia_display()', 'telefono']
    list_global_search = list_display[1:2]
    data_struct = dict(enumerate(list_display))

    # Cuenta total de articulos:
    recordsTotal = objects.count()

    # Filtrado general de los articulos
    objects = filtering(request.GET, objects, data_struct, list_global_search)

    # Ordenado
    objects = ordering(request.GET, objects, data_struct)

    # Conteo de articulos despues dle filtrado
    recordsFiltered = objects.count()

    # finally, slice according to length sent by dataTables:
    start = int(request.GET['start'])
    length = int(request.GET['length'])
    objects = objects[start: (start + length)]

    # extract information
    detalle = u'''<u>SALDO</u>: <strong>%(saldo)s</strong><br>
                   <u>Información fiscal</u>:  Condición IVA: %(get_cond_iva_display())s - IIBB: %(codigo_ingresos_brutos)s<br>
                   <u>Dirección</u>: %(direccion)s, %(localidad)s (%(get_provincia_display())s) -- CP: %(codigo_postal)s<br>
                   <u>Contacto</u>:  TE: %(telefono)s  FAX: %(fax)s<br>
                   </u>Información extra</u>:<br>
                   %(notas)s'''
    data = make_data(objects, list_display, 'editarCliente', 'suspenderCliente', 'habilitarCliente', detalle)

    # define response
    response = {
        'data': data,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'draw': request.GET['draw']
    }

    # serialize to json
    s = StringIO()
    json.dump(response, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_clientes_search(request):
    clientes = Cliente.objects.filter(razon_social__icontains=request.GET["search"])
    clie = []
    for cliente in clientes:
        clie.append({"ret": cliente.razon_social, "pk": cliente.pk})

    # serialize to json
    s = StringIO()
    json.dump(clie, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_comprobante_info(request):
    tipo_comprobante = request.GET['tipo']
    if ES_MONOTRIBUTO:
        tipo_comprobante += 'C'
        letra = 'c'
    else:
        cliente = Cliente.objects.get(pk=request.GET['id_cliente'])
        if cliente.cond_iva == 'RI':
            tipo_comprobante += 'A'
            letra = 'a'
        else:
            tipo_comprobante += 'B'
            letra = 'b'

    list_comprob = Venta.objects.filter(tipo__exact=tipo_comprobante, aprobado__exact=True).order_by('-numero')
    if len(list_comprob) != 0:
        numero = list_comprob[0].numero + 1
    else:
        numero = 1

    if tipo_comprobante == "FAA":
        info = "Factura A  /  %s - %s" % (str(PUNTO_VENTA_FAA).rjust(4, "0"), str(numero).rjust(8, "0"))
    if tipo_comprobante == "FAB":
        info = "Factura B  /  %s - %s" % (str(PUNTO_VENTA_FAB).rjust(4, "0"), str(numero).rjust(8, "0"))
    if tipo_comprobante == "FAC":
        info = "Factura C  /  %s - %s" % (str(PUNTO_VENTA_FAA).rjust(4, "0"), str(numero).rjust(8, "0"))
    if tipo_comprobante == "NCA":
        info = "Nota de crédito A  /  %s - %s" % (str(PUNTO_VENTA_NCA).rjust(4, "0"), str(numero).rjust(8, "0"))
    if tipo_comprobante == "NCB":
        info = "Nota de crédito B  /  %s - %s" % (str(PUNTO_VENTA_NCB).rjust(4, "0"), str(numero).rjust(8, "0"))
    if tipo_comprobante == "NCC":
        info = "Nota de crédito C  /  %s - %s" % (str(PUNTO_VENTA_NCB).rjust(4, "0"), str(numero).rjust(8, "0"))
    if tipo_comprobante == "NDA":
        info = "Nota de débito B  /  %s - %s" % (str(PUNTO_VENTA_NDA).rjust(4, "0"), str(numero).rjust(8, "0"))
    if tipo_comprobante == "NDB":
        info = "Nota de débito B  /  %s - %s" % (str(PUNTO_VENTA_NDB).rjust(4, "0"), str(numero).rjust(8, "0"))
    if tipo_comprobante == "NDC":
        info = "Nota de débito C  /  %s - %s" % (str(PUNTO_VENTA_NDB).rjust(4, "0"), str(numero).rjust(8, "0"))

    resp = {'info': info, 'letra': letra}

    s = StringIO()
    json.dump(resp, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_posibles_comprobantes_relacionados(request):
    cliente = Cliente.objects.get(pk=request.GET['id_cliente'])
    posibles_comprobantes_relacionados = Venta.objects.filter(cliente=cliente, aprobado=True, pagado=False).order_by(
        '-fecha', '-pk')
    pcr = []
    for comp in posibles_comprobantes_relacionados:
        pcr.append({'pk': comp.pk, 'info_comprobante': comp.pto_vta_num_full, 'total': comp.total})

    s = StringIO()
    json.dump(pcr, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_articulos_almacenados_search(request):
    print request.GET
    cod = Q(codigo__icontains=request.GET["search"])
    codfab = Q(codigo_fabrica__icontains=request.GET["search"])
    den = Q(denominacion__icontains=request.GET["search"])
    aas = Articulo.objects.filter(cod | codfab | den)[0:10]
    aass = []
    for aa in aas:
        precio = Decimal(aa.precio_venta)
        es_b = True if request.GET.get("es_b", "false") == u'true' else False
        if es_b == True:
            iva_articulo = ""
            if aa.iva:
                iva_articulo = aa.iva
            elif aa.subrubro.iva:
                iva_articulo = aa.subrubro.iva
            else:
                iva_articulo = aa.subrubro.rubro.iva

            if iva_articulo == "IVA21":
                precio *= Decimal(1.21)
            if iva_articulo == "IV105":
                precio *= Decimal(1.105)
            if iva_articulo == "IVA27":
                precio *= Decimal(1.27)
        aass.append({"aa": "%s / %s: %s" % (aa.codigo, aa.codigo_fabrica, aa.denominacion), "pk": aa.pk,
                     "precio": "%.2f" % precio, "alicuota": aa.alicuota_iva()})

    # serialize to json
    s = StringIO()
    json.dump(aass, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_ventas_table(request):
    objects = Venta.objects.all()
    print objects
    list_display = ['fecha', 'info_completa', 'cliente.razon_social', 'estado()']
    list_global_search = ['numero', 'cliente__razon_social']
    data_struct = dict(enumerate(['fecha']))

    # Cuenta total de articulos:
    recordsTotal = objects.count()

    # Filtrado general de los articulos
    objects = filtering(request.GET, objects, data_struct, list_global_search)
    print objects

    # Ordenado
    objects = ordering(request.GET, objects, data_struct)
    print objects

    # Conteo de articulos despues dle filtrado
    recordsFiltered = objects.count()

    # finally, slice according to length sent by dataTables:
    start = int(request.GET['start'])
    length = int(request.GET['length'])
    objects = objects[start: (start + length)]

    #actions = []
    # actions.append(ApiTableActions(name='BorrarVenta',url='borrarVenta',icon='delete', cond='aprobado'))
    url_delete = "borrarVenta"
    url_aprobar = "aprobarVenta"
    url_obtener = "obtenerComprobante"

    # extract information
    data = []
    print objects
    for obj in objects:
        row = map(lambda field: _getattr_foreingkey(obj, field), list_display)
        if not obj.aprobado:
            row.append('<a class="aprobar" href="%s"><i class="material-icons">done_all</i></a>' % reverse(url_aprobar, args=[obj.pk]))
            row.append('<a href="%s"><i class="material-icons">delete</i></a>' % reverse(url_delete, args=[obj.pk]))
            row.append('<a class="obtener" href="%s" style="pointer-events: none;"><i class="material-icons">print</i></a>' % reverse(url_obtener, args=[obj.pk]))
        else:
            row.append('<a href="%s" style="pointer-events: none;"><i class="material-icons">done_all</i></a>' % reverse(url_aprobar, args=[obj.pk]))
            row.append('<a href="%s" style="pointer-events: none;"><i class="material-icons">delete</i></a>' % reverse(url_delete, args=[obj.pk]))
            row.append('<a class="obtener" href="%s"><i class="material-icons">print</i></a>' % reverse(url_obtener, args=[obj.pk]))
        data.append(row)

    # define response
    response = {
        'data': data,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'draw': request.GET['draw']
    }

    # serialize to json
    s = StringIO()
    json.dump(response, s)
    s.seek(0)
    return HttpResponse(s.read())

def cobros___get_cobros_table(request):
    objects = Recibo.objects.all()
    list_display = ['fecha_dd_mm_aaaa()', 'numero_full', 'cliente.razon_social', 'total_str']
    list_global_search = ['numero', 'cliente__razon_social']
    data_struct = {0: 'fecha', 1: 'numero_full', 2: 'cliente__razon_social', 4: 'total_str'}

    # Cuenta total de articulos:
    recordsTotal = objects.count()

    # Filtrado de los articulos
    objects = filtering(request.GET, objects, data_struct, list_global_search)

    # Ordenado
    objects = ordering(request.GET, objects, data_struct)

    # Conteo de articulos despues dle filtrado
    recordsFiltered = objects.count()

    # finally, slice according to length sent by dataTables:
    start = int(request.GET['start'])
    length = int(request.GET['length'])
    objects = objects[start: (start + length)]

    data = []
    for obj in objects:
        row = map(lambda field: _getattr_foreingkey(obj, field), list_display)
        detalle_pago = Detalle_cobro.objects.filter(recibo=obj)
        det = ""
        for detalle in detalle_pago:
            det = det + "%s<br>" % detalle.venta
        row.insert(3, det)
        ops = '<a class="imprimirRecibo" href="%s">IMPRIMIR</a>' % (reverse_lazy('imprimirRecibo', args=[obj.pk]))
        row.append(ops)
        data.append(row)
    # define response
    response = {
        'data': data,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'draw': request.GET['draw']
    }
    return JsonResponse(response)


def cobros___get_facturas_pendiente_pago(request, cliente):
    cli = Cliente.objects.get(pk=cliente)
    vtas = Venta.objects.filter(cliente=cli, pagado=False)
    data = serializers.serialize("json", vtas, fields=('fecha', 'total', 'punto_venta', 'numero', 'saldo'))

    # data = serializers.serialize("json", vtas, fields=('fecha', 'total', 'punto_venta', 'numero'), extras=('saldo',))
    return HttpResponse(data, content_type="text/json")

def cobros___get_datos_defecto_cheque(request, cliente):
    cliente = Cliente.objects.get(id=cliente)
    defe={'razon_social':cliente.razon_social,'cuit':cliente.cuit,'paguese_a':RAZON_SOCIAL_EMPRESA,'fecha':datetime.date.today().strftime("%d/%m/%Y")}
    s = StringIO()
    json.dump(defe,s)
    s.seek(0)
    return HttpResponse(s.read())

def cobros___get_credito_valores(request, cliente):
    cliente = Cliente.objects.get(id=cliente)
    for rec in cliente.recibo_set.all():
        for valor in rec.dinero_set.all():
            try:
                if valor.pendiente_para_recibo > 0.009:
                    #obj = {'num_cheque':valor.chequetercero.numero, 'pendiente':'%.2f' %valor.chequetercero.pendiente_para_recibo}
                    obj = {'pendiente':'%.2f' %valor.pendiente_para_recibo}
                    s = StringIO()
                    json.dump(obj,s)
                    s.seek(0)
                    return HttpResponse(s.read())
            except Dinero.DoesNotExist:
                continue
    return HttpResponse()

def get_num_recibo(request):
    list_recibo = Recibo.objects.all().order_by('-numero')
    if len(list_recibo) != 0:
        return HttpResponse(list_recibo[0].numero + 1)
    else:
        return HttpResponse(1)