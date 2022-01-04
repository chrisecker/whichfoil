# -*- coding:latin-1 -*-

"""
Attempt to make it easier to deal with coordinates and transformations in wx.
"""

import math
import wx

from math import sqrt
from copy import copy

from wx import Point, Rect


### Methods for Size ###
def grown(size, dx, dy):
    r = wx.Size(*size)
    r.IncBy(dx, dy)
    return r    
wx.Size.Grown = grown

### Methods for Rect ###
def center(rect):
    position = rect.Position
    w, h = rect.Size
    return position+(w/2, h/2)
wx.Rect.Center = center

def moved(rect, point):
    r = wx.Rect(*rect)
    r.Position += wx.Point2D(*point)
    return r    
wx.Rect.Moved = moved

def grown(rect, dx, dy):
    r = wx.Rect(*rect)
    r.Inflate(dx, dy)
    return r    
wx.Rect.Grown = grown

def contains_any(rect, point_or_rect):
    if isinstance(point_or_rect, wx.Rect):
        return rect.ContainsRect(point_or_rect)
    return rect.ContainsXY(*point_or_rect)        
wx.Rect.__contains__ = contains_any

def area(rect):
    w, h = rect.Size
    return w*h
wx.Rect.Area = property(area)

def _ge(rect, other):
    return rect.Area >= other.Area
wx.Rect.__ge__ = _ge
    
def _gt(self, other):
    return self.Area > other.Area
wx.Rect.__gt__ = _gt
    
def _le(self, other):
    return self.Area <= other.Area
wx.Rect.__le__ = _le
    
def _lt(self, other):
    return self.Area < other.Area
wx.Rect.__lt__ = _lt
        
def _transform_rect(self, matrix):
    # XXX Does not work anymore. FIX THIS
    return wx.Rect(
        matrix.TransformPoint(self.Left, self.Bottom), 
        matrix.TransformPoint(self.Right, self.Top))
wx.Rect.Transformed = _transform_rect



### Methods for Point2D ###

def sub(point, other):
    return wx.Point2D(point[0]-other[0], point[1]-other[1])
wx.Point2D.__sub__ = sub

def rsub(point, other):
    return wx.Point2D(other[0]-point[0], other[1]-point[1])
wx.Point2D.__rsub__ = rsub

def add(point, other):
    return wx.Point2D(point[0]+other[0], point[1]+other[1])
wx.Point2D.__add__ = add

def radd(point, other):
    return wx.Point2D(other[0]+point[0], other[1]+point[1])
wx.Point2D.__radd__ = radd

def multiplied(point, f):
    x, y = point
    return wx.Point2D(f*x, f*y)
wx.Point2D.__mul__ = multiplied
wx.Size.__mul__ = multiplied
wx.Point2D.__rmul__ = multiplied
wx.Size.__rmul__ = multiplied

def divided(point, f):
    x, y = point
    return wx.Point2D(x/f, y/f)
wx.Point2D.__div__ = divided
wx.Size.__div__ = divided
wx.Point2D.__rdiv__ = divided
wx.Size.__rdiv__ = divided

def negated(point):
    x, y = point
    return wx.Point2D(-x, -y)
wx.Point2D.__neg__ = negated

def length(point):
    x, y = point
    return math.sqrt(x*x+y*y)
wx.Point2D.Length = length   

def polar(point):
    x,y = point
    return math.hypot(x, y), math.atan2(x,y)
wx.Point2D.Polar = polar

def normalized(point):
    x,y = point
    l = math.hypot(x, y)
    return wx.Point2D(x/l, y/l)
wx.Point2D.Normalized = normalized

def transformed(point, trafo):
    return wx.Point2D(*trafo.TransformPoint(*point))
wx.Point2D.Transformed = transformed    
        
def rounded(point):
    x, y = point
    return wx.Point2D(round(x), round(y))
wx.Point2D.Rounded = rounded

def dot(point, other):
    ax, ay = point
    bx, by = other
    return ax*bx+ay*by
wx.Point2D.Dot = dot

