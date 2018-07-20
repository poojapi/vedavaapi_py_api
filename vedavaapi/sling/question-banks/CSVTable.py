import csv;

class CSVTable:
    def reopen(self):
        self.close()        
        self.fileobj = open(self.fname,'ab')
        self.csvwriter = csv.writer(self.fileobj, delimiter = ',', lineterminator='\n')    
        self.rows = None
           
    def __init__(self, csvfile, create=False):
        self.colindices = {}
        self.colnames = []
        self.select_colnames = []
        self.select_colids = []
        self.rows = []
        self.fname = csvfile
        
        #Reading the required columns from the input CSV file
        self.csvreader = None
        self.csvwriter = None
        self.fileobj = None
        if (create):
            self.fileobj = open(csvfile, 'wb')
            self.csvwriter = csv.writer(self.fileobj, delimiter = ',', lineterminator='\n')
        else:
            self.fileobj = open(csvfile, 'rb')
            csvreader = csv.reader(self.fileobj, delimiter = ',')
            for row in csvreader:
                row[0] = row[0].strip('#')
                self.colindices = dict(zip(row, range(0, len(row))))
                self.colnames = row
                self.select_colnames = row
                break;
        print self.colnames
        self.rows = None

    def select_cols(self, cols):
        missingcols = filter(lambda c: not c in self.colindices, cols)
        if missingcols:
            print "Error: Missing columns " + ','.join(missingcols) + \
                " in file " + self.fname
            sys.exit(1)

        self.select_colnames = cols

        self.select_colids = map(lambda x: self.colindices[x], self.select_colnames)
        #print str(self.select_colids) + "column ids"
        if not self.select_colids:
            return

# import data from centroid file
#    def importAll(self):
#        self.rows = np.genfromtxt(self.fname, delimiter =',')
#        print "Importing columns " + str(self.select_colids) + " from " + self.fname
#        self.rows = self.rows[:,self.select_colids]
        

    def __iter__(self):
        j=0
        if self.rows is None:
        
            fileobj = open(self.fname, "rb")
            
            for row in csv.reader(fileobj, delimiter=","):
                # Skip commented lines
                if (row[0].startswith('#')): 
                    continue
                #print "row in iter "+ str(row) + "  "+str(j)
                reducedrow = map(lambda i: float(row[i]), self.select_colids)
                yield reducedrow
                j=j+1
            fileobj.close()
            fileobj = None
          
        else:
            for row in self.rows:
                yield row
      
    def write_header(self, hdr):
        self.csvwriter.writerow(hdr)

    def append(self, row):
#        trunc_row = map(
#                lambda x: x if (x == math.floor(x))  
#                            else math.floor((x + 0.0005)* 1000)/1000.0, 
#                row)
        self.csvwriter.writerow(trunc_row)

    def close(self):
        if not self.fileobj is None:
            self.fileobj.close()
            self.fileobj = None


