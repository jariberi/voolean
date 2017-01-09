# -*- coding: utf-8 -*-
from decimal import Decimal
from django.http.response import HttpResponse
from geraldo import Report, ReportBand, Label, DetailBand

from geraldo.widgets import ObjectValue, SystemField
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import A4
from geraldo.utils import cm, landscape, BAND_WIDTH, FIELD_ACTION_SUM
from geraldo.base import ReportBand
from reportlab.pdfgen.canvas import Canvas

from core.models import Dinero
from core.utils import to_word
from ventas.models import Recibo, Venta, Item_almacenados, Item_personalizados, Item_compuesto
from voolean.settings import RAZON_SOCIAL_EMPRESA, CUIT, DOMICILIO_COMERCIAL, INGRESOS_BRUTOS, INICIO_ACTIVIDADES, \
    CIUDAD, PROVINCIA, CONDICION_IVA, NOMBRE_FANTASIA
from geraldo.graphics import Line, RoundRect
from reportlab.lib.colors import yellow, grey, black


class IVAVentas(Report):
    title = 'LIBRO IVA VENTAS - RESOLUCION GENERAL AFIP 3419'
    page_size = landscape(A4)

    # first_page_number=7

    def __init__(self, queryset=None, fpn=1):
        print "INIT DE REPORTE"
        Report.__init__(self, queryset=queryset)
        self.first_page_number = fpn
        print self.first_page_number

    class band_page_header(ReportBand):
        height = 4 * cm
        elements = [SystemField(expression='%(report_title)s', top=0.1 * cm, left=0, width=BAND_WIDTH,
                                style={'fontName': 'Helvetica-Bold', 'fontSize': 14, 'alignment': TA_CENTER}),
                    Label(text="RAZON SOCIAL: %s" % RAZON_SOCIAL_EMPRESA, top=0.8 * cm, width=BAND_WIDTH,
                          style={'fontName': 'Helvetica', 'fontSize': 10}),
                    Label(text="CUIT: %s" % CUIT, top=1.2 * cm, width=BAND_WIDTH,
                          style={'fontName': 'Helvetica', 'fontSize': 10}),
                    Label(text="DOMICILIO COMERCIAL: %s" % DOMICILIO_COMERCIAL, top=1.5 * cm, width=BAND_WIDTH,
                          style={'fontName': 'Helvetica', 'fontSize': 10}),
                    SystemField(expression='Periodo: %(var:periodo)s', top=1.5 * cm, left=23 * cm,
                                style={'fontName': 'Helvetica', 'fontSize': 10}),
                    SystemField(expression='Fecha emisión: %(now:%d/%m/%Y)s', top=2 * cm, width=8 * cm),
                    SystemField(expression='Folio N°: %(page_number)s', top=2 * cm, left=23 * cm,
                                style={'fontName': 'Helvetica', 'fontSize': 10}),
                    Line(left=0, top=2.7 * cm, right=29.7 * cm, bottom=2.7 * cm),
                    # Encabezado de tabla
                    Label(text="Fecha", top=2.9 * cm, left=0, width=2 * cm,
                          style={'fontName': 'Helvetica-Bold', 'fontSize': 10, 'alignment': TA_CENTER}),
                    Label(text="Comprobante", top=2.9 * cm, left=2.1 * cm, width=3.5 * cm,
                          style={'fontName': 'Helvetica-Bold', 'fontSize': 10, 'alignment': TA_CENTER}),
                    Label(text="Razón Social", top=2.9 * cm, left=5.7 * cm, width=7 * cm,
                          style={'fontName': 'Helvetica-Bold', 'fontSize': 10, 'alignment': TA_CENTER}),
                    Label(text="CUIT", top=2.9 * cm, left=13.7 * cm, width=2.5 * cm,
                          style={'fontName': 'Helvetica-Bold', 'fontSize': 10, 'alignment': TA_CENTER}),
                    Label(text="Imp. Neto", top=2.9 * cm, left=17.2 * cm, width=2 * cm,
                          style={'fontName': 'Helvetica-Bold', 'fontSize': 10, 'alignment': TA_CENTER}),
                    Label(text="IVA(10.5%)", top=2.9 * cm, left=20.2 * cm, width=2 * cm,
                          style={'fontName': 'Helvetica-Bold', 'fontSize': 10, 'alignment': TA_CENTER}),
                    Label(text="IVA(21%)", top=2.9 * cm, left=22.2 * cm, width=2 * cm,
                          style={'fontName': 'Helvetica-Bold', 'fontSize': 10, 'alignment': TA_CENTER}),
                    Label(text="Exento", top=2.9 * cm, left=23.7 * cm, width=2 * cm,
                          style={'fontName': 'Helvetica-Bold', 'fontSize': 10, 'alignment': TA_CENTER}),
                    Label(text="Imp. Total", top=2.9 * cm, left=26 * cm, width=2 * cm,
                          style={'fontName': 'Helvetica-Bold', 'fontSize': 10, 'alignment': TA_CENTER}),
                    Line(left=0, top=3.5 * cm, right=29.7 * cm, bottom=3.5 * cm), ]

    class band_page_footer(ReportBand):
        height = 1 * cm
        elements = [SystemField(expression='Pagina N°: %(page_number)s', top=0.1 * cm, left=0, width=BAND_WIDTH,
                                style={'fontName': 'Helvetica', 'fontSize': 10, 'alignment': TA_CENTER}), ]

    class band_detail(DetailBand):
        height = 0.4 * cm
        elements = [ObjectValue(attribute_name='fecha_dd_mm_aaaa', top=0, left=0, width=2 * cm),
                    ObjectValue(attribute_name='info_completa_informe', top=0, left=2.1 * cm, width=3.5 * cm),
                    ObjectValue(attribute_name='cliente.razon_social', top=0, left=5.7 * cm, width=7 * cm,
                                height=0.4 * cm, truncate_overflow=True),
                    ObjectValue(attribute_name='cliente.cuit', top=0, left=13.7 * cm, width=2.5 * cm),
                    ObjectValue(attribute_name='neto',
                                get_value=lambda instance: "%.2f" % (instance.neto * -1) if instance.tipo.startswith(
                                    "NC") else "%.2f" % instance.neto, \
                                top=0, left=16.9 * cm, width=2 * cm, \
                                style={'alignment': TA_RIGHT}),
                    Label(text="0.00", top=0 * cm, left=19.7 * cm, width=2 * cm, style={'alignment': TA_RIGHT}),
                    ObjectValue(attribute_name='iva21',
                                get_value=lambda instance: "%.2f" % (instance.iva21 * -1) if instance.tipo.startswith(
                                    "NC") else "%.2f" % instance.iva21, \
                                top=0, left=21.4 * cm, width=2 * cm, style={'alignment': TA_RIGHT}),
                    Label(text="0.00", top=0 * cm, left=23.7 * cm, width=2 * cm, style={'alignment': TA_RIGHT}),
                    ObjectValue(attribute_name='total',
                                get_value=lambda instance: "%.2f" % (instance.total * -1) if instance.tipo.startswith(
                                    "NC") else "%.2f" % instance.total, \
                                top=0, left=26 * cm, width=2 * cm, style={'alignment': TA_RIGHT}),
                    ]

    class band_summary(ReportBand):
        margin_top = 3 * cm
        height = 0.5 * cm
        elements = [
            ObjectValue(attribute_name='neto', top=0.1 * cm, left=16.9 * cm, width=2 * cm, \
                        action=FIELD_ACTION_SUM, get_value=lambda instance: float(
                    "%.2f" % (instance.neto * -1) if instance.tipo.startswith("NC") else "%.2f" % instance.neto),
                        style={'alignment': TA_RIGHT}),
            ObjectValue(attribute_name='iva21', top=0.1 * cm, left=21.4 * cm, width=2 * cm, \
                        action=FIELD_ACTION_SUM, get_value=lambda instance: float(
                    "%.2f" % (instance.iva21 * -1) if instance.tipo.startswith("NC") else "%.2f" % instance.iva21),
                        style={'alignment': TA_RIGHT}),
            ObjectValue(attribute_name='total', top=0.1 * cm, left=26 * cm, width=2 * cm, \
                        action=FIELD_ACTION_SUM, get_value=lambda instance: float(
                    "%.2f" % (instance.total * -1) if instance.tipo.startswith("NC") else "%.2f" % instance.total),
                        style={'alignment': TA_RIGHT}), ]
        borders = {'top': Line()}


