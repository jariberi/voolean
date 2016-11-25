from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required

from ventas.api import get_clientes_table, get_rubros_table, get_subrubros_table, get_lineas_table, get_articulos_table, \
    get_condiciones_venta_table, get_clientes_search, get_comprobante_info, get_posibles_comprobantes_relacionados, \
    get_articulos_almacenados_search, get_ventas_table, get_rubros_fk, get_lineas_fk, get_subrubros_fk, get_clientes_fk, \
    get_articulos_fk, cobros___get_cobros_table, cobros___get_facturas_pendiente_pago, cobros___get_credito_valores, \
    cobros___get_datos_defecto_cheque, get_num_recibo
from ventas.reports import impr_recibo, obtener_comprobante
from ventas.views import ClientesList, ClientesNuevo, ClientesModificar, ArticulosList, ArticulosNuevo, \
    clientesSuspender, clientesHabilitar, RubrosList, RubrosNuevo, RubrosModificar, SubrubrosList, SubrubrosNuevo, \
    SubrubrosModificar, LineasList, LineasNuevo, LineasModificar, ArticulosModificar, articulosSuspender, \
    articulosHabilitar, CondicionesVentaList, CondicionesVentaNuevo, CondicionesVentaModificar, vender, \
    VentasList, VentaDelete, afip_aprob, subdiario_iva_ventas, CobrosList, CobroNew, recibo_contado

__author__ = 'jorge'

rubrosPattern = patterns('',
                         url(r'^$', login_required(RubrosList.as_view()), name='listaRubros'),
                         url(r'nuevo$', login_required(RubrosNuevo.as_view()), name='nuevoRubro'),
                         url(r'editar/(?P<pk>\d+)$', login_required(RubrosModificar.as_view()),
                             name='editarRubro'),
                         url(r'get_rubros_table/$', login_required(get_rubros_table), name='get_rubros_table'),
                         url(r'get_rubros_fk/$', login_required(get_rubros_fk), name='get_rubros_fk'),
                         )

lineasPattern = patterns('',
                         url(r'^$', login_required(LineasList.as_view()), name='listaLineas'),
                         url(r'nuevo$', login_required(LineasNuevo.as_view()), name='nuevaLinea'),
                         url(r'editar/(?P<pk>\d+)$', login_required(LineasModificar.as_view()),
                             name='editarLinea'),
                         url(r'get_rubros_table/$', login_required(get_lineas_table), name='get_lineas_table'),
                         url(r'get_lineas_fk/$', login_required(get_lineas_fk), name='get_lineas_fk'),
                         )

subrubrosPattern = patterns('',
                            url(r'^$', login_required(SubrubrosList.as_view()), name='listaSubrubros'),
                            url(r'nuevo$', login_required(SubrubrosNuevo.as_view()), name='nuevoSubrubro'),
                            url(r'editar/(?P<pk>\d+)$', login_required(SubrubrosModificar.as_view()),
                                name='editarSubrubro'),
                            url(r'get_subrubros_table/$', login_required(get_subrubros_table),
                                name='get_subrubros_table'),
                            url(r'get_subrubros_fk/$', login_required(get_subrubros_fk), name='get_subrubros_fk'),
                            )

articulosPattern = patterns('',
                            url(r'^$', login_required(ArticulosList.as_view()), name='listaArticulos'),
                            url(r'nuevo$', login_required(ArticulosNuevo.as_view()), name='nuevoArticulo'),
                            url(r'editar/(?P<pk>\d+)$', login_required(ArticulosModificar.as_view()),
                                name='editarArticulo'),
                            url(r'suspender/(?P<pk>\d+)$', login_required(articulosSuspender),
                                name='suspenderArticulo'),
                            url(r'habilitar/(?P<pk>\d+)$', login_required(articulosHabilitar),
                                name='habilitarArticulo'),
                            url(r'get_articulos_table/$', login_required(get_articulos_table),
                                name='get_articulos_table'),
                            url(r'get_articulos_fk/$', login_required(get_articulos_fk), name='get_articulos_fk'),
                            )

condicionesVentaPattern = patterns('',
                                   url(r'^$', login_required(CondicionesVentaList.as_view()),
                                       name='listaCondicionesVenta'),
                                   url(r'nuevo$', login_required(CondicionesVentaNuevo.as_view()),
                                       name='nuevaCondicionVenta'),
                                   url(r'editar/(?P<pk>\d+)$', login_required(CondicionesVentaModificar.as_view()),
                                       name='editarCondicionVenta'),
                                   url(r'get_condiciones_venta_table/$', login_required(get_condiciones_venta_table),
                                       name='get_condiciones_venta_table'),
                                   )

