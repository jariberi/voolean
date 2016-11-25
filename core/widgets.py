from django.db.models.fields import IntegerField, EmailField
from django.db.models.fields.related import ForeignKey
from django.forms.fields import CharField
from django.forms.widgets import TextInput, Select, NumberInput, EmailInput, Widget


def charfield_handler(field):
    attrs = {}
    if field.max_length > 0:
        if field.min_length >= 0:
            attrs.update(
                {'data-validation': 'length', 'data-validation-length': '%s-%s' % (field.min_length, field.max_length)})
        else:
            attrs.update({'data-validation': 'length', 'data-validation-length': 'max%s' % field.max_length})
    elif field.required:
        attrs.update({'data-validation': 'required'})
    return attrs


def customize_widgets(form_class):
    '''
    :param form_class: Clase del formulario
    :return: devuelve un dict con los widgets personalizados para validacion entre otras cosas
    '''
    widgets = {}
    attrs = {}
    print form_class
    for field in form_class.base_fields.items():
        if type(field[1]) == CharField:
            attrs.update(charfield_handler(field))
        widgets[field[0]] = TextInput(attrs=attrs)
    # if not field[0].name == 'id':
    #         fields.append(field[0])
    # for field in fields:
    #     attrs = {}
    #     if not field.blank:
    #         attrs.update({'data-validation': 'required'})
    #     # attrs.update({'required': ''}) if not field.blank else attrs.update({'required': 'required'})
    #     if type(field) == CharField:
    #         widgets[field.name] = TextInput(attrs=attrs)
    #     if type(field) == ForeignKey:
    #         widgets[field.name] = Select(attrs=attrs)
    #     if type(field) == IntegerField:
    #         widgets[field.name] = NumberInput(attrs=attrs)
    #     if type(field) == EmailField:
    #         widgets[field.name] = EmailInput(attrs=attrs)
    return widgets


class PlainTextWidget(Widget):
    def render(self, name, value, attrs=None):
        if value == None: value = u"--vacio--appline--"
        return value
