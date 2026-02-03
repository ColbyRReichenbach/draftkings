{% test accepted_range(model, column_name, min_value=None, max_value=None, inclusive=True) %}

SELECT
    *
FROM {{ model }}
WHERE {{ column_name }} IS NOT NULL
  AND (
    {% if min_value is not none %}
      {% if inclusive %}
        {{ column_name }} < {{ min_value }}
      {% else %}
        {{ column_name }} <= {{ min_value }}
      {% endif %}
    {% else %}
      FALSE
    {% endif %}
    OR
    {% if max_value is not none %}
      {% if inclusive %}
        {{ column_name }} > {{ max_value }}
      {% else %}
        {{ column_name }} >= {{ max_value }}
      {% endif %}
    {% else %}
      FALSE
    {% endif %}
  )

{% endtest %}
