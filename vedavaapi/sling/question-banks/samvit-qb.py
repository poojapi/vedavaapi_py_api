from pprint import pprint
import re
import sys
import csv
from CSVTable import *

if __name__ == "__main__":
    fname = sys.argv[1]
    qb = CSVTable(fname)
        
    print qb.colnames
