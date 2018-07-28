import subprocess
import sys
import re
import json
import os
from os.path import join, dirname, realpath
from functools import reduce #for 3.x
from indic_transliteration import sanscript

SANDHI_OVERRIDES_SHEET_NAME = 'Sandhi_overrides';
MACROS_SHEET_NAME ='Macros';

# Format of sandhi_overrides sheet
# First header row has header fields Purva_pattern,Uttara_pattern,Samhita_pattern,Shaakha,Priority
# A row that starts with a '#' is ignored as comment.
# Within a purva_pada pattern, one can refer to a macro to
# refer to a list of items via __M:<macroname>__
# For example, to refer to chars 'a i u', embed __M:aR1__
#
# Within an uttara_pada pattern, one can embed a python expression to be
# evaluated via __<expr>__
#
class SandhiJoiner:
    def __init__(self, sclpath, sandhi_gsheet_id):
        self.overrides = []
        self.macros = {}
        self.sclpath = sclpath
        self.sandhi_gsheet = sandhi_gsheet_id
        self.reload()
    
    def reload(self):
        del self.overrides[:] #clears list without changing referance.
        self.macros.clear() #clears macros dict with out changing referance, to effect all referances.
        
        #so: sandhi_overrides
        from google_services_helper import gsheets
        so_response_table , so_response_code = gsheets.values.sheet_values_for(
            self.sandhi_gsheet, SANDHI_OVERRIDES_SHEET_NAME, 
            pargs={'idType':'title', 'valuesFormat':'rows'})
        
        so_rows_list = so_response_table.get('values', [])
        for row in so_rows_list:
            self.overrides.append(row)

        self.macros = {}
        #ph:Pratyaharas
        ph_response_table, ph_response_code = gsheets.values.sheet_values_for(
            self.sandhi_gsheet, MACROS_SHEET_NAME, 
            pargs={'idType':'title', 'valuesFormat':'maps'})
        
        ph_maps_list = ph_response_table.get('values', [])
        for amap in ph_maps_list:
            vals = amap.get('value', '').split()
            chars = reduce(lambda x, y: x and y, [len(x) > 1 for x in vals])
            vals = "|".join(vals) if chars else "[" + "".join(vals) + "]"
            self.macros[amap.get('macro')] = vals

    def expand_macro(self, matchObj):
        [op, parms] = matchObj.group(1).split(':')
        if op == 'M':
            if parms in self.macros:
                return self.macros[parms]
        return ""

    # Input and output is in SLP1 format
    def apply_overrides(self, pada1, pada2, shakha=None):
        results = []
        #print pada1, pada2
        for p in self.overrides:
            #print p
            if shakha and shakha not in p[3]:
                continue
            p1 = re.sub(r'__(.*?)__', self.expand_macro, p[0])
            m1 = re.match(p1, pada1)
            if not m1:
                continue
            p2 = re.sub(r'__(.*?)__', self.expand_macro, p[1])
            m2 = re.match(p2, pada2)
            if not m2:
                continue
            matches = [s for s in m1.groups()]
            matches.extend([s for s in m2.groups()])
            #print matches

            def subst_args(matchobj):
                return matches[int(matchobj.group(1))-1]
            samhita = re.sub(r'\$(\d+)', subst_args, p[2])

            def exec_expr(matchobj):
                return eval(matchobj.group(1))
            samhita = re.sub(r'__(.*?)__', exec_expr, samhita)

            esc_p = ['##' + v + '##' for v in p]
            res = {'praTamapadam' : pada1, 'dvitIyapadam' : pada2, 
                   'saMhitapadam' : samhita, 'apavAdaH' : esc_p }
            results.append(res)

        return results

    # Given two words in SLP1 format, produce their samhita form
    # along with the sandhi detected and the sutras and prakriya used.
    def join2(self, word1, word2, shakha=None):
        results = self.apply_overrides(word1, word2, shakha)
        if len(results) > 0:
            return results[0]

        args = ["perl", join(self.sclpath, "sandhi/mysandhi.pl")]
        args.extend(["WX", "any", 
            sanscript.transliterate(word1, sanscript.SLP1, sanscript.WX), 
            sanscript.transliterate(word2, sanscript.SLP1, sanscript.WX), 
            ])
        result = subprocess.check_output(args).decode('utf-8')
        #print(result)
        output = [sanscript.transliterate(re.sub('^:', '', val), \
            sanscript.WX, sanscript.SLP1) for val in result.split(",")]
        res=dict(zip(output[5:],output[0:5]))
        #print res
        return res

    # Given a list of words/morphemes, this function will join them according to
    # sandhi rules and give the final samhita word.
    def join(self, words, encoding, shakha=None, exceptions=None):
        samhita = sanscript.transliterate(words[0], encoding, sanscript.SLP1)
        analysis = []
        for w in words[1:]:
            w = sanscript.transliterate(w, encoding, sanscript.SLP1)
            res = self.join2(samhita, w)
            #print res
            if 'saMhitapadam' in res:
                samhita = res['saMhitapadam']
            analysis.append(res)
                
            #print samhita

        analysis_str = sanscript.transliterate(json.dumps(analysis), 
            sanscript.SLP1, encoding)
        analysis = json.loads(analysis_str)
        samhita = sanscript.transliterate(samhita, sanscript.SLP1, encoding)
        return {'words' : words, 'result' : samhita, 'analysis' : analysis }

if __name__ == "__main__":
    encoding = sys.argv[1].upper()
    encoding = eval('sanscript.' + encoding)
    sys.path.append(join(dirname(realpath(__file__)), "../.."))

    sandhi = SandhiJoiner(sclpath="/home/samskritam/scl-dev-local/build", 
        sandhi_gsheet_id='1yP82Y5d5mGrvNV2e-OPc6rBhPEtTYWI2vEwYN7uZdnU')
    while (1):
        try:
            line = str(raw_input('Words to join: '))
        except:
            break
        words = line.rstrip("\n").split()
        res = sandhi.join(words, encoding)
        print(json.dumps(res, indent=4, ensure_ascii=False, separators=(',', ': ')))

__all__ = ['SandhiJoiner']
