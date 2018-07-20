from config import *
from rules import *

wdesc = { 'word' : 'yAnam', 'encoding' : 'Itrans' }

all_mods = { 'vibhakti' : [1,2,3,4,5,6,7], 'vachana' : ['eka'] }
correct_mods = { 'vibhakti' : [1,2], 'vachana' : ['eka'] }

initworkdir(True)

correct = [w for w in SktTemplate.word_forms(wdesc, correct_mods)]

options = SktTemplate.word_options(wdesc, all_mods, correct_mods)
print options
