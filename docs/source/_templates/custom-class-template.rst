{{ fullname.split('.')[-1] | escape | underline }}

.. currentmodule:: {{ module }}

.. autoclass:: {{ module }}.{{ objname }}
   :noindex:

.. rubric:: {{ _('Methods') }}

.. autosummary::
{%- for item in methods %}
   {{ objname }}.{{ item }}
{%- endfor %}

.. rubric:: {{ _('Attributes') }}

.. autosummary::
{%- for item in attributes %}
   {{ objname }}.{{ item }}
{%- endfor %}

{%- for item in methods %}
.. _method-{{ item }}:

.. automethod:: {{ module }}.{{ objname }}.{{ item }}
{%- endfor %}

{%- for item in attributes %}
.. _attribute-{{ item }}:

.. autoattribute:: {{ module }}.{{ objname }}.{{ item }}
{%- endfor %}