def dist_point_line(c, a, b):
    cx, cy = map(float, c)
    bx, by = map(float, b)
    ax, ay = map(float, a)

    """
    Let the point be C (Cx,Cy) and the line be AB (Ax,Ay) to (Bx,By).
    Let P be the point of perpendicular projection of C on AB.  The parameter
    r, which indicates P's position along AB, is computed by the dot product 
    of AC and AB divided by the square of the length of AB:
    
    (1)     AC dot AB
        r = ---------  
            ||AB||^2
    
    r has the following meaning:
    
        r=0      P = A
        r=1      P = B
        r<0      P is on the backward extension of AB
        r>1      P is on the forward extension of AB
        0<r<1    P is interior to AB
    
    The length of a line segment in d dimensions, AB is computed by:
    
        L = sqrt( (Bx-Ax)^2 + (By-Ay)^2 + ... + (Bd-Ad)^2)

    so in 2D:   
    
        L = sqrt( (Bx-Ax)^2 + (By-Ay)^2 )
    
    and the dot product of two vectors in d dimensions, U dot V is computed:
    
        D = (Ux * Vx) + (Uy * Vy) + ... + (Ud * Vd)
    
    so in 2D:   
    
        D = (Ux * Vx) + (Uy * Vy) 
    
    So (1) expands to:
    
            (Cx-Ax)(Bx-Ax) + (Cy-Ay)(By-Ay)
        r = -------------------------------
                          L^2

    The point P can then be found:

        Px = Ax + r(Bx-Ax)
        Py = Ay + r(By-Ay)

    And the distance from A to P = r*L.

    Use another parameter s to indicate the location along PC, with the 
    following meaning:
           s<0      C is left of AB
           s>0      C is right of AB
           s=0      C is on AB

    Compute s as follows:

            (Ay-Cy)(Bx-Ax)-(Ax-Cx)(By-Ay)
        s = -----------------------------
                        L^2


    Then the distance from C to P = |s|*L.

    """

    r_numerator = (cx-ax)*(bx-ax) + (cy-ay)*(by-ay)
    r_denomenator = (bx-ax)*(bx-ax) + (by-ay)*(by-ay)
    r = r_numerator / r_denomenator

    px = ax + r*(bx-ax)
    py = ay + r*(by-ay)

    s =  ((ay-cy)*(bx-ax)-(ax-cx)*(by-ay) ) / r_denomenator

    distanceLine = abs(s)*sqrt(r_denomenator)

    #
    # (xx,yy) is the point on the lineSegment closest to (cx,cy)
    #
    xx = px
    yy = py

    if (r >= 0) and (r <= 1):
        distanceSegment = distanceLine
    else:
        dist1 = (cx-ax)*(cx-ax) + (cy-ay)*(cy-ay)
        dist2 = (cx-bx)*(cx-bx) + (cy-by)*(cy-by)
        if (dist1 < dist2):
            xx = ax
            yy = ay
            distanceSegment = sqrt(dist1)
        else:
            xx = bx
            yy = by
            distanceSegment = sqrt(dist2)
    return distanceSegment

        
class PointArray:

    _data = None # eine Liste von Points
    def __init__(self, data=None):
        if data is not None:
            if isinstance(data, PointArray):
                self._data = data._data
            else:
                d = []
                d.extend(data)
                self._data = d
        else:
            self._data = []
        
    def __delitem__(self, i):
        del self._data[i]
        
    def __getitem__(self, i):
        return self._data[i]
        
    def __len__(self):
        return len(self._data)
        
    def Insert(self, i, point):
        self._data.insert(i, wx.Point2D(*point))
        
    def Append(self, p):
        self.Insert(len(self._data), p)
        
    def Transformed(self, trafo):
        r = []
        tranformed = trafo.TransformPoint
        for point in self._data:
            r.append(transformed(point))
        return PointArray(data=r)
        
    def GetBounds(self):
        data = self._data
        if not len(data):
            return wx.Rect()            
        point = data[0]
        xmin = xmax = point[0]
        ymin = ymax = point[1]        
        for point in data[1:]:
            xmin = min(xmin, point[0])
            xmax = max(xmax, point[0])
            ymin = min(ymin, point[1])
            ymax = max(ymax, point[1])            
        return wx.Rect(xmin, ymin, xmax, ymax)
    
        
        

