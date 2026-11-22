import hashlib,json
from decimal import Decimal
from app.errors import DomainError
from app.reasons import sources
def evaluate(rows,context):
    stages=[v for v in context.values() if isinstance(v,dict) and "metrics" in v]
    balances=[s["metrics"]["balanced"] for s in stages if "balanced" in s["metrics"]]
    if balances and not all(balances): raise DomainError("UNBALANCED","来源行未对平，不能归档")
    allocations=[s["metrics"]["allocation_balanced"] for s in stages if "allocation_balanced" in s["metrics"]]
    if allocations and not all(allocations): raise DomainError("ALLOCATION_UNBALANCED","清分与分摊结果未对平，不能封存")
    ids=[str(r.get("event_id",r.get("_line",""))) for r in rows]
    if len(ids)!=len(set(ids)): raise DomainError("ARCHIVE_DUPLICATE","归档业务键重复")
    for row in rows:
        if not sources(row) or row.get("_raw") is None or not row.get("operator_basis"):
            raise DomainError("EVIDENCE_MISSING","原始刷卡记录或运营归属依据缺失，不能封存")
    encoded=json.dumps(rows,ensure_ascii=False,sort_keys=True,default=str).encode()
    return {"rows":rows,"quarantine":[],"metrics":{"records":len(rows),"source_lines":len(set(x for row in rows for x in sources(row))),"sha256":hashlib.sha256(encoded).hexdigest(),"ready":True,"differences":sum(r.get("status")=="差异" for r in rows)}}
