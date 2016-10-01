import cv2
import numpy as np
import preprocessing
import sys, os
import json
from operator import itemgetter, attrgetter
from pprint import pprint


class DotDict(dict):
    def __getattr__(self, name):
        return self[name] if name in self else None
    def __setattr__(self, name, value):
        self[name] = value

# Represents a rectangular image segment
class ImgSegment(DotDict):
    # Two segments are 'equal' if they overlap
    def __eq__(self, other):
        xmax = max(self.x, other.x)
        ymax = max(self.y, other.y)
        w = min(self.x+self.w, other.x+other.w) - xmax
        h = min(self.y+self.h, other.y+other.h) - ymax
        return w > 0 and h > 0

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        if self == other:
            print str(self) + " overlaps " + str(other)
            return 0
        elif (self.y < other.y) or ((self.y == other.y) and (self.x < other.x)):
            return -1
        else:
            return 1
    def __str__(self):
        mystr = "(" + \
            ", ".join(map(lambda p: json.dumps(self[p]) if p in self else "", \
                            ["x", "y", "w", "h", "score", "state", "text"])) \
            + ")"
        return mystr.encode('utf-8')

class DisjointSegments:
    segments = []

    def __init__(self, segments = []):
        self.segments = []
        self.merge(segments)

    def to_rect(self, seg):
        return DotDict(seg)

    def intersection(self, a, b):
        x = max(a.x, b.x)
        y = max(a.y, b.y)
        w = min(a.x+a.w, b.x+b.w) - x
        h = min(a.y+a.h, b.y+b.h) - y
        return w > 0 and h > 0
        #if w<=0 or h<=0: return () # or (0,0,0,0) ?
        #return (x, y, w, h)

    def overlap(self, testseg):
        #testrect = self.to_rect(testseg)
        for i in range(len(self.segments)):
            if self.segments[i] == testseg:
                return i
        return -1

    def insert(self, newseg):
        #print "Inserting " + str(newseg)
        i = self.overlap(newseg)
        if i >= 0:
            if self.segments[i].score >= newseg.score:
                #print "Skipping " + str(newseg) + " < " + str(self.segments[i])
                return False
            else:
                self.remove(i)
                #for r in self.segments:
                #    print "->  " + str(r)
        #print "--> at " + str(len(self.segments))
        self.segments.append(newseg)
        return True

    def merge(self, segments):
        merged = [r for r in segments if self.insert(r)]
        return merged

    def get(self, i):
        return self.segments[i] if i >= 0 and i < len(self.segments) else None

    def remove(self, i):
        #print "deleting " + str(i) + "(" + str(len(self.segments)) + "): " + str(self.segments[i])
        if i >= 0 and i < len(self.segments):
            del self.segments[i]

