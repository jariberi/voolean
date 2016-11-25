from django.conf.urls import patterns, include, url

'''from boolean_app.api import articulo_datatables_view, comp_datatables_view,\
    cobros_datatables_view, get_comprobantes_de_cliente, get_credito_valores,\
    cliente_datatables_view, proveedores_datatables_view,\
    comp_compras_datatables_view, cheques_datatables_view,\
    cheque_quitar_de_cartera, pagos_datatables_view, get_credito_valores_op,\
    get_datos_defecto_cheque
from boolean_app.reports import impr_comprobante, impr_recibo'''

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

'''clientesPattern = patterns('',
    url(r'^$', login_required(ClientesList.as_view()), name='listaClientes'),
    url(r'nuevo$', login_required(ClientesNuevo.as_view()), name='nuevoCliente'),
    url(r'editar/(?P<pk>\d+)$', login_required(ClientesModificar.as_view()), name='editarCliente'),
    url(r'borrar/(?P<pk>\d+)$', login_required(ClientesBorrar.as_view()), name='borrarCliente'),
    )

bancosPattern = patterns('',
    url(r'^$', login_required(BancosList.as_view()), name='listaBancos'),
    url(r'nuevo$', login_required(BancosNuevo.as_view()), name='nuevoBanco'),
    url(r'editar/(?P<pk>\d+)$', login_required(BancosModificar.as_view()), name='editarBanco'),
    url(r'borrar/(?P<pk>\d+)$', login_required(BancosBorrar.as_view()), name='borrarBanco'),
    )

cpPattern = patterns('',
    url(r'^$', login_required(CondPagoList.as_view()), name='listaCondPago'),
    url(r'nuevo$', login_required(CondPagoNuevo.as_view()), name='nuevoCondPago'),
    url(r'editar/(?P<pk>\d+)$', login_required(CondPagoModificar.as_view()), name='editarCondPago'),
    url(r'borrar/(?P<pk>\d+)$', login_required(CondPagoBorrar.as_view()), name='borrarCondPago'),
    )

lineasPattern = patterns('',
    url(r'^$', login_required(LineaList.as_view()), name='listaLineas'),
    url(r'nuevo$', login_required(LineaNuevo.as_view()), name='nuevoLinea'),
    url(r'editar/(?P<pk>\d+)$', login_required(LineaModificar.as_view()), name='editarLinea'),
    url(r'borrar/(?P<pk>\d+)$', login_required(LineaBorrar.as_view()), name='borrarLinea'),
    )

informesPattern = patterns('',
    url(r'iva_ventas$', login_required(iva_periodo_fecha), name='subdiarioIVAVentas'),
    url(r'exportar_3685_ventas/(?P<periodo>\d+)$', login_required(rg3685_ventas), name='AFIP3685Ventas'),
    url(r'iva_compras$', login_required(subdiario_iva_compras), name='subdiarioIVACompras'),
    url(r'exportar_3685_compras/(?P<periodo>\d+)$', login_required(rg3685_compras), name='AFIP3685Compras'),
    url(r'ventas_totales$', login_required(ventas_totales_fecha), name='informeVentasTotales'),
    url(r'resumen_cuenta$', login_required(resumen_cuenta), name='informeResumenCuenta'),
    url(r'composicion_saldo$', login_required(comp_saldo), name='informeComposicionSaldo'),
    )



pagosPattern = patterns('',
    url(r'^$', login_required(PagosList.as_view()), name='listaOrdenesPago'),
    #url(r'lista_pendientes$', login_required(ListarComprobantesPendientesDeAprobacion.as_view()), name='listarPendientes'),
    url(r'nuevo$', login_required(orden_pago_new), name='nuevaOrdenPago'),
    url(r'nuevo_contado/(?P<compra>\d+)$', login_required(orden_pago_contado_new), name='nuevaOrdenPagoContado'),
    #url(r'afip_aprobar/(?P<pk>\d+)$', login_required(afip_aprob), name='afipAprobar'),
    url(r'impr_op/(?P<pk>\d+)$', login_required(imprimirOrdenPago), name='imprimirOrdenPago'),
    #url(r'editar/(?P<pk>\d+)$', login_required(ProveedoresModificar.as_view()), name='editarProveedor'),
    #url(r'borrar/(?P<pk>\d+)$', login_required(ProveedoresBorrar.as_view()), name='borrarProveedor'),
    )
'''
urlpatterns = patterns('',
                       # url(r'^', include('express.urls')),#Solo express
                       url(r'^', include('core.urls')),
                       url(r'^', include('ventas.urls')),
                       url(r'^', include('compras.urls')),
                       # url(r'^$', login_required(Home.as_view()), name="home"),
                       # url(r'^login/$',login, {"template_name":"login.html"}, name="login"),
                       # url(r'^clientes/', include(clientesPattern)),
                       # url(r'^bancos/', include(bancosPattern)),
                       # url(r'^cond_pago/', include(cpPattern)),
                       # url(r'^articulos/', include(articulosPattern)),
                       # url(r'^lineas/', include(lineasPattern)),
                       # url(r'^rubros/', include(rubrosPattern)),
                       # url(r'^proveedores/', include(proveedoresPattern)),
                       # url(r'^ventas/', include(ventasPattern)),
                       # url(r'^informes/', include(informesPattern)),
                       # url(r'^api/get_punto_venta/(?P<tipo_comprobante>\w{0,50})/$', get_punto_venta,),
                       # url(r'^api/get_proximo_nro_comprobante/(?P<tipo_comprobante>\w{0,50})/$', get_num_prox_comprobante,),
                       # url(r'^api/get_precio_unitario/(?P<pk>\d+)/$', get_precio_unitario,),
                       # url(r'^api/get_precio_unitario_iva_inc/(?P<pk>\d+)/$', get_precio_unitario_iva_inc,),
                       # url(r'^api/get_num_recibo/$', get_num_prox_recibo,),
                       # url(r'^api/get_facturas_pendiente_pago/(?P<cliente>\d+)/$', get_facturas_pendiente_pago,),

                       # url(r'^api/get_credito_valores_op/(?P<proveedor>\d+)/$', get_credito_valores_op),
                       # url(r'^api/obtener_articulos_datatables/$', articulo_datatables_view, name='art_datatables'),
                       # url(r'^api/obtener_clientes_datatables/$', cliente_datatables_view, name='cli_datatables'),
                       # url(r'^api/obtener_proveedores_datatables/$', proveedores_datatables_view, name='pro_datatables'),
                       # url(r'^api/obtener_comprobantes_datatables/$', comp_datatables_view, name='comp_datatables'),
                       # url(r'^api/obtener_compras_datatables/$', comp_compras_datatables_view, name='compras_datatables'),
                       # url(r'^api/obtener_cobros_datatables/$', cobros_datatables_view, name='cobros_datatables'),
                       # url(r'^api/obtener_cheques_datatables/$', cheques_datatables_view, name='cheques_datatables'),
                       # url(r'^api/obtener_comprobantes_cliente/(?P<cliente>\d+)/$', get_comprobantes_de_cliente, name='cobros_datatables'),
                       # url(r'^api/quitar_cheque_de_cartera/$', cheque_quitar_de_cartera, name='cheque_quitar_de_cartera'),
                       # url(r'^api/obtener_pagos_datatables/$', pagos_datatables_view, name='pagos_datatables'),

                       # url(r'^cobros/', include(cobrosPattern)),
                       # url(r'^compras/', include(comprasPattern)),
                       # url(r'^pagos/', include(pagosPattern)),
                       # url(r'^api/get_num_orden_pago/$', get_num_prox_orden_pago,),
                       # url(r'^api/get_facturas_pendiente_pago_prov/(?P<proveedor>\d+)/$', get_facturas_pendiente_pago_prov,),
                       # url(r'^api/get_precio_unitario/', include(ventasPattern)),
                       # Examples:
                       # url(r'^$', 'boolean.views.home', name='home'),
                       # url(r'^boolean/', include('boolean.foo.urls')),

                       # Uncomment the admin/doc line below to enable admin documentation:
                       # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

                       # Uncomment the next line to enable the admin:
                       # url(r'^admin/', include(admin.site.urls)),
                       )
