from samvit import *

myrules = fromCSV("rules.csv")

rule_id = "Rule 1"

def interpret(rule_id, parms):
    # Search in database for a rule with given rule_id
    myrule = None
    for entry in myrules:
        if entry['Rule #'] == rule_id:
            myrule = entry
            break
    if not myrule:
        return None

    mystr = "{'word' : S }"
    # Replace parameters in mystr with r parms['S']
    c1 = json.loads(myrule['c1'])
    c1 = _subst_parms(myrule['c1'], parms)
    return c1

interpret("Rule 1", { 'S' : 'bAlakaH', 'V' : 'asti', 'vachana' : 'bahu' })

{'word' : S }

{'word' : 'bAlakaH' }
