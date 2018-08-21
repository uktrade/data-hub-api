{% set sections_by_category = [] %}
{% for section, category_data in sections.items() %}
{% for category, values in category_data.items() %}
{% for text, issues in values.items() %}{{ sections_by_category.append({'category': category, 'section': section, 'text': text, 'issues': issues}) or '' }}{% endfor %}
{% endfor %}
{% endfor %}
{% set sections_by_category = dict(sections_by_category|groupby('category')) %}


{% for category, val in definitions.items() if category in sections_by_category %}

{% set underline = "-" %}
{{ definitions[category]['name'] }}
{{ underline * definitions[category]['name']|length }}

{% for item in sections_by_category[category] %}{% set text = item.text %}{% set values = item.issues %}
{% if definitions[category]['showcontent'] %}
- {% if item.section %}**{{item.section}}** {% endif %}{{ text }}
{% else %}
not supported due to lack of issues
{% endif %}
{% endfor %}
{% endfor %}
