
def permutations(options, start = 0, stop = 0):
    if stop == 0:
        stop = len(options)
    if start >= stop: 
        yield []
        return
    #print "{}: start = {}, stop = {}".format(self.name, start, stop)
    vals = options[start] if hasattr(vals, '__iter__') else [options[start]]
    for v in vals:
        #print (' ' * start) + str(v) + " ==> "
        if start+1 < stop:
            for x in permutations(options, start+1, stop):
                yield [v] + x
        else:
            yield [v]
    return

x = "sai"

x = (i for i in [['a', 'b']])
print x

if hasattr(x, '__iter__'):
    for i in permutations(x):
        print i
else:
    print "scalar: " + str(x)
