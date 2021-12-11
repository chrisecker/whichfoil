# -*- coding:latin-1 -*-

"""
Variante der affinen Geometry, die sich in wx integriert. Es werden 
Point, Rect und Size von wx verwendet. Es ist zu beachten, dass
Koordinaten in Wx immer aus ganzen Zahlen bestehen.

Der Trafo kann auch mit Float-Koordinaten umgehehn, wenn sie als Tupel
übegeben werden: trafo.TransformPoint((1.3, 2.1))
"""

import math
import wx

from math import sqrt
from copy import copy

from wx import Point, Rect


# Methoden für Size
def grown(size, dx, dy):
    r = wx.Size(*size)
    r.IncBy(dx, dy)
    return r    
wx.Size.Grown = grown

# Methoden für Rect
def center(rect):
    position = rect.Position
    w, h = rect.Size
    return position+(w/2, h/2)
wx.Rect.Center = center

def moved(rect, point):
    r = wx.Rect(*rect)
    r.Position += wx.Point(*point)
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
        


# Methoden für Point
# ACHTUNG:
#
# wx.Point is immutable. "point += xxx" kann zu abstürzen führen
def multiplied(point, f):
    x, y = point
    return wx.Point(f*x, f*y)
wx.Point.__mul__ = multiplied
wx.Size.__mul__ = multiplied
wx.Point.__rmul__ = multiplied
wx.Size.__rmul__ = multiplied

def divided(point, f):
    x, y = point
    return wx.Point(x/f, y/f)
wx.Point.__div__ = divided
wx.Size.__div__ = divided
wx.Point.__rdiv__ = divided
wx.Size.__rdiv__ = divided

def negated(point):
    x, y = point
    return wx.Point(-x, -y)
wx.Point.__neg__ = negated

def length(point):
    x, y = point
    return math.sqrt(x*x+y*y)
wx.Point.Length = length   

def polar(point):
    x,y = point
    return math.hypot(x, y), math.atan2(x,y)
wx.Point.Polar = polar

def normalized(point):
    x,y = point
    l = math.hypot(x, y)
    return wx.Point(x/l, y/l)
wx.Point.normalized = normalized

def transformed(point, trafo):
    return trafo.TransformPoint(point)
wx.Point.Transformed = transformed    
        
def rounded(point):
    x, y = point
    return wx.Point(round(x), round(y))
wx.Point.Rounded = rounded


def xxdist_point_line(p, a, b):
    """Berechnet den Abstand zwischen dem Punkt p und dem Segment ab
    
       p, a und b brauchen keine Punkte zu sein
    """
    x1, y1 = a
    x2, y2 = b
    x3, y3 = p
    u = ((x3-x1)*(x2-x1)+(y3-y1)*(y2-y1))/sqrt((x2-x1)**2+(y2-y1)**2)
    
    x = x1 + u*(x2-x1)
    y = y1 + u*(y2-y1)     
    
    return sqrt((x-x3)**2+(y-y3)**2)
    

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

        
class _PointArray:

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
    
class FloatPointArray(_PointArray):
    """
    Die Punkte werden nicht als Integer, sondern als Float abgespeichert.
    """
    def Insert(self, i, point):        
        x, y = point
        self._data.insert(float(x), float(y))

    def Transformed(self, trafo):
        r = []
        tranformed = trafo.TransformPointFloat
        for point in self._data:
            r.append(transformed(point))
        return PointArray(data=r)
        
    def Rounded(self):
        data = [wx.Point(round(x), round(y)) for x, y in self._data]
        return IntPointArray(data)
        
        
        
class IntPointArray(_PointArray):
    def Insert(self, i, point):
        self._data.insert(i, wx.Point(*point))
        
PointArray = IntPointArray

        
class SingularMatrix(Exception):
    pass