class DocImage:
    fname = ""
    img_rgb = None
    img_gray = None
    w = 0
    h = 0

    def __init__(self, imgfile = None):
        if imgfile:
            #print "DocImage: loading ", imgfile
            self.fromFile(imgfile)

    def fromFile(self, imgfile):
        self.fname = imgfile
        self.img_rgb = cv2.imread(self.fname)
        self.init()

    def init(self):
        self.img_gray = cv2.cvtColor(self.img_rgb, cv2.COLOR_BGR2GRAY)
        self.img_bin = preprocessing.binary_img(self.img_gray)
        self.w, self.h = self.img_gray.shape[::-1]
        #print "width = " + str(self.w) + ", ht = " + str(self.h)

    def fromImage(self, img_cv):
        self.img_rgb = img_cv
        self.init()

    def save(self, dstfile):
        cv2.imwrite(dstfile, self.img_rgb)

    def find_matches(self, template_img, thres = 0.7, known_segments = None):
        res = cv2.matchTemplate(self.img_bin,  template_img.img_bin, cv2.TM_CCOEFF_NORMED )
   
        loc = np.where(res >= float(thres))
        matches = [ImgSegment({ 'x' : pt[0], 'y' : pt[1], \
                        'w' : template_img.w, 'h' : template_img.h, \
                        'score' : float("{0:.2f}".format(res[pt[1], pt[0]])) \
                        }) \
                    for pt in zip(*loc[::-1])]

        if known_segments is None:
            known_segments = DisjointSegments()
        disjoint_matches = known_segments.merge(matches)
        known_segments.segments.sort()
        #for r in known_segments.segments:
        #   print str(r)
        return disjoint_matches

    def find_recurrence(self, r, thres = 0.7, known_segments = None):
        #print "Searching for recurrence of " + json.dumps(r)

        template_img = self.img_rgb[r.y:(r.y+r.h), r.x:(r.x+r.w)]
        template = DocImage()
        template.fromImage(template_img)

        if known_segments is None:
            known_segments = DisjointSegments()
        known_segments.insert(ImgSegment(r))
        return self.find_matches(template, thres, known_segments)
   
    def self_to_image(self):
        return self.img_rgb

    def find_segments(self, show_int, pause_int, known_segments = None):

        img = self.img_gray
        
        kernel1 = np.ones((2,2),np.uint8)
        kernel2 = np.ones((1,1),np.uint8)

        all_heights = [] 
        
        
        def show_img(name, fname):
            if int(show_int) != 0:
                cv2.imshow(name, fname)
            if int(pause_int) != 0:
                cv2.waitKey(0)
        
        show_img('Output0',img)

        boxes_temp = np.zeros(img.shape[:2],np.uint8)
        print "boxes generated"

        binary = preprocessing.binary_img(img)
        show_img('BinaryOutput',binary)        
        
        dilation = cv2.dilate(binary,kernel1,iterations = 1)
        show_img('Dilation', dilation)
        
        erosion = cv2.dilate(dilation,kernel1,iterations = 1)
        show_img('Erosion', erosion)

        edges = cv2.Canny(dilation,50,100)
        show_img('Edges', edges)

        dilation2 = cv2.dilate(edges,kernel1,iterations = 1)
        show_img('Dilation9999', dilation2)
        
        inv9999 = 255-dilation2
        show_img('inv9999', inv9999)

        edges = cv2.dilate(edges,kernel1,iterations = 1)
        ret,thresh = cv2.threshold(erosion,127,255,0)
        contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            x,y,w,h = cv2.boundingRect(c)
            #annotate(boxes_temp,(255,255,255),-1)
            if h> 10:
                all_heights.append(h)

        std_dev = np.std(all_heights)
        mn = np.mean(all_heights)
        md = np.median(all_heights)

        for xx in contours:
            cv2.drawContours(edges,[xx],-1,(255,255,255),-1)
        
        show_img('edges2',edges)

        ret,thresh = cv2.threshold(erosion,127,255,0)
        contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            x,y,w,h = cv2.boundingRect(c)
            #if (mn+(std_dev/2)<h):
            cv2.rectangle(boxes_temp,(x,y),(x+w,y+h),(255,0,0),-1)
            #annotate(img,(255,0,0),2)
        
        show_img('boxes_temp',boxes_temp)
        
        ret,thresh = cv2.threshold(boxes_temp,127,255,0)
        contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        
        allsegments = []
        
        for c in contours:
            coordinates = DotDict({'x': 0, 'y':0, 'h':0, 'w':0, 'score':float(0.0)})
            x,y,w,h = cv2.boundingRect(c)
            coordinates['x'] = x
            coordinates['y'] = y
            coordinates['w'] = w
            coordinates['h'] = h
            allsegments.append(ImgSegment(coordinates))

        if known_segments is None:
            known_segments = DisjointSegments()
        disjoint_matches = known_segments.merge(allsegments);
        
        # print "Disjoint Segments = " + json.dumps(disjoint_matches)
        return disjoint_matches

    def annotate(self, sel_areas, color = (0,0,255),thickness = 2):      
        for rect in sel_areas:
            cv2.rectangle(self.img_rgb, (rect['x'], rect['y']), \
                (rect['x'] + rect['w'], rect['y'] + rect['h']), color, thickness)

def main(args):
    img = DocImage(args[0])
    rect = DotDict({ 'x' : int(args[1]), \
             'y' : int(args[2]), \
             'w' : int(args[3]), 'h' : int(args[4]), 'score' : float(1.0) })
    print "Template rect = " + json.dumps(rect)
    matches = img.find_recurrence(rect, 0.7)
    pprint(matches)
    print "Total", len(matches), "matches found."

    #print json.dumps(matches)
    img.annotate(matches)
    img.annotate([rect], (0,255,0))

    cv2.namedWindow('Annotated image', cv2.WINDOW_NORMAL)
    cv2.imshow('Annotated image', img.img_rgb)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    sys.exit(0)

def mainTEST(arg):
    img = DocImage(arg)
    img.annotate(img.find_segments(0,0))
    
    screen_res = 1280.0, 720.0
    scale_width = screen_res[0] / img.w
    scale_height = screen_res[1] / img.h
    scale = min(scale_width, scale_height)
    window_width = int(img.w * scale)
    window_height = int(img.h * scale)

    cv2.namedWindow('Final image', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Final image', window_width, window_height)

    cv2.imshow('Final image', img.img_rgb)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    

if __name__ == "__main__":
    #main(sys.argv[1:])
    mainTEST(sys.argv[1])

