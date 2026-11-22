from decimal import Decimal,ROUND_FLOOR
from app.values import number,instant,money
from app.errors import DomainError
CENT=Decimal("0.01")
def allocate(weights,total):
    "把total按weights比例分摊到分，最大余数法保证Σ分摊==total。weights:[(key,Decimal)]。"
    keys=[k for k,_ in weights];pool=sum((w for _,w in weights),Decimal(0))
    if total<=0 or pool<=0:return {k:Decimal("0.00") for k in keys}
    exact={k:total*w/pool for k,w in weights}
    share={k:(exact[k]/CENT).to_integral_value(rounding=ROUND_FLOOR)*CENT for k in keys}
    left=int((total-sum(share.values()))/CENT)
    order=sorted(keys,key=lambda k:(-(exact[k]-share[k]),str(k)))
    for i in range(left):share[order[i%len(order)]]+=CENT
    return share
def evaluate(rows,context):
    params=context.get("parameters",{});cap=number(params.get("daily_cap","6.00"));off=number(params.get("transfer_discount","1.00"));window=number(params.get("transfer_minutes","60"))
    if cap<0 or off<0 or window<0:raise DomainError("BAD_DISCOUNT","优惠参数不能为负")
    spent={};anchor={};good=[]
    for row in sorted(rows,key=lambda r:(r["card"],instant(r["at"]),r["event_id"])):
        key=(row["card"],row["business_day"]);base=number(row["base_fare"]);previous=anchor.get(key);eligible=False
        if previous:
            delta=Decimal(str((instant(row["at"])-instant(previous["at"])).total_seconds()))/60
            eligible=previous["route"]!=row["route"] and Decimal(0)<=delta<window
        transfer=min(base,off) if eligible else Decimal(0)
        after_transfer=base-transfer;remaining=max(Decimal(0),cap-spent.get(key,Decimal(0)));charge=min(after_transfer,remaining)
        cap_discount=after_transfer-charge;spent[key]=spent.get(key,Decimal(0))+charge
        good.append({**row,"transfer_anchor":previous["event_id"] if eligible else "—","transfer_discount":money(transfer),"cap_discount":money(cap_discount),"expected":money(charge),"day_paid":money(spent[key])})
        if charge>0:anchor[key]=row
    days={}
    for row in good:days.setdefault((row["card"],row["business_day"]),[]).append(row)
    fallback=0
    for items in days.values():
        cap_total=sum((number(r["cap_discount"]) for r in items),Decimal(0))
        if cap_total<=0:
            for r in items:r.update(cap_share="0.00",allocation_mode="none")
            continue
        if any(not r.get("operator") for r in items):
            fallback+=1
            for r in items:r.update(cap_share=r["cap_discount"],allocation_mode="legacy_fallback")
            continue
        shares=allocate([(i,number(r["expected"])) for i,r in enumerate(items)],cap_total)
        for i,r in enumerate(items):r.update(cap_share=money(shares[i]),allocation_mode="shared")
    for r in good:r["operator_net"]=money(number(r["expected"])-number(r["cap_share"]))
    cap_total=sum((number(r["cap_discount"]) for r in good),Decimal(0));share_total=sum((number(r["cap_share"]) for r in good),Decimal(0))
    return {"rows":good,"quarantine":[],"metrics":{"expected_total":money(sum((number(r["expected"]) for r in good),Decimal(0))),"daily_caps":len(spent),"transfer_hits":sum(r["transfer_anchor"]!="—" for r in good),"cap_discount_total":money(cap_total),"allocated_total":money(share_total),"allocation_balanced":cap_total==share_total,"fallback_days":fallback}}
