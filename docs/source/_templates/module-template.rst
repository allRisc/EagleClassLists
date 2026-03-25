{{ (fullname + " API") | escape | underline}}

.. automodule:: {{ fullname }}
   :private-members:
   :undoc-members:

   {% block modules %}
   {% if modules %}
   .. rubric:: Modules

   .. autosummary::
      :toctree:
      :template: module-template.rst
      :recursive:
   {% for item in modules %}
      {{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block attributes %}
   {% if attributes %}
   .. rubric:: Module Attributes

   {% for item in attributes %}
   .. autoattribute:: {{ fullname }}.{{ item }}
   {% endfor %}
   {% endif %}
   {% endblock %}

   {% block functions %}
   {% if functions %}
   .. rubric:: {{ _('Functions') }}

   {% for item in functions %}
   .. autofunction:: {{ fullname }}.{{ item }}
   {% endfor %}
   {% endif %}
   {% endblock %}

   {% block classes %}
   {% if classes %}
   .. rubric:: {{ _('Classes') }}

   {% for item in classes %}
   .. autoclass:: {{ fullname }}.{{ item }}
      :members:
      :undoc-members:
      :show-inheritance:
      :member-order: groupwise
   {% endfor %}
   {% endif %}
   {% endblock %}

   {% block exceptions %}
   {% if exceptions %}
   .. rubric:: {{ _('Exceptions') }}

   {% for item in exceptions %}
   .. autoexception:: {{ fullname }}.{{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

