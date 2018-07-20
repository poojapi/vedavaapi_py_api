import subprocess
import sys
import re
import json
from os.path import join
from indic_transliteration import sanscript
from vedavaapi.sling import get_service()

# Given two words in WX format, this word produces their samhita form in WX form
# along with the sandhi detected and the sutras and prakriya used.
def sandhi_join2_wx(word1, word2):
    sclpath = get_service().config['scl_path']
    args = ["perl", join(sclpath, "sandhi/mysandhi.pl")]
    args.extend(["WX", "any", word1, word2])
    result = subprocess.check_output(args).decode('utf-8')
    output = [re.sub('^:', '', val) for val in result.split(",")]
    res=dict(zip(output[5:],output[0:5]))
    #print res
    return res

# Given a list of words/morphemes, this function will join them according to sandhi rules
# and give the final samhita word.
def sandhi_join(words, encoding, shakha=None, exceptions=None):
    samhita = sanscript.transliterate(words[0], encoding, sanscript.WX)
    analysis = []
    for w in words[1:]:
        w = sanscript.transliterate(w, encoding, sanscript.WX)
        res = sandhi_join2_wx(samhita, w)
        #print res
        if 'saMhiwapaxam' in res:
            samhita = res['saMhiwapaxam']
        analysis.append(res)
            
        #print samhita

    analysis_str = sanscript.transliterate(json.dumps(analysis), sanscript.WX, encoding)
    analysis = json.loads(analysis_str)
    samhita = sanscript.transliterate(samhita, sanscript.WX, encoding)
    return {'words' : words, 'result' : samhita, 'analysis' : analysis }

if __name__ == "__main__":
    encoding = sys.argv[1].upper()
    encoding = eval('sanscript.' + encoding)
    samhita = sandhi_join(sys.argv[2:], encoding)
    print(json.dumps(samhita, indent=4, ensure_ascii=False, separators=(',', ': ')))

__all__ = ['sandhi_join']
