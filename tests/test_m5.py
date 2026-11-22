from app.modules.m5_discounts.rules import evaluate,allocate
from app.errors import DomainError
from decimal import Decimal
import pytest
def ride(id,minute,route="01",base="2.50"):
    return {"event_id":str(id),"card":"0001","business_day":"2026-11-16","at":f"2026-11-16T{8+minute//60:02d}:{minute%60:02d}:00Z","route":route,"base_fare":base}
ROUTE_OPS={"01":"OP_A","02":"OP_B","03":"OP_C"}
def op_ride(id,minute,route="01",base="2.50"):
    return {**ride(id,minute,route,base),"operator":ROUTE_OPS[route]}
def test_real_day_cap(result): assert result["stages"][4]["metrics"]["expected_total"]=="48.00"
def test_exact_window_excluded():
    "TRAP-23 半开换乘窗"
    r=evaluate([ride(1,0),ride(2,60,"02")],{})["rows"];assert r[1]["transfer_discount"]=="0.00"
def test_within_window_discount(): assert evaluate([ride(1,0),ride(2,59,"02")],{})["rows"][1]["expected"]=="1.50"
def test_same_route_no_transfer(): assert evaluate([ride(1,0),ride(2,10)],{})["rows"][1]["expected"]=="2.50"
def test_zero_paid_not_anchor():
    r=evaluate([ride(1,0,base="1"),ride(2,30,"02",base="1"),ride(3,61,"03",base="1")],{})["rows"]
    assert r[1]["expected"]=="0.00" and r[2]["transfer_discount"]=="0.00"
def test_discount_before_cap_conservation():
    "TRAP-10 Decimal守恒"
    r=evaluate([ride(1,0),ride(2,10,"02"),ride(3,20,"03"),ride(4,90)],{})["rows"]
    assert sum(Decimal(x["expected"]) for x in r)==Decimal("6")
    assert all(Decimal(x["base_fare"])==Decimal(x["expected"])+Decimal(x["transfer_discount"])+Decimal(x["cap_discount"]) for x in r)
def test_negative_parameter_rejected():
    with pytest.raises(DomainError):evaluate([],{"parameters":{"daily_cap":"-1"}})
def test_input_order_invariant():
    rows=[ride(1,0),ride(2,10,"02")];assert evaluate(rows,{})["rows"]==evaluate(list(reversed(rows)),{})["rows"]
def test_cap_shared_by_contributing_operators():
    "TRAP-27 封顶减免按各运营方实扣贡献比例分担，不独压末程"
    r=evaluate([op_ride(1,0),op_ride(2,10,"02"),op_ride(3,20,"03"),op_ride(4,120)],{})["rows"]
    assert [x["cap_share"] for x in r]==["0.83","0.50","0.50","0.17"]
    by_op={}
    for x in r:by_op[x["operator"]]=by_op.get(x["operator"],Decimal(0))+Decimal(x["cap_share"])
    assert by_op=={"OP_A":Decimal("1.00"),"OP_B":Decimal("0.50"),"OP_C":Decimal("0.50")}
def test_day_paid_never_exceeds_cap():
    r=evaluate([op_ride(1,0),op_ride(2,10,"02"),op_ride(3,20,"03"),op_ride(4,120)],{})["rows"]
    assert sum(Decimal(x["expected"]) for x in r)<=Decimal("6.00")
    assert sum(Decimal(x["cap_share"]) for x in r)==sum(Decimal(x["cap_discount"]) for x in r)
def test_allocate_odd_cents_conserved():
    "TRAP-10 分币守恒：最大余数法，并列按业务键字典序"
    share=allocate([("a",Decimal(1)),("b",Decimal(1)),("c",Decimal(1))],Decimal("0.05"))
    assert share=={"a":Decimal("0.02"),"b":Decimal("0.02"),"c":Decimal("0.01")}
    assert sum(share.values())==Decimal("0.05")
def test_zero_contribution_operator_no_share():
    r=evaluate([op_ride(1,0),op_ride(2,10,"02")],{"parameters":{"daily_cap":"2.50"}})["rows"]
    assert r[1]["expected"]=="0.00" and r[1]["cap_share"]=="0.00" and r[0]["cap_share"]=="1.50"
def test_operator_missing_legacy_fallback():
    "TRAP-28 归属读取失败时该卡日完整保留旧版口径"
    r=evaluate([ride(1,0),ride(2,10,"02")],{"parameters":{"daily_cap":"2.50"}})["rows"]
    assert all(x["allocation_mode"]=="legacy_fallback" for x in r)
    assert [x["cap_share"] for x in r]==[x["cap_discount"] for x in r]==["0.00","1.50"]
def test_real_sample_allocation_balanced(result):
    m=result["stages"][4]["metrics"]
    assert m["cap_discount_total"]=="16.00" and m["allocated_total"]=="16.00" and m["allocation_balanced"] is True and m["fallback_days"]==0
