# Create your views here.
from django.http.response import HttpResponseRedirect
from django.views.generic.base import TemplateView
from django.core.urlresolvers import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView

from core.forms import BancosForm, PeriodosForm, TransporteForm, CuentasBancariasForm
from core.models import Bancos, FunctionHit, Periodo, Transporte, CuentasBanco


class Home(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        funciones_favoritas = FunctionHit.objects.filter(usuario=self.request.user).order_by("-hit")[0:5]
        context = super(Home, self).get_context_data(**kwargs)
        context["funciones_favoritas"] = funciones_favoritas
        return context


class BancosList(TemplateView):
    template_name = "bancos/bancos_list.html"

    def dispatch(self, request, *args, **kwargs):
        hit = FunctionHit.objects.get(usuario=self.request.user, funcion="BANCO")
        hit.hit += 1
        hit.save()
        return super(BancosList, self).dispatch(request, *args, **kwargs)


class BancosNuevo(CreateView):
    model = Bancos
    form_class = BancosForm
    template_name = "bancos/bancos_form.html"
    success_url = reverse_lazy("listaBancos")


class BancosModificar(UpdateView):
    model = Bancos
    form_class = BancosForm
    template_name = "bancos/bancos_form.html"
    success_url = reverse_lazy("listaBancos")


def bancosSuspender(request, pk):
    banco = Bancos.objects.get(pk=pk)
    banco.suspendido = True
    banco.save()
    return HttpResponseRedirect(reverse_lazy('listaBancos'))


def bancosHabilitar(request, pk):
    banco = Bancos.objects.get(pk=pk)
    banco.suspendido = False
    banco.save()
    return HttpResponseRedirect(reverse_lazy('listaBancos'))


class PeriodosList(TemplateView):
    template_name = "periodos/periodos_list.html"

    def dispatch(self, request, *args, **kwargs):
        hit = FunctionHit.objects.get(usuario=self.request.user, funcion="PERIO")
        hit.hit += 1
        hit.save()
        return super(PeriodosList, self).dispatch(request, *args, **kwargs)


class PeriodosNuevo(CreateView):
    model = Periodo
    form_class = PeriodosForm
    template_name = "periodos/periodos_form.html"
    success_url = reverse_lazy("listaPeriodos")


class TransportesList(TemplateView):
    template_name = "transportes/transportes_list.html"

    def dispatch(self, request, *args, **kwargs):
        hit = FunctionHit.objects.get(usuario=self.request.user, funcion="TRANS")
        hit.hit += 1
        hit.save()
        return super(TransportesList, self).dispatch(request, *args, **kwargs)


class TransportesNuevo(CreateView):
    model = Transporte
    form_class = TransporteForm
    template_name = "transportes/transportes_form.html"
    success_url = reverse_lazy("listaTransportes")


class TransportesModificar(UpdateView):
    model = Transporte
    form_class = TransporteForm
    template_name = "transportes/transportes_form.html"
    success_url = reverse_lazy("listaTransportes")


def transportesSuspender(request, pk):
    transporte = Transporte.objects.get(pk=pk)
    transporte.suspendido = True
    transporte.save()
    return HttpResponseRedirect(reverse_lazy('listaTransportes'))


def transportesHabilitar(request, pk):
    transporte = Transporte.objects.get(pk=pk)
    transporte.suspendido = False
    transporte.save()
    return HttpResponseRedirect(reverse_lazy('listaTransportes'))


class CuentasBancariasList(TemplateView):
    template_name = "cuentas_bancarias/cuentas_bancarias_list.html"

    def dispatch(self, request, *args, **kwargs):
        hit = FunctionHit.objects.get(usuario=self.request.user, funcion="CUENT")
        hit.hit += 1
        hit.save()
        return super(CuentasBancariasList, self).dispatch(request, *args, **kwargs)


class CuentasBancariasNuevo(CreateView):
    model = CuentasBanco
    form_class = CuentasBancariasForm
    template_name = "cuentas_bancarias/cuentas_bancarias_form.html"
    success_url = reverse_lazy("listaCuentasBancarias")


class CuentasBancariasModificar(UpdateView):
    model = CuentasBanco
    form_class = CuentasBancariasForm
    template_name = "cuentas_bancarias/cuentas_bancarias_form.html"
    success_url = reverse_lazy("listaCuentasBancarias")


def cuentasBancariasSuspender(request, pk):
    cuenta = CuentasBanco.objects.get(pk=pk)
    cuenta.suspendido = True
    cuenta.save()
    return HttpResponseRedirect(reverse_lazy('listaCuentasBancarias'))


def cuentasBancariasHabilitar(request, pk):
    cuenta = CuentasBanco.objects.get(pk=pk)
    cuenta.suspendido = False
    cuenta.save()
    return HttpResponseRedirect(reverse_lazy('listaCuentasBancarias'))