class MatrixFactory:
    def __init__(self):
        dc = wx.MemoryDC()
        bmp = wx.EmptyBitmap(0, 0)
        dc.SelectObject(bmp)
        # https://wxpython.org/Phoenix/docs/html/wx.MemoryDC.html
        # A bitmap must be selected into the new memory DC before it
        # may be used for anything.
        self.gc = wx.GraphicsContext.Create(dc)

    def CreateMatrix(self, *args, **kwds):
        return self.gc.CreateMatrix(*args, **kwds)

_MATRIXFACTORY = None
def create_matrix(*args, **kwds):
    global _MATRIXFACTORY
    if _MATRIXFACTORY is None:
        _MATRIXFACTORY = MatrixFactory()
    return _MATRIXFACTORY.CreateMatrix(*args, **kwds)
    
### Matrix methods ###    
def _M__repr__(matrix, *args):
    return "Matrix"+repr(matrix.Get())
wx.GraphicsMatrix.__repr__ = _M__repr__


def _M__call__(matrix, other):
    return other.Transformed(matrix)
wx.GraphicsMatrix.__call__ = _M__call__


def _MCopy(matrix):
    values = matrix.Get()
    m = create_matrix()
    m.Set(*values)
    return m
wx.GraphicsMatrix.Copy = _MCopy

def _MTransformed(self, m):
    r = self.Copy()
    r.Concat(m)
    return r
wx.GraphicsMatrix.Transformed = _MTransformed

def _MRotated(self, angle, center=(0, 0)):
    c = cos(angle)
    s = sin(angle)
    x, y = center
    t = create_matrix(c, +s, -s, c, s*y-c*x+x, -c*y-s*x+y)
    r = self.Copy()
    r.Concat(t)
    return r
wx.GraphicsMatrix.Rotated = _MRotated
    
def _MTranslated(self, p):
    r = self.Copy()
    r.Translate(*p)
    return r    
wx.GraphicsMatrix.Translated = _MTranslated

def _MScaled(self, f1, f2=None):
    r = self.Copy()
    if f2 is None:
        f2 = f1
    r.Scale(f1, f2)
    return r    
wx.GraphicsMatrix.Scaled = _MScaled

def _MZoomed(self, z, p):
    "Zoom with focus on point p"
    t = create_matrix(z, 0.0, 0.0, z, p[0]*(1-z), p[1]*(1-z))
    r = self.Copy()
    r.Concat(t)
    return r
wx.GraphicsMatrix.Zoomed = _MZoomed

def _MInverted(self):
    r = self.Copy()
    # XXX WX does not throw in exception if matrix is singular. Should be reported!
    r.Invert()
    return r    
wx.GraphicsMatrix.Inverted = _MInverted

          
def _eq(a, b):
    # compares values a and b
    return abs(a-b) < 1e-8

        
def test_00():
    "Matrix.Copy"
    f = MatrixFactory()
    m = f.CreateMatrix()
    m_ = m.Copy()
    p = x, y = wx.Point2D(1, 2)
    assert x == 1.0
    assert y == 2.0
    x, y = m.TransformPoint(*p)
    assert x == 1.0
    assert y == 2.0
    m2 = m.Rotated(45*math.pi/180.0)
    x, y = m2.TransformPoint(*p)
    assert _eq(x, -2.0)
    assert _eq(y, 1.0)
    assert m.IsIdentity()
    assert not m2.IsIdentity()


def test_01():
    "Matrix.__call__"
    m = create_matrix().Translated((100, 0)).Rotated(10*3.141592/180.0)

    # transform a point
    p = wx.Point2D(0, 0)
    #print m(p)

    # transform a matrix
    m_ = create_matrix().Translated((100, 0))
    #print m(m_)
    
    # transform a rect
    #r = wx.Rect(0, 0, 100, 200)
    #print m(r)

    

def test_02():
    deg = 3.141592/180.0
    t1 = IDENTITY.Translate((0, 0)).Rotate(10*deg)    
    t2 = IDENTITY.Rotate(10*deg)
    print (t1)
    print (t2)
    assert repr(t1) == repr(t2)
    
if __name__ == '__main__':
    app = wx.App()