def impr_recibo(request, pk):
    mitad = 14.8 * cm
    mita = 14.8
    # Inicializo todos los comprobantes y valores
    recibo = Recibo.objects.get(pk=pk)
    a_cuenta = recibo.a_cuenta
    # Datos de comprobantes
    comprobantes = recibo.detalle_cobro_set.all()
    # a_cuenta = recibo.cobranza_a_cuenta_set.all()
    # credito_anterior = recibo.cobranza_credito_anterior_set.all()
    # Datos de valores
    valores = recibo.dinero_set.all()
    # transferencia = recibo.transferenciabancariaentrante_set.all()
    # efectivo = recibo.dinero_set.all()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'filename="somefilename.pdf"'
    p = Canvas(response, pagesize=A4)
    # Numero de recibo
    p.setFont('Helvetica-Bold', 16)
    p.drawString(15.7 * cm, 13 * cm, recibo.numero_full)
    # Fecha
    p.setFont('Helvetica', 13)
    p.drawString(17 * cm, 12 * cm, str(recibo.fecha.day))
    p.drawString(18 * cm, 12 * cm, str(recibo.fecha.month))
    p.drawString(19 * cm, 12 * cm, str(recibo.fecha.year))
    # Datos del cliente
    p.setFont('Helvetica', 13)
    p.drawString(12 * cm, 11 * cm, recibo.cliente.razon_social)
    p.drawString(12 * cm, 10.3 * cm, recibo.cliente.get_cond_iva_display())
    p.drawString(12 * cm, 9.8 * cm, "CUIT: %s" % recibo.cliente.cuit)
    p.drawString(12 * cm, 9.3 * cm, recibo.cliente.direccion)
    p.drawString(12 * cm, 8.8 * cm, "%s - %s" % (recibo.cliente.localidad, recibo.cliente.get_provincia_display()))
    inicio_y = 6.2
    alto_item = 0.4
    i = 0
    p.setFont('Helvetica', 7)
    if a_cuenta and a_cuenta > 0:
        p.drawString(3.4 * cm, (inicio_y - i * alto_item) * cm, "A cuenta")
        p.drawRightString(7.4 * cm, (inicio_y - i * alto_item) * cm, "%.2f" % a_cuenta)
        i += 1
    if recibo.credito_anterior and recibo.credito_anterior > 0:
        p.drawString(3.4 * cm, (inicio_y - i * alto_item) * cm, "Credito anterior")
        p.drawRightString(7.4 * cm, (inicio_y - i * alto_item) * cm, "-%.2f" % recibo.credito_anterior)
        i += 1
    for item in comprobantes:
        p.drawString(2 * cm, (inicio_y - i * alto_item) * cm, item.venta.tipo)
        p.drawString(3.4 * cm, (inicio_y - i * alto_item) * cm, item.venta.num_comp_full())
        p.drawString(5.1 * cm, (inicio_y - i * alto_item) * cm, item.venta.fecha_dd_mm_aaaa())
        p.drawRightString(7.4 * cm, (inicio_y - i * alto_item) * cm, item.monto_2d())
        i += 1
    # Cheques
    i = 0
    for item in valores:
        try:
            p.drawString(10 * cm, (inicio_y - i * alto_item) * cm, item.chequetercero.numero)
            p.drawString(11.7 * cm, (inicio_y - i * alto_item) * cm, item.chequetercero.cuit_titular)
            p.drawString(13.8 * cm, (inicio_y - i * alto_item) * cm, item.chequetercero.fecha_dd_mm_aaaa())
            p.drawString(15.4 * cm, (inicio_y - i * alto_item) * cm, item.chequetercero.banco.nombre[:20])
            p.drawRightString(20 * cm, (inicio_y - i * alto_item) * cm, "%.2f" % item.monto)
        except Dinero.DoesNotExist:
            try:
                item.transferenciabancariaentrante
                p.drawString(10 * cm, (inicio_y - i * alto_item) * cm, "Transferencia Bancaria")
                p.drawRightString(20 * cm, (inicio_y - i * alto_item) * cm, "%.2f" % item.monto)
            except Dinero.DoesNotExist:
                p.drawString(10 * cm, (inicio_y - i * alto_item) * cm,
                             "Efectivo" if item.monto >= 0 else "Efectivo - SU VUELTO")
                p.drawRightString(20 * cm, (inicio_y - i * alto_item) * cm, "%.2f" % item.monto)
        finally:
            i += 1
    # for item in transferencia:
    #    p.drawString(10*cm, (inicio_y-i*alto_item)*cm, "Transferencia Bancaria")
    #    p.drawRightString(20*cm, (inicio_y-i*alto_item)*cm, "%.2f" %item.monto)
    #    i+=1
    # for item in efectivo:
    #    p.drawString(10*cm, (inicio_y-i*alto_item)*cm, "Efectivo")
    #    p.drawRightString(20*cm, (inicio_y-i*alto_item)*cm, "%.2f" %item.monto)
    #    i+=1
    p.setFont('Helvetica-Bold', 12)
    p.drawString(7.5 * cm, 2.3 * cm, recibo.total_str)
    p.drawString(18 * cm, 2.3 * cm, recibo.total_str)
    try:
        letra = (to_word(int(recibo.total_str.split('.')[0].strip())) + "con " + to_word(
            int(recibo.total_str.split('.')[1].strip())) + "centavos").lower()
    except IndexError:
        letra = (to_word(int(recibo.total_str.split('.')[0].strip()))).lower()
    p.setFont('Helvetica', 9)
    p.drawString(2 * cm, 7.5 * cm, letra)
    ######################################################
    ##############RECIBO DUPLICADO########################
    ######################################################
    # Numero de recibo
    p.setFont('Helvetica-Bold', 16)
    p.drawString(15.7 * cm, mitad + 13 * cm, recibo.numero_full)
    # Fecha
    p.setFont('Helvetica', 13)
    p.drawString(17 * cm, mitad + 12 * cm, str(recibo.fecha.day))
    p.drawString(18 * cm, mitad + 12 * cm, str(recibo.fecha.month))
    p.drawString(19 * cm, mitad + 12 * cm, str(recibo.fecha.year))
    # Datos del cliente
    p.setFont('Helvetica', 13)
    p.drawString(12 * cm, mitad + 11 * cm, recibo.cliente.razon_social)
    p.drawString(12 * cm, mitad + 10.3 * cm, recibo.cliente.get_cond_iva_display())
    p.drawString(12 * cm, mitad + 9.8 * cm, "CUIT: %s" % recibo.cliente.cuit)
    p.drawString(12 * cm, mitad + 9.3 * cm, recibo.cliente.direccion)
    p.drawString(12 * cm, mitad + 8.8 * cm,
                 "%s - %s" % (recibo.cliente.localidad, recibo.cliente.get_provincia_display()))
    # Datos de comprobantes
    # comprobantes = recibo.detalle_cobro_set.all()
    inicio_y = mita + 6.2
    alto_item = 0.4
    i = 0
    p.setFont('Helvetica', 7)
    if a_cuenta and a_cuenta > 0:
        p.drawString(3.4 * cm, (inicio_y - i * alto_item) * cm, "A cuenta")
        p.drawRightString(7.4 * cm, (inicio_y - i * alto_item) * cm, "%.2f" % a_cuenta)
        i += 1
    if recibo.credito_anterior and recibo.credito_anterior > 0:
        p.drawString(3.4 * cm, (inicio_y - i * alto_item) * cm, "Credito anterior")
        p.drawRightString(7.4 * cm, (inicio_y - i * alto_item) * cm, "-%.2f" % recibo.credito_anterior)
        i += 1
    for item in comprobantes:
        p.drawString(2 * cm, (inicio_y - i * alto_item) * cm, item.venta.tipo)
        p.drawString(3.4 * cm, (inicio_y - i * alto_item) * cm, item.venta.num_comp_full())
        p.drawString(5.1 * cm, (inicio_y - i * alto_item) * cm, item.venta.fecha_dd_mm_aaaa())
        p.drawRightString(7.4 * cm, (inicio_y - i * alto_item) * cm, item.monto_2d())
        i += 1
    i = 0
    for item in valores:
        try:
            p.drawString(10 * cm, (inicio_y - i * alto_item) * cm, item.chequetercero.numero)
            p.drawString(11.7 * cm, (inicio_y - i * alto_item) * cm, item.chequetercero.cuit_titular)
            p.drawString(13.8 * cm, (inicio_y - i * alto_item) * cm, item.chequetercero.fecha_dd_mm_aaaa())
            p.drawString(15.4 * cm, (inicio_y - i * alto_item) * cm, item.chequetercero.banco.nombre[:20])
            p.drawRightString(20 * cm, (inicio_y - i * alto_item) * cm, "%.2f" % item.monto)
        except Dinero.DoesNotExist:
            try:
                item.transferenciabancariaentrante
                p.drawString(10 * cm, (inicio_y - i * alto_item) * cm, "Transferencia Bancaria")
                p.drawRightString(20 * cm, (inicio_y - i * alto_item) * cm, "%.2f" % item.monto)
            except Dinero.DoesNotExist:
                p.drawString(10 * cm, (inicio_y - i * alto_item) * cm,
                             "Efectivo" if item.monto >= 0 else "Efectivo - SU VUELTO")
                p.drawRightString(20 * cm, (inicio_y - i * alto_item) * cm, "%.2f" % item.monto)
        finally:
            i += 1
    p.setFont('Helvetica-Bold', 12)
    p.drawString(7.5 * cm, mitad + 2.3 * cm, recibo.total_str)
    p.drawString(18 * cm, mitad + 2.3 * cm, recibo.total_str)
    try:
        letra = (to_word(int(recibo.total_str.split('.')[0].strip())) + "con " + to_word(
            int(recibo.total_str.split('.')[1].strip())) + "centavos").lower()
    except IndexError:
        letra = (to_word(int(recibo.total_str.split('.')[0].strip()))).lower()
    p.setFont('Helvetica', 9)
    p.drawString(2 * cm, mitad + 7.5 * cm, letra)
    p.showPage()
    p.save()
    return response


