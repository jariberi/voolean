# -*- coding: utf-8 -*-

from StringIO import StringIO
from decimal import Decimal
import json
import re

import datetime
from django.core.urlresolvers import reverse
from django.db.models.query_utils import Q
from django.http.response import HttpResponse
from core.models import Bancos, Periodo, Transporte, CuentasBanco

__author__ = 'jorge'

class ApiTableActions:
    def __init__(self, name, url, icon, cond=None, attrs=None):
        self.name = name
        self.url = url
        self.icon = icon
        self.cond = cond
        self.attrs = cond

######    FK'S    ######
def get_periodos_fk(request):
    phrase = request.GET['ph']
    bancos_qs = Periodo.objects.filter(Q(ano__icontains=phrase)|Q(mes__icontains=phrase))
    periodos = []
    for periodo in bancos_qs:
        periodos.append({'nombre': periodo.periodo_full, 'pk': periodo.pk})
    s = StringIO()
    json.dump(periodos, s)
    s.seek(0)
    return HttpResponse(s.read())


def get_bancos_fk(request):
    phrase = request.GET['ph']
    bancos_qs = Bancos.objects.filter(nombre__icontains=phrase)
    bancos = []
    for banco in bancos_qs:
        bancos.append({'nombre': banco.nombre, 'pk': banco.pk})
    s = StringIO()
    json.dump(bancos, s)
    s.seek(0)
    return HttpResponse(s.read())


def _getattr_foreingkey(obj, attr):
    pt = attr.count('.')
    if pt == 0:  # No hay clave foranea
        if attr.endswith('()'):
            re = getattr(obj, attr[:-2])()
        else:
            re = getattr(obj, attr)
        if isinstance(re, datetime.date):
            return re.strftime("%d/%m/%Y")
        if isinstance(re, Decimal):
            return "%.2f" % re
        else:
            return re
    else:
        nobj = getattr(obj, attr[:attr.find('.')])
        nattr = attr[attr.find('.') + 1:]
        return _getattr_foreingkey(nobj, nattr)


def filtering(get, dataset, data_struct, global_search):
    """
    :param get: Diccionario GET del request de la vista, para buscar los parametros
    :param dataset: Dataset con la info, normalmente objects.all()
    :param data_struct: Dictionario con la estructura de la tabla {0:'columna_a',1:'columna_b'}
    :param global_search: En que columna debe buscar el termino global
    :return: Dataset filtrado segun los parametros
    """
    # Extraccion de las busquedas indivuales
    individual_searchs_i = {}
    for item in get:
        match = re.match(r'columns\[(\d+)\]\[search\]\[value\]', item)
        if match and get[item]:
            individual_searchs_i[int(match.group(1))] = int(get[item])
    # Filtrado de los datos
    search = get['search[value]']
    queries_g = []
    for item in global_search:
        queries_g.append(Q(**{item + '__icontains': search}))
    print queries_g
    qs = reduce(lambda x, y: x | y, queries_g)
    queries_i = []
    for k, v in individual_searchs_i.iteritems():
        if v == 'false':
            queries_i.append(Q(**{data_struct[k]: False}))
        if v == 'true':
            queries_i.append(Q(**{data_struct[k]: True}))
        else:
            queries_i.append(Q(**{data_struct[k] + '__icontains': v}))
    if individual_searchs_i:
        qi = reduce(lambda x, y: x & y, queries_i)
        qs = qs | qi
    return dataset.filter(qs)


def ordering(get, dataset, data_struct):
    individual_orders = {}
    for item in get:
        match_dir = re.match(r'order\[(\d+)\]\[dir\]', item)
        match_col = re.match(r'order\[(\d+)\]\[column\]', item)
        if match_dir or match_col and get[item]:
            if match_dir:
                i = int(match_dir.group(1))
                if i not in individual_orders:
                    individual_orders[i] = ['', '']
                individual_orders[i][0] = get[item]
            if match_col:
                i = int(match_col.group(1))
                if i not in individual_orders:
                    individual_orders[i] = ['', '']
                individual_orders[i][1] = get[item]
    dirs = {'asc': '', 'desc': '-'}
    ordering = []
    for k, order in individual_orders.iteritems():
        ordering.append(dirs[order[0]] + data_struct[int(order[1])])
    ordering = tuple(ordering)
    return dataset.order_by(*ordering)


def make_data(dataset, list_display, url_modif=None, url_hab=None, url_suspen=None, detalle=None):
    """
    :param dataset: Dataset con la info, normalmente objects.all()
    :param list_display:
    :param actions: Array de objetos tipo ApiActions
    :return: Datos en Array
    """
    data = []
    for obj in dataset:
        row = map(lambda field: _getattr_foreingkey(obj, field), list_display)
        if url_modif:
            row.append(
                '<a class="mdl-button mdl-js-button mdl-button--icon mdl-button--colored" href="%s"><i class="material-icons">mode_edit</i></a>' % reverse(
                    url_modif, args=[obj.pk]))
        if url_suspen and url_hab:
            if obj.suspendido:
                row.append(
                    '<a class="mdl-button mdl-js-button mdl-button--icon mdl-button--colored" href="%s"><i class="material-icons">keyboard_arrow_up</i></a>' % reverse(
                        url_hab,
                        args=[obj.pk]))
            else:
                row.append(
                    '<a class="mdl-button mdl-js-button mdl-button--icon mdl-button--colored" href="%s"><i class="material-icons">keyboard_arrow_down</i></a>' % reverse(
                        url_suspen,
                        args=[
                            obj.pk]))
        if detalle:
            real_detail = {}
            for field in re.findall(r'%\((\w+\(*\)*)\)s', detalle):
                real_detail[field] = getattr(obj, field[:-2])() if field.endswith("()") else getattr(obj, field)
            deta = detalle % real_detail
            row.insert(0, deta)
        data.append(row)
    return data


def get_bancos_table(request):
    # SETEOS INICIALES
    objects = Bancos.objects.all()
    list_display = ['nombre']
    list_global_search = list_display
    data_struct = {0: 'nombre'}

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
    data = make_data(objects, list_display, "editarBanco", "suspenderBanco", "habilitarBanco")
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


def get_periodos_table(request):
    objects = Periodo.objects.all()
    list_display = ['ano', 'mes_display']
    list_global_search = ['ano', 'mes']
    data_struct = {0: 'ano', 1: 'mes'}

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
    data = make_data(objects, list_display)

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


def get_transportes_table(request):
    objects = Transporte.objects.all()
    list_display = ['nombre', 'direccion', 'localidad', 'telefono']
    list_global_search = ['nombre']
    data_struct = {0: 'nombre', 1: 'direccion', 2: 'localidad', 3: 'telefono'}

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

    data = make_data(objects, list_display, 'editarTransporte', 'suspenderTransporte', 'habilitarTransporte')
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


def get_cuentabancaria_table(request):
    objects = CuentasBanco.objects.all()
    list_display = ['cbu', 'banco.nombre']
    list_global_search = ['cbu', 'banco__nombre']
    data_struct = {0: 'cbu', 1: 'banco__nombre'}

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

    data = make_data(objects, list_display, 'editarCuentaBancaria', 'suspenderCuentaBancaria',
                     'habilitarCuentaBancaria')
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