clientesPattern = patterns('',
                           url(r'^$', login_required(ClientesList.as_view()), name='listaClientes'),
                           url(r'nuevo$', login_required(ClientesNuevo.as_view()), name='nuevoCliente'),
                           url(r'editar/(?P<pk>\d+)$', login_required(ClientesModificar.as_view()),
                               name='editarCliente'),
                           url(r'suspender/(?P<pk>\d+)$', login_required(clientesSuspender), name='suspenderCliente'),
                           url(r'habilitar/(?P<pk>\d+)$', login_required(clientesHabilitar), name='habilitarCliente'),
                           url(r'get_clientes_table/$', login_required(get_clientes_table), name='get_clientes_table'),
                           url(r'get_clientes_fk/$', login_required(get_clientes_fk), name='get_clientes_fk'),
                           # url(r'borrar/(?P<pk>\d+)$', login_required(ClientesBorrar.as_view()), name='borrarCliente'),
                           )

ventasPattern = patterns('',
                         url(r'^$', login_required(VentasList.as_view()), name='listaVentas'),
                         url(r'nuevo$', login_required(vender), name='nuevaVenta'),
                         # TODO:funcion no terminadaurl(r'editar/(?P<pk>\d+)$', login_required(modificarVenta), name='editarVenta'),
                         url(r'get_clientes_search/$', login_required(get_clientes_search), name='get_clientes_search'),
                         url(r'get_comprobante_info/$', login_required(get_comprobante_info),
                             name='get_comprobante_info'),
                         url(r'get_posibles_comprobantes_relacionados/$',
                             login_required(get_posibles_comprobantes_relacionados),
                             name='get_posibles_comprobantes_relacionados'),
                         url(r'get_articulos_almacenados_search/$', login_required(get_articulos_almacenados_search),
                             name='get_articulos_almacenados_search'),
                         url(r'get_ventas_table/$', login_required(get_ventas_table), name='get_ventas_table'),
                         url(r'borrar/(?P<pk>\d+)$', login_required(VentaDelete.as_view()), name='borrarVenta'),
                         url(r'aprobar/(?P<pk>\d+)$', login_required(afip_aprob), name='aprobarVenta'),
                         url(r'subdiario/$', login_required(subdiario_iva_ventas), name='subdiarioIvaVentas'),
                         url(r'obtener_comprobante/(?P<pk>\d+)$', login_required(obtener_comprobante),
                             name='obtenerComprobante'),
                         )

cobrosPattern = patterns('',
                         url(r'^$', login_required(CobrosList.as_view()), name='listaCobros'),
                         # url(r'cheques_en_cartera$', login_required(chequesList.as_view()),
                         #     name='listarChequesEnCartera'),
                         url(r'nuevo$', login_required(CobroNew.as_view()), name='nuevoCobro'),
                         url(r'nuevo_contado/(?P<venta>\d+)$', login_required(recibo_contado),
                             name='nuevoReciboContado'),
                         url(r'impr_recibo/(?P<pk>\d+)$', login_required(impr_recibo), name='imprimirRecibo'),
                         url(r'get_cobros_table/$', login_required(cobros___get_cobros_table), name='get_cobros_table'),
                         url(r'get_num_recibo/$', get_num_recibo, name='get_num_recibo'),
                         url(r'get_facturas_pendiente_pago/(?P<cliente>\d+)/$', cobros___get_facturas_pendiente_pago,
                             name="get_facturas_pendiente_pago"),
                         url(r'get_credito_valores/(?P<cliente>\d+)/$', cobros___get_credito_valores,
                             name='cobros___get_credito_valores'),
                         url(r'^get_datos_cheque_defecto/(?P<cliente>\d+)/$', cobros___get_datos_defecto_cheque,
                             name='cobros___get_datos_defecto_cheque'),
                         )

urlpatterns = patterns('',
                       url(r'^rubros/', include(rubrosPattern)),
                       url(r'^subrubros/', include(subrubrosPattern)),
                       url(r'^lineas/', include(lineasPattern)),
                       url(r'^clientes/', include(clientesPattern)),
                       url(r'^articulos/', include(articulosPattern)),
                       url(r'^condiciones_venta/', include(condicionesVentaPattern)),
                       url(r'^ventas/', include(ventasPattern)),
                       url(r'^cobros/', include(cobrosPattern)),
                       )
