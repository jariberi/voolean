from StringIO import StringIO
from decimal import Decimal
import json
import re
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.http.response import HttpResponse, JsonResponse
from django.utils.datetime_safe import date
from compras.models import Proveedor, Compra, Condicion_compra
from core.api import filtering, ordering, make_data, _getattr_foreingkey
from core.models import Bancos, Periodo, Transporte, CuentasBanco
from ventas.models import Articulo

__author__ = 'jorge'


def get_proveedores_fk(request):
    phrase = request.GET['ph']
    proveedores_qs = Proveedor.objects.filter(razon_social__icontains=phrase)
    proveedores = []
    for proveedor in proveedores_qs:
        proveedores.append({'razon_social': proveedor.razon_social, 'pk': proveedor.pk})
    s = StringIO()
    json.dump(proveedores, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_condiciones_compra_fk(request):
    phrase = request.GET['ph']
    cond_comp_qs = Condicion_compra.objects.filter(descripcion__icontains=phrase)
    cond_comp = []
    for con_comp in cond_comp_qs:
        cond_comp.append({'condicion': con_comp.descripcion, 'pk': con_comp.pk})
    s = StringIO()
    json.dump(cond_comp, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_proveedores_table(request):
    # SETEOS INICIALES
    objects = Proveedor.objects.all()
    list_display = ['razon_social', 'localidad', 'telefono', 'email']
    list_global_search = ['razon_social']
    data_struct = dict(enumerate(list_display))

    # Cuenta total de articulos:
    recordsTotal = objects.count()

    # Filtrado de los bancos
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
    data = make_data(objects, list_display, "editarProveedor", "suspenderProveedor", "habilitarProveedor")
    print data
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


def get_compras_table(request):
    objects = Compra.objects.all()
    list_display = ['fecha', 'tipo', 'identificador', 'proveedor.razon_social', 'neto', 'iva', 'total', 'estado']
    list_global_search = ['proveedor__razon_social', 'numero']
    data_struct = dict(enumerate(map(lambda x: x.replace(".", "__"), list_display)))

    recordsTotal = objects.count()

    objects = filtering(request.GET, objects, data_struct, list_global_search)

    objects = ordering(request.GET, objects, data_struct)

    recordsFiltered = objects.count()

    # finally, slice according to length sent by dataTables:
    start = int(request.GET['start'])
    length = int(request.GET['length'])
    objects = objects[start: (start + length)]


    # extract information
    data = make_data(objects, list_display)

    # define response
    response = {
        'data': data,
        'recordsTotal': recordsTotal,
        'recordsFiltered': recordsFiltered,
        'draw': request.GET['draw']
    }

    return JsonResponse(response)