class Trafo(object):
    """
Trafo implements a 2D affine transformation T:
 
           / x \   / m11 m12 \ / x \   / v1 \
       T * |   | = |         | |   | + |    |
           \ y /   \ m21 m22 / \ y /   \ v2 /
 
 
or, in homogeneous coordinates:
 
                    / m11 m12 v1 \ / x \
                    |            | |   |
                 ^= | m21 m22 v2 | | y |
                    |            | |   |
                    \ 0   0   1  / \ 1 /

Code is based on Sketch 0.6.17
"""

    def __init__(self, m11, m12, m21, m22, v1, v2):
        self.m11 = float(m11)
        self.m12 = float(m12)
        self.m21 = float(m21)
        self.m22 = float(m22)
        self.v1 = float(v1)
        self.v2 = float(v2)
        
    def __repr__(self):
        return "Trafo(%.10g, %.10g, %.10g, %.10g, %.10g, %.10g)" % \
               (self.m11, self.m12, self.m21, self.m22, self.v1, self.v2)

    def __cmp__(self, t):
        if self.m11 == t.m11 and self.m12 == t.m12 and \
           self.m21 == t.m21 and self.m22 == t.m22 and \
           self.v1 == t.v1 and self.v2 == t.v2:
            return 1
        return cmp(id(self), id(t))
    
    def __call__(self, *args):
        if len(args) == 1:
            p = args[0]
            return p.Transformed(self)

    def Get(self):
        return self.m11, self.m12, self.m21, self.m22, self.v1, self.v2

    def TransformPoint(self, p):
        # Note that wx points are based on integers. If you do not
        # want that, use TransformPointFloat. ... I know!
        x, y = p
        return wx.Point(self.m11 * x + self.m12 * y + self.v1,
                        self.m21 * x + self.m22 * y + self.v2)
                     
    def TransformPointFloat(self, p):
        x, y = p
        return (self.m11 * x + self.m12 * y + self.v1,
                self.m21 * x + self.m22 * y + self.v2)
                     
    def TransformRect(self, r):
        return wx.Rect(
            self.transform_xy(r.Left, r.Bottom), 
            self.transform_xy(r.Right, r.Top))

    def TransformTrafo(self, t):
        return Trafo(self.m11*t.m11 + self.m12*t.m21,
                     self.m21*t.m11 + self.m22*t.m21,
                     self.m11*t.m12 + self.m12*t.m22,
                     self.m21*t.m12 + self.m22*t.m22,
                     self.m11*t.v1 + self.m12*t.v2 +self.v1,
                     self.m21*t.v1 + self.m22*t.v2 +self.v2)

    def Transformed(self, trafo):
        return trafo.TransformTrafo(self)

    def Rotate(self, angle, center=(0, 0)):
        return Rotation(angle, center).TransformTrafo(self)

    def Translate(self, p):
        return Translation(p).TransformTrafo(self)

    def Scale(self, f1, f2=None):
        return Scale(f1, f2).TransformTrafo(self)
                     
    def Inverse(self):
        det = float(self.m11 * self.m22 - self.m12 * self.m21)
        #print "det=", det

        if det == 0.0:
            raise SingularMatrix("inverting singular matrix")
        
        m11 = self.m22 / det
        m12 = -self.m12 / det
        m21 = -self.m21 / det
        m22 = self.m11 / det

        r = Trafo(m11, m12, m21, m22,
                  -m11 * self.v1 - m12 * self.v2,
                  -m21 * self.v1 - m22 * self.v2);
        return r
          

IDENTITY = Trafo(1.0, 0, 0, 1.0, 0, 0)


class Scale(Trafo):
    def __init__(self, f1, f2=None):
        if f2 is None:
            f2 = f1
        Trafo.__init__(self, float(f1), 0, 0, float(f2), 0, 0)
        

class Translation(Trafo):
    def __init__(self, p):
        Trafo.__init__(self, 1., 0,0,1., p[0], p[1])

        
class Rotation(Trafo):
    def __init__(self, angle, center = (0,0)):
        s = math.sin(angle)
        c = math.cos(angle)
        cx, cy = center
        
        # compute offset.
        # The rotation around center is
        # T(p) = center + M * (p - center)
        # => offset = center - M * center
     
        offx = cx - c * cx + s * cy
        offy = cy - s * cx - c * cy

        Trafo.__init__(self, c, s, -s, c, offx, offy)

        
def test_00():
    p = wx.Point(1, 2)
    print 2*p
    print p*2
    print p/2
    print p/2.0
    
    trafo = Translation((2, 5))
    print trafo(p)
    
    inv = trafo.Inverse()
    print inv(trafo(p))

    size = wx.Size(10, 10)
    size2 = size.Grown(3, 4)
    w, h = size2
    print w, h    
    print wx.Rect(10, 10, 40, 30).Center()


def test_01():
    t = IDENTITY.Translate((100, 0)).Rotate(0.25*3.141592)    
    p = wx.Point(0.0, 0.0)
    x, y =  t.TransformPointFloat((0.0, 0.0))
    assert x>70
    assert y<-70
    
if __name__ == '__main__':
    test_01()
