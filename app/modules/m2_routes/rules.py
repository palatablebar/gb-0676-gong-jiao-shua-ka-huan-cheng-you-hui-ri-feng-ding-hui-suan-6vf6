from app.reasons import reject
ROUTES={"01":"01","1路":"01","02":"02","2路":"02","03":"03","3路":"03"}
OPERATORS={"01":"OP_A","02":"OP_B","03":"OP_C"}
def evaluate(rows,context):
    mapping=context.get("parameters",{}).get("operators",OPERATORS)
    if not isinstance(mapping,dict):mapping=None
    good=[];bad=[]
    for row in rows:
        route=ROUTES.get(row.get("route"))
        if not route:bad.append(reject(row,"UNKNOWN_ROUTE","线路未登记"));continue
        if not row.get("card"):bad.append(reject(row,"EMPTY_CARD","卡号为空"));continue
        operator=mapping.get(route) if mapping else None
        basis=f"route={route}→{operator}" if operator else "OPERATOR_UNMAPPED"
        good.append({**row,"route":route,"line_group":"city","operator":operator,"operator_basis":basis})
    return {"rows":good,"quarantine":bad,"metrics":{"routes":len(set(r["route"] for r in good)),"accepted":len(good),"operators":len(set(r["operator"] for r in good if r["operator"]))}}
