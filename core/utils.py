#! /usr/bin/env python
# -*- coding: utf-8 -*-
from django.utils.timezone import now

from afip_ws.models import AFIP_Datos_Autenticacion
from afip_ws.wsaa import WSAA
from voolean.settings import PUNTO_VENTA_FAA, PUNTO_VENTA_FAB, PUNTO_VENTA_NCA, \
    PUNTO_VENTA_NCB, PUNTO_VENTA_NDA, PUNTO_VENTA_NDB, PUNTO_VENTA_FAC, PUNTO_VENTA_NCC, PUNTO_VENTA_NDC, \
    CERT_FILE_TEST, \
    PRIVATE_KEY_FILE
from ventas.models import Venta, Recibo


def get_pto_vta(venta):
    if venta.tipo == "FAA":
        return PUNTO_VENTA_FAA
    elif venta.tipo == "FAB":
        return PUNTO_VENTA_FAB
    elif venta.tipo == "FAC":
        return PUNTO_VENTA_FAC
    elif venta.tipo == "NCA":
        return PUNTO_VENTA_NCA
    elif venta.tipo == "NCB":
        return PUNTO_VENTA_NCB
    elif venta.tipo == "NCC":
        return PUNTO_VENTA_NCC
    elif venta.tipo == "NDA":
        return PUNTO_VENTA_NDA
    elif venta.tipo == "NDB":
        return PUNTO_VENTA_NDB
    elif venta.tipo == "NDC":
        return PUNTO_VENTA_NDC


def get_num_comp(venta):
    list_comprob = Venta.objects.filter(tipo=venta.tipo, aprobado__exact=True).order_by('-numero')
    if len(list_comprob) != 0:
        return list_comprob[0].numero + 1
    else:
        return 1


def get_tipo_comp_afip(venta):
    if venta.tipo == "FAA":
        return 1
    elif venta.tipo == "FAB":
        return 6
    elif venta.tipo == "NCA":
        return 3
    elif venta.tipo == "NCB":
        return 8
    elif venta.tipo == "NDA":
        return 2
    elif venta.tipo == "NDB":
        return 7
    elif venta.tipo == "FAC":
        return 11
    elif venta.tipo == "NCC":
        return 13
    elif venta.tipo == "NDC":
        return 12


# def get_num_orden_pago():
#     list_orden_pago = OrdenPago.objects.all().order_by('-numero')
#     if len(list_orden_pago) != 0:
#         return list_orden_pago[0].numero + 1
#     else:
#         return 1


def getattr_foreingkey(obj, attr):
    pt = attr.count('.')
    if pt == 0:  # No hay clave foranea
        return getattr(obj, attr)
    else:
        nobj = getattr(obj, attr[:attr.find('.')])
        nattr = attr[attr.find('.') + 1:]
        getattr(nobj, nattr)


'''
Utilidad para convertir de numero a letra
Extraido de: https://github.com/AxiaCore/numero-a-letras/tree/master/python
Andres Cardenas
'''

from itertools import ifilter

UNIDADES = (
    '',
    'UN ',
    'DOS ',
    'TRES ',
    'CUATRO ',
    'CINCO ',
    'SEIS ',
    'SIETE ',
    'OCHO ',
    'NUEVE ',
    'DIEZ ',
    'ONCE ',
    'DOCE ',
    'TRECE ',
    'CATORCE ',
    'QUINCE ',
    'DIECISEIS ',
    'DIECISIETE ',
    'DIECIOCHO ',
    'DIECINUEVE ',
    'VEINTE '
)

DECENAS = (
    'VENTI',
    'TREINTA ',
    'CUARENTA ',
    'CINCUENTA ',
    'SESENTA ',
    'SETENTA ',
    'OCHENTA ',
    'NOVENTA ',
    'CIEN '
)

CENTENAS = (
    'CIENTO ',
    'DOSCIENTOS ',
    'TRESCIENTOS ',
    'CUATROCIENTOS ',
    'QUINIENTOS ',
    'SEISCIENTOS ',
    'SETECIENTOS ',
    'OCHOCIENTOS ',
    'NOVECIENTOS '
)

MONEDAS = (
    {'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS',
     'symbol': u'$'},
    {'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
    {'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
    {'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS',
     'symbol': u'$'},
    {'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL', 'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
    {'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
)


# Para definir la moneda me estoy basando en los código que establece el ISO 4217
# Decidí poner las variables en inglés, porque es más sencillo de ubicarlas sin importar el país
# Si, ya sé que Europa no es un país, pero no se me ocurrió un nombre mejor para la clave.


def to_word(number, mi_moneda=None):
    if mi_moneda != None:
        try:
            moneda = ifilter(lambda x: x['currency'] == mi_moneda, MONEDAS).next()
            if number < 2:
                moneda = moneda['singular']
            else:
                moneda = moneda['plural']
        except:
            return "Tipo de moneda inválida"
    else:
        moneda = ""
    """Converts a number into string representation"""
    converted = ''

    if not (0 < number < 999999999):
        return 'No es posible convertir el numero a letras'

    number_str = str(number).zfill(9)
    millones = number_str[:3]
    miles = number_str[3:6]
    cientos = number_str[6:]

    if (millones):
        if (millones == '001'):
            converted += 'UN MILLON '
        elif (int(millones) > 0):
            converted += '%sMILLONES ' % __convert_group(millones)

    if (miles):
        if (miles == '001'):
            converted += 'MIL '
        elif (int(miles) > 0):
            converted += '%sMIL ' % __convert_group(miles)

    if (cientos):
        if (cientos == '001'):
            converted += 'UN '
        elif (int(cientos) > 0):
            converted += '%s ' % __convert_group(cientos)

    converted += moneda

    return converted.title()


def __convert_group(n):
    """Turn each group of numbers into letters"""
    output = ''

    if (n == '100'):
        output = "CIEN "
    elif (n[0] != '0'):
        output = CENTENAS[int(n[0]) - 1]

    k = int(n[1:])
    if (k <= 20):
        output += UNIDADES[k]
    else:
        if ((k > 30) & (n[2] != '0')):
            output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
        else:
            output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])

    return output
