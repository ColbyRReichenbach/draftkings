{% macro normalize_score(value, low_threshold, high_threshold) %}
    CASE
        WHEN {{ value }} >= {{ high_threshold }} THEN 1.0
        WHEN {{ value }} >= {{ low_threshold }} THEN
            ({{ value }} - {{ low_threshold }})::FLOAT /
            NULLIF({{ high_threshold }} - {{ low_threshold }}, 0)
        ELSE 0.0
    END
{% endmacro %}
