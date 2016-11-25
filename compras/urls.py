from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required
from compras.api import get_proveedores_table, get_proveedores_fk, get_compras_table, get_condiciones_compra_fk
from compras.views import ProveedoresList, ProveedoresNuevo, ProveedoresModificar, proveedoresSuspender, \
    proveedoresHabilitar, ComprasList, compra_new

__author__ = 'jorge'

# PATTERNS DE BANCOS
proveedoresPattern = patterns('',
                              url(r'^$', login_required(ProveedoresList.as_view()), name='listaProveedores'),
                              url(r'nuevo$', login_required(ProveedoresNuevo.as_view()), name='nuevoProveedor'),
                              url(r'editar/(?P<pk>\d+)$', login_required(ProveedoresModificar.as_view()),
                                  name='editarProveedor'),
                              url(r'suspender/(?P<pk>\d+)$', login_required(proveedoresSuspender),
                                  name='suspenderProveedor'),
                              url(r'habilitar/(?P<pk>\d+)$', login_required(proveedoresHabilitar),
                                  name='habilitarProveedor'),
                              url(r'get_proveedores_table/$', login_required(get_proveedores_table),
                                  name='get_proveedores_table'),
                              url(r'get_proveedores_fk/$', login_required(get_proveedores_fk),
                                  name='get_proveedores_fk'),
                              )

comprasPattern = patterns('',
                          url(r'^$', login_required(ComprasList.as_view()), name='listaCompras'),
                          # url(r'lista_pendientes$', login_required(ListarComprobantesPendientesDeAprobacion.as_view()), name='listarPendientes'),
                          url(r'nuevo$', login_required(compra_new), name='nuevaCompra'),
                          # url(r'afip_aprobar/(?P<pk>\d+)$', login_required(afip_aprob), name='afipAprobar'),
                          # url(r'impr_comprobante/(?P<pk>\d+)$', login_required(impr_comprobante), name='imprimirComprobante'),
                          # url(r'editar/(?P<pk>\d+)$', login_required(ProveedoresModificar.as_view()), name='editarProveedor'),
                          # url(r'borrar/(?P<pk>\d+)$', login_required(ProveedoresBorrar.as_view()), name='borrarProveedor'),
                          url(r'get_compras_table/$', login_required(get_compras_table), name='get_compras_table'),
                          )


condicioncompraPattern = patterns('',
                                  url(r'get_condiciones_compra_fk/$', login_required(get_condiciones_compra_fk), name='get_condiciones_compra_fk'),
                                  )


urlpatterns = patterns('',
                       url(r'^proveedores/', include(proveedoresPattern)),
                       url(r'^compras/', include(comprasPattern)),
                       url(r'^condiciones_compra/', include(condicioncompraPattern)),
                       )
