from decimal import Decimal
from django import forms
from django.db import models
from django.forms import widgets

from compras.models import Proveedor, Condicion_compra
from core.models import Bancos, Periodo, Transporte, CuentasBanco
from ventas.models import Rubro, SubRubro, Linea, Cliente, Articulo
from django.forms import widgets, utils
from django.utils import encoding, html

__author__ = 'jorge'


#####   WIDGET's    #####

class AutoCompleteFKMultiWidget(widgets.MultiWidget):
    dict_pk_search = {Bancos: 'nombre', Rubro: 'nombre', Proveedor: 'razon_social', SubRubro: 'nombre', Linea: 'nombre',
                      Transporte: 'nombre', Cliente: 'razon_social', Articulo: 'denominacion', Periodo: 'periodo_full',
                      Condicion_compra: 'descripcion'}

    def __init__(self, attrs=None):
        _widgets = (
            widgets.TextInput(attrs={'class': 'mdl-textfield__input'}), widgets.HiddenInput())
        super(AutoCompleteFKMultiWidget, self).__init__(_widgets, attrs)

    def decompress(self, value):
        if value:
            obj = self.choices.queryset.model.objects.get(pk=value)
            return [getattr(obj, self.dict_pk_search[self.choices.queryset.model]), obj.pk]
        else:
            return [None, None]

    def value_from_datadict(self, data, files, name):
        values = super(AutoCompleteFKMultiWidget, self).value_from_datadict(data, files, name)
        try:
            return int(values[1])
        except ValueError:
            return None


class MDLSwitch(forms.CheckboxInput):
    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs, type='checkbox', name=name)
        final_attrs['class'] = 'mdl-switch__input'
        if self.check_test(value):
            final_attrs['checked'] = 'checked'
        if not (value is True or value is False or value is None or value == ''):
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = encoding.force_text(value)
        wi = '<label class="mdl-switch mdl-js-switch" for="%s"><input {} ><span class="mdl-switch__label">%s</span></label>' % (
            'id_' + name, name)
        return html.format_html(wi, utils.flatatt(final_attrs))


class RadioSelectMDL(forms.widgets.RadioSelect):
    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs, type='checkbox', name=name)
        final_attrs['class'] = 'mdl-switch__input'
        if self.check_test(value):
            final_attrs['checked'] = 'checked'
        if not (value is True or value is False or value is None or value == ''):
            # Only add the 'value' attribute if a value is non-empty.
            final_attrs['value'] = encoding.force_text(value)
        wi = '<label class="mdl-switch mdl-js-switch" for="%s"><input {} ><span class="mdl-switch__label">%s</span></label>' % (
            'id_' + name, name)
        return html.format_html(wi, utils.flatatt(final_attrs))


class BooleanFieldMDL(forms.BooleanField):
    widget = MDLSwitch

    def widget_attrs(self, widget):
        attrs = super(BooleanFieldMDL, self).widget_attrs(widget)
        attrs.update({'class': 'mdl-switch__input'})
        return attrs
        return super(BooleanFieldMDL, self).widget_attrs(widget)


##### FIELD'S ######

class BoundFieldMDL(forms.forms.BoundField):
    def label_tag(self, contents=None, attrs={'class': 'mdl-textfield__label'}, label_suffix=None):
        return super(BoundFieldMDL, self).label_tag(contents, attrs, label_suffix)


class CharFieldMDL(forms.CharField):
    def widget_attrs(self, widget):
        attrs = super(CharFieldMDL, self).widget_attrs(widget)
        attrs.update({'class': 'mdl-textfield__input'})
        return attrs


class DateFieldMDL(forms.DateField):
    def widget_attrs(self, widget):
        attrs = super(DateFieldMDL, self).widget_attrs(widget)
        attrs.update({'class': 'mdl-textfield__input'})
        return attrs


class IntegerFieldMDL(forms.IntegerField):
    def widget_attrs(self, widget):
        attrs = super(IntegerFieldMDL, self).widget_attrs(widget)
        attrs.update({'class': 'mdl-textfield__input'})
        return attrs


class DecimalFieldMDL(forms.DecimalField):
    def widget_attrs(self, widget):
        attrs = super(DecimalFieldMDL, self).widget_attrs(widget)
        attrs.update({'class': 'mdl-textfield__input'})
        return attrs


