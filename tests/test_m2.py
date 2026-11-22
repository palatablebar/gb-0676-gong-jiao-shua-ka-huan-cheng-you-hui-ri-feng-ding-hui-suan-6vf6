from app.modules.m2_routes.rules import evaluate
def test_real_routes(result): assert result["stages"][1]["metrics"]["routes"]==3
def test_real_alias_normalized(result): assert result["stages"][1]["rows"][0]["route"]=="01"
def test_unknown_route_quarantine(result): assert any(r["reason"]=="UNKNOWN_ROUTE" for r in result["stages"][1]["quarantine"])
def test_alias_has_same_group(): assert evaluate([{"route":"1路","card":"01"},{"route":"01","card":"02"}],{})["rows"][0]["line_group"]=="city"
def test_missing_card(): assert evaluate([{"route":"01","card":""}],{})["quarantine"][0]["reason"]=="EMPTY_CARD"
def test_all_unknown(): assert evaluate([{"route":"X","card":"a"}],{})["rows"]==[]
def test_input_order_preserved(): assert [r["card"] for r in evaluate([{"route":"01","card":"02"},{"route":"01","card":"01"}],{})["rows"]]==["02","01"]
def test_operator_attributed():
    r=evaluate([{"route":"1路","card":"01"}],{})["rows"][0]
    assert r["operator"]=="OP_A" and r["operator_basis"]=="route=01→OP_A"
def test_operator_map_failure_keeps_rows():
    "TRAP-28 归属读取失败保留完整行，operator置空待旧版回退"
    r=evaluate([{"route":"01","card":"01"}],{"parameters":{"operators":"broken"}})
    assert len(r["rows"])==1 and r["rows"][0]["operator"] is None and r["rows"][0]["operator_basis"]=="OPERATOR_UNMAPPED"
def test_operator_unmapped_route_kept():
    r=evaluate([{"route":"01","card":"01"}],{"parameters":{"operators":{"02":"OP_X"}}})
    assert r["rows"][0]["operator"] is None and r["rows"][0]["route"]=="01"
