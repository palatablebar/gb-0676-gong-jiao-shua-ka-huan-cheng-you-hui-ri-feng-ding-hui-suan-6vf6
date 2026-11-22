from app.modules.m7_settlement.rules import evaluate
from app.errors import DomainError
import pytest
def test_real_sample_archive_ready(result): assert result["stages"][6]["metrics"]["ready"] is True
def test_real_sample_archive_source_count(result): assert result["stages"][6]["metrics"]["source_lines"]==result["stages"][5]["metrics"]["accepted_inputs"]
def test_real_sample_seal_stable(result):
    rows=result["stages"][5]["rows"];assert evaluate(rows,{})["metrics"]["sha256"]==evaluate(rows,{})["metrics"]["sha256"]
def test_unbalanced_blocked():
    with pytest.raises(DomainError) as e:evaluate([],{"reconcile":{"metrics":{"balanced":False}}})
    assert e.value.code=="UNBALANCED"
def test_allocation_unbalanced_blocked():
    "TRAP-29 清分与分摊未对平时拦住日结封存"
    with pytest.raises(DomainError) as e:evaluate([],{"clearing":{"metrics":{"allocation_balanced":False}}})
    assert e.value.code=="ALLOCATION_UNBALANCED"
def test_missing_evidence_blocked():
    "TRAP-30 原始刷卡记录或运营归属依据缺失时拦住封存"
    with pytest.raises(DomainError) as e:evaluate([{"event_id":"1","_sources":[2],"_raw":["x"],"operator_basis":""}],{})
    assert e.value.code=="EVIDENCE_MISSING"
    with pytest.raises(DomainError) as e:evaluate([{"event_id":"1","_sources":[2],"operator_basis":"route=01→OP_A"}],{})
    assert e.value.code=="EVIDENCE_MISSING"
def test_duplicate_archive_key():
    with pytest.raises(DomainError):evaluate([{"event_id":"1"},{"event_id":"1"}],{})
def test_real_sample_manifest_has_hash(result): assert len(result["manifest"]["input_sha256"])==64
def test_real_sample_export_rows_match(result): assert result["stages"][6]["rows"]==result["stages"][5]["rows"]
