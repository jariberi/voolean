from django import forms

__author__ = 'jorge'

class CustomCharField(forms.fields.CharField):


    def clean(self, value):
        return super(CustomCharField, self).clean(value)