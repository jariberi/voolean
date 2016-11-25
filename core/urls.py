__author__ = 'jorge'

from core.api import get_bancos_table, get_periodos_table, get_transportes_table, get_cuentabancaria_table, \
    get_bancos_fk, get_periodos_fk
from django.conf.urls import patterns, url, include
from django.contrib.auth.decorators import login_required
from core.views import Home, BancosList, BancosNuevo, BancosModificar, bancosSuspender, bancosHabilitar, PeriodosList, \
    PeriodosNuevo, TransportesList, TransportesNuevo, TransportesModificar, transportesSuspender, transportesHabilitar, \
    CuentasBancariasList, CuentasBancariasNuevo, CuentasBancariasModificar, cuentasBancariasSuspender, \
    cuentasBancariasHabilitar
from django.contrib.auth.views import login

#PATTERNS DE BANCOS
bancosPattern = patterns('',
    url(r'^$', login_required(BancosList.as_view()), name='listaBancos'),
    url(r'nuevo$', login_required(BancosNuevo.as_view()), name='nuevoBanco'),
    url(r'editar/(?P<pk>\d+)$', login_required(BancosModificar.as_view()), name='editarBanco'),
    url(r'suspender/(?P<pk>\d+)$', login_required(bancosSuspender), name='suspenderBanco'),
    url(r'habilitar/(?P<pk>\d+)$', login_required(bancosHabilitar), name='habilitarBanco'),
    url(r'get_bancos_table/$', login_required(get_bancos_table), name='get_bancos_table'),
    url(r'get_bancos_fk/$', login_required(get_bancos_fk), name='get_bancos_fk'),
    )

#PATTERNS DE PERIODOS
periodosPattern = patterns('',
    url(r'^$', login_required(PeriodosList.as_view()), name='listaPeriodos'),
    url(r'nuevo$', login_required(PeriodosNuevo.as_view()), name='nuevoPeriodo'),
    # url(r'editar/(?P<pk>\d+)$', login_required(BancosModificar.as_view()), name='editarBanco'),
    # url(r'suspender/(?P<pk>\d+)$', login_required(bancosSuspender), name='suspenderBanco'),
    # url(r'habilitar/(?P<pk>\d+)$', login_required(bancosHabilitar), name='habilitarBanco'),
    url(r'get_periodos_table/$', login_required(get_periodos_table), name='get_periodos_table'),
    url(r'get_periodos_fk/$', login_required(get_periodos_fk), name='get_periodos_fk'),
    )

#PATTERNS DE TRANSPORTES
transportesPattern = patterns('',
    url(r'^$', login_required(TransportesList.as_view()), name='listaTransportes'),
    url(r'nuevo$', login_required(TransportesNuevo.as_view()), name='nuevoTransporte'),
    url(r'editar/(?P<pk>\d+)$', login_required(TransportesModificar.as_view()), name='editarTransporte'),
    url(r'suspender/(?P<pk>\d+)$', login_required(transportesSuspender), name='suspenderTransporte'),
    url(r'habilitar/(?P<pk>\d+)$', login_required(transportesHabilitar), name='habilitarTransporte'),
    url(r'get_transportes_table/$', login_required(get_transportes_table), name='get_transporte_table'),
    )

#PATTERNS DE CUENTAS BANCARIAS
cuentasBancariasPattern = patterns('',
    url(r'^$', login_required(CuentasBancariasList.as_view()), name='listaCuentasBancarias'),
    url(r'nuevo$', login_required(CuentasBancariasNuevo.as_view()), name='nuevaCuentaBancaria'),
    url(r'editar/(?P<pk>\d+)$', login_required(CuentasBancariasModificar.as_view()), name='editarCuentaBancaria'),
    url(r'suspender/(?P<pk>\d+)$', login_required(cuentasBancariasSuspender), name='suspenderCuentaBancaria'),
    url(r'habilitar/(?P<pk>\d+)$', login_required(cuentasBancariasHabilitar), name='habilitarCuentaBancaria'),
    url(r'get_transportes_table/$', login_required(get_cuentabancaria_table), name='get_cuentabancaria_table'),
    )


urlpatterns = patterns('',
                       url(r'^$', login_required(Home.as_view()), name="home"),
                       url(r'^login/$', login, {"template_name": "login.html"}, name="login"),
                       url(r'^bancos/', include(bancosPattern)),
                       url(r'^transportes/', include(transportesPattern)),
                       url(r'^periodos/', include(periodosPattern)),
                       url(r'^cuentas_bancarias/', include(cuentasBancariasPattern)),
                       )
