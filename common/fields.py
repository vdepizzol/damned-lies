#-*- coding: utf-8 -*-
# From: http://djangosnippets.org/snippets/1979/

from django import forms
from django.core import exceptions
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import simplejson

class DictionaryField(models.Field):
    description = "Dictionary object"

    __metaclass__ = models.SubfieldBase

    def get_internal_type(self):
        return "TextField"

    def to_python(self, value):
        if value is None:
            return None
        elif value == "":
            return {}
        elif isinstance(value, basestring):
            try:
                return dict(simplejson.loads(value))
            except (ValueError, TypeError):
                raise exceptions.ValidationError(self.error_messages['invalid'])

        if isinstance(value, dict):
            return value
        else:
            return {}

    def get_prep_value(self, value):
        if not value:
            return ""
        elif isinstance(value, basestring):
            return value
        else:
            return simplejson.dumps(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)

    def clean(self, value, model_instance):
        value = super(DictionaryField, self).clean(value, model_instance)
        return self.get_prep_value(value)

    def formfield(self, **kwargs):
        defaults = {'widget': forms.Textarea}
        defaults.update(kwargs)
        return super(DictionaryField, self).formfield(**defaults)


# From http://djangosnippets.org/snippets/1478/

class JSONField(models.TextField):
    """JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly"""

    # Used so to_python() is called
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""

        if value == "":
            return None

        try:
            if isinstance(value, basestring):
                return simplejson.loads(value)
        except ValueError:
            pass

        return value

    def get_db_prep_save(self, value, connection):
        """Convert our JSON object to a string before we save"""

        if value == "":
            return None

        if isinstance(value, (dict, list)):
            value = simplejson.dumps(value, cls=DjangoJSONEncoder)

        return super(JSONField, self).get_db_prep_save(value, connection=connection)


# rules for South migrations tool (for version >= 0.7)
try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^common\.fields\.DictionaryField"])
    add_introspection_rules([], ["^common\.fields\.JSONField"])
except ImportError:
    pass