def obtener_comprobante(request, pk):
    def ycm(cm):
        return 29.7 - cm

    def comprobante(p):
        # Lineas del encabezado
        p.setLineWidth(0.01 * cm)
        # Cuadro horizonal superior: tipo de comprobante y datos del mismo
        p.rect(0.7 * cm, ycm(5.8) * cm, 19.6 * cm, 5 * cm)
        p.line(0.7 * cm, ycm(1.8) * cm, 20.3 * cm, ycm(1.8) * cm)  # Primer linea horizontal
        p.rect(9.7 * cm, ycm(3.1) * cm, 1.6 * cm, 1.3 * cm)  # Cuadro letra y codigo de comprobante
        p.line(10.5 * cm, ycm(3.1) * cm, 10.5 * cm, ycm(5.8) * cm)
        # p.line(20.3 * cm, ycm(0.8) * cm, 20.3 * cm, ycm(5) * cm)
        p.setFont('Helvetica-Bold', 20)
        p.drawCentredString(10.5 * cm, ycm(2.6) * cm, venta.tipo[-1:])
        # Recuadro izquierda
        p.setFont('Helvetica-Bold', 16)
        rz_split = NOMBRE_FANTASIA.split(" ")
        pal_sum = 0
        linea_1 = linea_2 = ""
        for pal in rz_split:
            pal_sum += len(pal)
            if pal_sum <= 20:
                linea_1 += pal + " "
            else:
                linea_2 += pal + " "
        p.drawCentredString(5 * cm, ycm(2.5) * cm, linea_1[:-1])
        p.drawCentredString(5 * cm, ycm(3) * cm, linea_2[:-1])
        p.setFont('Helvetica', 11)
        p.drawString(0.9 * cm, ycm(4.2) * cm, RAZON_SOCIAL_EMPRESA)
        p.drawString(0.9 * cm, ycm(4.7) * cm, DOMICILIO_COMERCIAL + " - " + CIUDAD + ", " + PROVINCIA)
        p.drawCentredString(5.4 * cm, ycm(5.5) * cm, CONDICION_IVA)
        # Recuadro derecha
        p.setFont('Helvetica-Bold', 16)
        if venta.tipo[:2] == 'FA':
            p.drawString(12 * cm, ycm(2.6) * cm, 'FACTURA')
        elif venta.tipo[:2] == 'NC':
            p.drawString(12 * cm, ycm(2.6) * cm, 'NOTA DE CREDITO')
        elif venta.tipo[:2] == 'ND':
            p.drawString(12 * cm, ycm(2.6) * cm, 'NOTA DE DEBITO')
        p.setFont('Helvetica', 15)
        p.drawString(12 * cm, ycm(3.2) * cm, "%s - %s" % (venta.pto_vta_full(), venta.num_comp_full()))
        p.drawString(12 * cm, ycm(3.8) * cm, venta.fecha_dd_mm_aaaa())
        p.setFont('Helvetica', 10)
        p.drawString(12 * cm, ycm(4.8) * cm, "CUIT: %s" % CUIT)  # CUIT
        p.drawString(12 * cm, ycm(5.2) * cm, "Ingresos Brutos: %s" % INGRESOS_BRUTOS)  # Ingresos Brutos
        p.drawString(12 * cm, ycm(5.6) * cm, "Inicio Actividades: %s" % INICIO_ACTIVIDADES)  # Inicio Actividades
        # Cuadro cliente
        p.rect(0.7 * cm, ycm(8.1) * cm, 19.6 * cm, 2.2 * cm)
        p.setFont('Helvetica-Bold', 10)
        p.drawString(0.9 * cm, ycm(6.5) * cm, "CLIENTE:")
        p.setFont('Helvetica', 11)
        p.drawString(2.9 * cm, ycm(6.5) * cm, str(venta.cliente.id))
        p.drawString(4.2 * cm, ycm(6.5) * cm, venta.cliente.razon_social)
        p.drawString(13 * cm, ycm(6.5) * cm, "CUIT:  " + venta.cliente.cuit)  # CUIT
        p.setFont('Helvetica-Bold', 10)
        p.drawString(0.9 * cm, ycm(7.2) * cm, "DOMICILIO:")
        p.setFont('Helvetica', 10)
        p.drawString(3 * cm, ycm(7.2) * cm, "%s - %s, %s" % (
            venta.cliente.direccion, venta.cliente.localidad, venta.cliente.get_provincia_display()))
        p.setFont('Helvetica-Bold', 10)
        p.drawString(0.9 * cm, ycm(7.8) * cm, "COND. IVA:")
        p.setFont('Helvetica', 10)
        p.drawString(3 * cm, ycm(7.8) * cm, venta.cliente.get_cond_iva_display())
        p.setFont('Helvetica-Bold', 11)
        p.drawString(9.9 * cm, ycm(7.8) * cm, "COND. DE VENTA:")
        p.setFont('Helvetica', 10)
        p.drawString(13.9 * cm, ycm(7.8) * cm, venta.condicion_venta.descripcion)
        # Encabezado detalle factura
        p.setFillGray(0.80)
        p.rect(0.7 * cm, ycm(9.1) * cm, 19.6 * cm, 0.7 * cm, fill=1)
        p.setFillGray(0)
        p.setFont('Helvetica', 9)
        p.drawCentredString(1.6 * cm, ycm(8.9) * cm, "Código")
        p.line(2.5 * cm, ycm(8.4) * cm, 2.5 * cm, ycm(9.1) * cm)  # Fin Codigo
        p.drawCentredString(5.45 * cm, ycm(8.9) * cm, "Producto/Servicio")
        p.line(8.4 * cm, ycm(8.4) * cm, 8.4 * cm, ycm(9.1) * cm)  # Fin producto/servicio
        p.drawCentredString(9.4 * cm, ycm(8.9) * cm, "Cantidad")
        p.line(10.4 * cm, ycm(8.4) * cm, 10.4 * cm, ycm(9.1) * cm)  # Fin cantidad
        p.drawCentredString(11.1 * cm, ycm(8.9) * cm, "U. medida")
        p.line(11.8 * cm, ycm(8.4) * cm, 11.8 * cm, ycm(9.1) * cm)  # Fin unidad medida
        p.drawCentredString(13.05 * cm, ycm(8.9) * cm, "P. unitario")
        p.line(14.3 * cm, ycm(8.4) * cm, 14.3 * cm, ycm(9.1) * cm)  # Fin precio unitario
        p.drawCentredString(14.8 * cm, ycm(8.9) * cm, "% Bon.")
        p.line(15.3 * cm, ycm(8.4) * cm, 15.3 * cm, ycm(9.1) * cm)  # Fin % descuento
        p.drawCentredString(16.55 * cm, ycm(8.9) * cm, "Imp.Bonif")
        p.line(17.8 * cm, ycm(8.4) * cm, 17.8 * cm, ycm(9.1) * cm)  # Fin descuento
        p.drawCentredString(19.05 * cm, ycm(8.9) * cm, "Subtotal")
        detalle = venta.items_set()
        inicio_y = 20
        alto_item = 0.4
        p.setFont('Helvetica', 8)
        for i, item in enumerate(detalle):
            if isinstance(item, Item_almacenados):
                p.drawString(0.9 * cm, (inicio_y - i * alto_item) * cm, str(item.articulo.codigo))
                p.drawString(2.7 * cm, (inicio_y - i * alto_item) * cm, item.articulo.denominacion[:45])
                p.drawRightString(10.2 * cm, (inicio_y - i * alto_item) * cm, "%.2f" % item.cantidad)
                p.drawString(10.5 * cm, (inicio_y - i * alto_item) * cm, item.articulo.get_unidad_medida_display())
                p.drawRightString(14.1 * cm, (inicio_y - i * alto_item) * cm, item.articulo.precio_venta if venta.tipo[
                                                                                                            -1:] == 'A' else item.articulo.precio_venta_iva_inc)
                p.drawRightString(15.1 * cm, (inicio_y - i * alto_item) * cm, "%.2f%%" % item.descuento)
                p.drawRightString(17.6 * cm, (inicio_y - i * alto_item) * cm, "-%.2f" % item.descuento_value())
                p.drawRightString(20.1 * cm, (inicio_y - i * alto_item) * cm, "%.2f" % item.subtotal())
            if isinstance(item, Item_personalizados):
                # p.drawString(0.9 * cm, (inicio_y - i * alto_item) * cm, str(item.articulo.codigo))
                p.drawString(2.7 * cm, (inicio_y - i * alto_item) * cm, item.descripcion[:45])
                p.drawRightString(10.2 * cm, (inicio_y - i * alto_item) * cm, "%.2f" % item.cantidad)
                # p.drawString(10.5 * cm, (inicio_y - i * alto_item) * cm, item.articulo.get_unidad_medida_display())
                p.drawRightString(14.1 * cm, (inicio_y - i * alto_item) * cm, str(item.precio_unitario))
                p.drawRightString(15.1 * cm, (inicio_y - i * alto_item) * cm, "%.2f%%" % item.descuento)
                p.drawRightString(17.6 * cm, (inicio_y - i * alto_item) * cm, "-%.2f" % (item.descuento_value()))
                p.drawRightString(20.1 * cm, (inicio_y - i * alto_item) * cm, "%.2f" % item.subtotal())
            if isinstance(item, Item_compuesto):
                # p.drawString(0.9 * cm, (inicio_y - i * alto_item) * cm, str(item.articulo.codigo))
                p.drawString(2.7 * cm, (inicio_y - i * alto_item) * cm, item.descripcion[:45])
                p.drawRightString(10.2 * cm, (inicio_y - i * alto_item) * cm, "%.2f" % item.cantidad)
                # p.drawString(10.5 * cm, (inicio_y - i * alto_item) * cm, item.articulo.get_unidad_medida_display())
                p.drawRightString(14.1 * cm, (inicio_y - i * alto_item) * cm, str(item.precio_unitario()))
                p.drawRightString(15.1 * cm, (inicio_y - i * alto_item) * cm, "%.2f%%" % item.descuento)
                p.drawRightString(17.6 * cm, (inicio_y - i * alto_item) * cm, "-%.2f" % (item.descuento_value()))
                p.drawRightString(20.1 * cm, (inicio_y - i * alto_item) * cm, "%.2f" % item.subtotal())

        p.setFont('Helvetica', 12)
        p.drawString(15 * cm, 5.5 * cm, "Subtotal")
        p.drawRightString(18.5 * cm, 5.5 * cm, "%.2f" % (venta.subtotal if venta.tipo[-1:] == 'A' else venta.total))
        p.drawString(15 * cm, 5 * cm, "Descuento")
        p.drawRightString(18.5 * cm, 5 * cm, "-%.2f" % venta.descuento_importe())
        p.drawString(15 * cm, 4.5 * cm, "Neto")
        p.drawRightString(18.5 * cm, 4.5 * cm, "%.2f" % (venta.neto if venta.tipo[-1:] == 'A' else venta.total))
        p.drawString(15 * cm, 4 * cm, "IVA 21%")
        p.drawRightString(18.5 * cm, 4 * cm, "%.2f" % (venta.iva21 if venta.tipo[-1:] == 'A' else 0.00))
        p.setFont('Helvetica-Bold', 12)
        p.drawString(15 * cm, 3.3 * cm, "Total")
        p.drawRightString(18.5 * cm, 3.3 * cm, "%.2f" % venta.total)
        p.setFont('Helvetica', 13)
        p.drawString(15 * cm, 1.7 * cm, "CAE: %s" % venta.cae)
        p.drawString(15 * cm, 1.2 * cm, "Fecha Vto: %s" % venta.vto_cae_dd_mm_aaaa())

    venta = Venta.objects.get(pk=pk)
    if venta.aprobado:
        response = HttpResponse(content_type='application/pdf')
        filename = venta.tipo + '-' + venta.pto_vta_num_full
        response['Content-Disposition'] = 'filename="%s.pdf"' % filename.replace(" ", "")
        p = Canvas(response, pagesize=A4)
        p.setAuthor("Appline")
        p.setTitle(filename)
        comprobante(p)
        # Texto tipo de comprobante: original, duplicado, triplicado
        p.drawCentredString(x=10.5 * cm, y=ycm(1.5) * cm, text="ORIGINAL")
        p.showPage()
        comprobante(p)
        # Texto tipo de comprobante: original, duplicado, triplicado
        p.drawCentredString(x=10.5 * cm, y=ycm(1.5) * cm, text="DUPLICADO")
        p.showPage()
        comprobante(p)
        # Texto tipo de comprobante: original, duplicado, triplicado
        p.drawCentredString(x=10.5 * cm, y=ycm(1.5) * cm, text="TRIPLICADO")
        p.showPage()
        p.save()
        return response
