{{ fullname | escape | underline }}

.. currentmodule:: {{ module }}

.. autoclass:: {{ module }}.{{ objname }}
   :noindex:

.. rubric:: {{ _('Methods') }}

.. autosummary::
{% for item in methods %}
   {{ module }}.{{ objname }}.{{ item }}
{%- endfor %}

.. rubric:: {{ _('Attributes') }}

.. autosummary::
{% for item in attributes %}
   {{ module }}.{{ objname }}.{{ item }}
{%- endfor %}

.. toctree::
   :hidden:

{% for item in methods %}
   {{ fullname }}#method-{{ item }}
{%- endfor %}
{% for item in attributes %}
   {{ fullname }}#attribute-{{ item }}
{%- endfor %}

{% for item in methods %}
.. _method-{{ item }}:

.. automethod:: {{ module }}.{{ objname }}.{{ item }}
{%- endfor %}

{% for item in attributes %}
.. _attribute-{{ item }}:

.. autoattribute:: {{ module }}.{{ objname }}.{{ item }}
{%- endfor %}
