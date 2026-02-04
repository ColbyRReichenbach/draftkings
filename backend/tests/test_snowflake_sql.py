from ai_services.snowflake_sql import validate_snowflake_sql


def test_validate_snowflake_sql_rejects_prohibited_syntax():
    sql = "SELECT * FROM table WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'::date"
    violations = validate_snowflake_sql(sql)
    assert violations


def test_validate_snowflake_sql_allows_simple_select():
    sql = "SELECT player_id FROM PROD.RG_RISK_SCORES LIMIT 10"
    violations = validate_snowflake_sql(sql)
    assert not violations
