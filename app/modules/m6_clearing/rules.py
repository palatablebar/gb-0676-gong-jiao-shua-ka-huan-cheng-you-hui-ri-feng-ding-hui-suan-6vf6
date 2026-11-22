from decimal import Decimal
from app.reasons import sources
from app.errors import DomainError
def evaluate(rows,context):
    intake=context.get("intake")
    bad=context.get("quarantine",[])
    accepted=set(x for row in rows for x in sources(row))
    rejected=set(x for row in bad for x in sources(row))
    if accepted & rejected: raise DomainError("LINEAGE_OVERLAP","同一来源行被重复裁决")
    m={"accepted_inputs":len(accepted),"quarantine_inputs":len(rejected),"output_records":len(rows)}
    if intake:
        excluded=intake["duplicate"]+intake["blank"]+intake["repeated_headers"]
        m.update(input=intake["input"],excluded=excluded,balanced=intake["input"]==len(accepted)+len(rejected)+excluded)
    else:m.update(input=len(accepted)+len(rejected),excluded=0,balanced=True)
    output=[]
    for row in rows:
        expected=Decimal(str(row.get("expected","0")));reported=Decimal(str(row.get("reported","0")))
        output.append({**row,"difference":str(expected-reported),"status":"通过" if expected==reported else "差异"})
    m.update(expected_total=str(sum((Decimal(str(r.get("expected","0"))) for r in rows),Decimal(0))),reported_total=str(sum((Decimal(str(r.get("reported","0"))) for r in rows),Decimal(0))),differences=sum(r["status"]=="差异" for r in output))
    days={}
    for row in rows:
        day=days.setdefault((row.get("card"),row.get("business_day")),[Decimal(0),Decimal(0)])
        day[0]+=Decimal(str(row.get("cap_discount","0")));day[1]+=Decimal(str(row.get("cap_share","0")))
    cap_total=sum((d[0] for d in days.values()),Decimal(0));share_total=sum((d[1] for d in days.values()),Decimal(0))
    m.update(cap_discount_total=str(cap_total),allocated_total=str(share_total),allocation_balanced=cap_total==share_total and all(a==b for a,b in days.values()))
    return {"rows":output,"quarantine":[],"metrics":m}
