# -*- coding: latin-1 -*-


class ParseError(Exception):
    pass
    

def is_coord(l):
    try:
        x, y = [float(s) for s in l.split()]
        return True
    except:
        return False


def ascending(l):
    """Returns True if the values in l are in ascending order"""
    last = None
    for x in l:
        if last is not None and x<last:
            return False
        last = x
    return True


def descending(l):
    """Returns True if the values in l are in descending order"""
    last = None
    for x in l:
        if last is not None and x>last:
            return False
        last = x
    return True    


def load_airfoil(p):
    f = open(p)
    next = f.readline

    l = next()
    comments = []
    values = []    
    while True:
        s = l.strip()
        if s:
            if is_coord(l): 
                x, y = [float(s) for s in l.split()]
                values.append((x, y))
                break
            else:
                comments.append(s)
        l = next()
    
    for l in f:
        if not l.strip():
            continue
        if not is_coord(l):
            continue # raise ParseError("Expected coordinate tuple: "+repr(l))
        x, y = [float(s) for s in l.split()]
        values.append((x, y))

    px, py = values[0]
    if px>1.5 or py > 1.5: # assume Letnicer's format
    
        # Lednicer's format lists points on the upper surface (from leading
        # edge to trailing edge), then points on the lower surface (from
        # leading edge to trailing edge). 

        nupper, nlower = int(px), int(py)
        upper = values[1:nupper+1]
        lower = values[nupper+1:]
        values = upper+lower
        upper.reverse()
        values = lower+upper
    else:
        # assume Selig's format

        # Selig's format starts from the trailing edge of the airfoil,
        # goes over the upper surface, then over the lower surface, to
        # go back to the trailing edge.

        pass # nothing to do

    # remove values outside -0.001 ... 1.001
    coordinates = [p for p in values if p[0]>-0.001 and p[0]<1.001]
    xv, yv = zip(*coordinates)
    return '\n'.join(comments), (xv, yv)
    

def _interpolate(x, x1, x2, y1, y2):
    if not (x1 <= x <= x2):
        raise ValueError(x, x1, x2)
    return y1+(y2-y1)/(x2-x1)*(x-x1) 

def interpolate_airfoil(t, xv, yv):
    """Determines the intersection of the profile coordinates with x=t

    Returns a tuple (upper, lower).
    """
    if t<0 or t>1:
        raise ValueError(t)
    l = []
    ax = None
    for i, x in enumerate(xv):
        if ax is not None:
            if (ax<t and t<=x): 
                ty = _interpolate(t, ax, x, yv[i-1], yv[i])
                l.append(ty)        
            elif (x<t and t<=ax): 
                ty = _interpolate(t, x, ax, yv[i], yv[i-1])
                l.append(ty)        
        ax = x
    return l