class ChoiceFieldMDL(forms.ChoiceField):
    def widget_attrs(self, widget):
        attrs = super(ChoiceFieldMDL, self).widget_attrs(widget)
        attrs.update({'style': 'width: 100%;'})
        return attrs


class AutoCompleteMDLFKField(forms.ModelChoiceField):
    widget = AutoCompleteFKMultiWidget


def customize_field(field):
    if field.choices:
        return ChoiceFieldMDL(choices=field.choices, label='', help_text=field.help_text)
    elif isinstance(field, models.CharField):
        if 'cbu' in field.name:
            return CharFieldMDL(max_length=field.max_length, min_length=field.max_length, help_text=field.help_text)
        return CharFieldMDL(max_length=field.max_length, help_text=field.help_text, required=not field.blank)
    elif isinstance(field, models.PositiveIntegerField) or isinstance(field, models.IntegerField):
        return IntegerFieldMDL(localize=True, help_text=field.help_text)
    elif isinstance(field, models.DecimalField):
        return DecimalFieldMDL(localize=True, help_text=field.help_text, required=not field.blank,
                               initial=field.default if isinstance(field.default, Decimal) else None)
    elif isinstance(field, models.TextField):
        return CharFieldMDL(help_text=field.help_text, widget=forms.Textarea)
    elif isinstance(field, models.ForeignKey):
        return AutoCompleteMDLFKField(queryset=field.rel.to.objects.all(), required=not field.blank)
    elif isinstance(field, models.DateField):
        return DateFieldMDL(input_formats=['%d/%m/%Y',], help_text=field.help_text, localize=False, initial=field.default, widget=forms.DateInput(format="%d/%m/%Y"))
    else:
        return field.formfield()


class MDLBaseModelForm(forms.ModelForm):
    def __getitem__(self, name):
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError(
                "Key %r not found in '%s'" % (name, self.__class__.__name__))
        if name not in self._bound_fields_cache:
            self._bound_fields_cache[name] = BoundFieldMDL(self, field, name)
        return self._bound_fields_cache[name]

    class Meta:
        abstract = True

    def as_mdl(self):
        self.label_suffix = ''
        line = """<div class="mdl-grid">
                    <div class="mdl-cell--5-col">
                        <div style="width:90%%" class="mdl-textfield mdl-js-textfield">
                            %(field)s
                            %(label)s
                            <span class="individual_errors">%(errors)s</span>
                        </div>
                    </div>
                    <div class="mdl-cell--7-col">
                        %(help_text)s
                    </div>
                </div>"""
        return self._html_output(
            normal_row=line,
            error_row='<div class="form_errors">%s</div>',
            row_ender='</p>',
            help_text_html='<p class="mdl-textfield mdl-js-textfield help-text">%s</p>',
            errors_on_separate_row=False)


class MDLBaseForm(forms.Form):
    def __getitem__(self, name):
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError(
                "Key %r not found in '%s'" % (name, self.__class__.__name__))
        if name not in self._bound_fields_cache:
            self._bound_fields_cache[name] = BoundFieldMDL(self, field, name)
        return self._bound_fields_cache[name]

    class Meta:
        abstract = True

    def as_mdl(self):
        self.label_suffix = ''
        line = """<div class="mdl-grid">
                    <div class="mdl-cell--5-col">
                        <div style="width:90%%" class="mdl-textfield mdl-js-textfield">
                            %(field)s
                            %(label)s
                            <span class="individual_errors">%(errors)s</span>
                        </div>
                    </div>
                    <div class="mdl-cell--7-col">
                        %(help_text)s
                    </div>
                </div>"""
        return self._html_output(
            normal_row=line,
            error_row='<div class="form_errors">%s</div>',
            row_ender='</p>',
            help_text_html='<p class="mdl-textfield mdl-js-textfield help-text">%s</p>',
            errors_on_separate_row=False)


class BancosForm(MDLBaseModelForm):
    formfield_callback = customize_field

    class Meta:
        model = Bancos
        fields = ['nombre']


class CuentasBancariasForm(MDLBaseModelForm):
    formfield_callback = customize_field

    class Meta:
        model = CuentasBanco
        fields = '__all__'
        exclude = ['suspendido']


class PeriodosForm(MDLBaseModelForm):
    formfield_callback = customize_field

    class Meta:
        model = Periodo
        fields = '__all__'


class TransporteForm(MDLBaseModelForm):
    formfield_callback = customize_field

    class Meta:
        model = Transporte
        fields = '__all__'
        exclude = ['suspendido']
