# -*- coding: latin-1 -*-


def load_airfoil(p, warnings=None):
    if warnings is None:
        warnings = []
    xl = []
    yl = []
    name = None
    for l in open(p):
        s = l.strip()
        if not s: 
            continue
        if name is None:
            name = s
            continue
        #print l
        try:
            xs, ys = l.split()
            xs = float(xs)
            ys = float(ys)
        except:
            warnings.append((p, repr(l)))
            continue
        xl.append(xs)
        yl.append(ys)
    return xl, yl
