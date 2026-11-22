from app.modules.m6_clearing.rules import evaluate
from decimal import Decimal
def test_real_sample_four_books(result): assert result["stages"][5]["metrics"]["balanced"] is True
def test_real_sample_final_lineage(result):
    m=result["stages"][5]["metrics"];assert m["accepted_inputs"]+m["quarantine_inputs"]+m["excluded"]==m["input"]
def test_real_sample_difference_is_explicit(result):
    rows=result["stages"][5]["rows"];assert any(r["status"]=="差异" for r in rows)
def test_real_sample_totals_exact(result):
    rows=result["stages"][5]["rows"];m=result["stages"][5]["metrics"]
    assert sum((Decimal(r["difference"]) for r in rows),Decimal(0))==Decimal(m["expected_total"])-Decimal(m["reported_total"])
def test_empty_reconcile():
    r=evaluate([],{});assert r["metrics"]["balanced"] is True and r["metrics"]["expected_total"]=="0"
def test_overlap_is_rejected():
    import pytest
    from app.errors import DomainError
    with pytest.raises(DomainError):evaluate([{"_line":1}],{"quarantine":[{"_line":1}]})
def test_real_sample_rejected_have_reason(result):
    assert all(r["reason"] and r["detail"] for r in result["stages"][5]["cumulative_quarantine"])
def test_real_sample_allocation_reconciled(result):
    m=result["stages"][5]["metrics"]
    assert m["allocation_balanced"] is True and m["cap_discount_total"]=="16.00" and m["allocated_total"]=="16.00"
def test_allocation_unbalanced_detected():
    rows=[{"card":"0001","business_day":"2026-11-16","expected":"2.00","reported":"2.00","cap_discount":"1.00","cap_share":"0.50"}]
    assert evaluate(rows,{})["metrics"]["allocation_balanced"] is False
def test_allocation_balanced_per_card_day():
    rows=[{"card":"0001","business_day":"2026-11-16","expected":"2.00","reported":"2.00","cap_discount":"1.00","cap_share":"0.60"},
          {"card":"0001","business_day":"2026-11-16","expected":"1.00","reported":"1.00","cap_discount":"0.00","cap_share":"0.40"}]
    assert evaluate(rows,{})["metrics"]["allocation_balanced"] is True
