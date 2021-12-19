# -*- coding: latin-1 -*-

from __future__ import absolute_import
import sys
import wx
import math
from math import sin, cos, pi, sqrt
try:
    from StringIO import StringIO ## for Python 2
except ImportError:
    from io import BytesIO as StringIO ## for Python 3


from . import geometry
from .viewbase import ViewBase


def overridable_property(name, doc = None):
    setter_name = 'set_' + name
    return property(
        lambda self: getattr(self, '_'+name),
        lambda self, value: getattr(self, setter_name)(value),
        None,
        doc)


def dist(p1, p2):
    return sqrt((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)
    



class Canvas(wx.Window, ViewBase):
    zoom = overridable_property('zoom')
    shift = overridable_property('shift')
    transient = overridable_property('transient')
    _zoom = 1.0
    _shift = 0.0, 0.0
    _transient = None
    bmp = None
    def __init__(self, *args, **kwds):
        ViewBase.__init__(self)
        wx.Window.__init__(self, *args, **kwds)
        
        self.SetBackgroundColour('white')
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda e: None)
        
        self.Bind(wx.EVT_MOUSE_EVENTS, self.mouse_event)
        #self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.capturelost_event)
        
        self.SetFocus()

    def model_added(self, model):
        self.bmp_changed(model, None)
        
    def bmp_changed(self, model, old):
        bmp = model.bmp
        if bmp is None:
            self.bmp = None
        else:
            f = StringIO(bmp)
            im = wx.ImageFromStream(f)
            self.bmp = im.ConvertToBitmap()
        self.Refresh()

    def alpha_changed(self, model, old):
        #print("alpha changed")

        # update shift etc.
        if self.bmp is not None:
            alpha = self.model.alpha
            zoom = self.model.zoom
            trafo =  geometry.IDENTITY.Rotate(alpha).Scale(zoom, zoom)
            w, h = self.bmp.Size
            l = (0, 0), (w, 0), (w, h), (0, h)
            l_ = [trafo.TransformPointFloat(p) for p in l]
            minx = min([p[0] for p in l_])
            miny = min([p[1] for p in l_])
            maxx = max([p[0] for p in l_])
            maxy = max([p[1] for p in l_])
            #self.shift = minx, miny
        self.Refresh()

    def zoom_changed(self, model, old):
        #print("zoom changed")
        self.Refresh()
    
    def p1_changed(self, model, old):
        self.Refresh()
    
    def p2_changed(self, model, old):
        self.Refresh()

    def airfoil_changed(self, model, old):
        self.Refresh()

    def xshift_changed(self, model, old):
        self.Refresh()

    def yshift_changed(self, model, old):
        self.Refresh()

    def get_trafo(self):
        p1 = self.model.p1
        p2 = self.model.p2
        #alpha = math.atan2((p1[1]-p2[1]), p2[0]-p1[0])
        alpha = self.model.alpha
        shift = self.shift
        shift = self.model.xshift, self.model.yshift
        zoom = self.model.zoom
        # note the sign of shift[1]!
        print ("shift=", shift)
        return geometry.IDENTITY.Rotate(-alpha).Translate((-shift[0], -shift[1])) #.Rotate(-alpha).Scale(zoom, zoom)  Translate((-shift[0], -shift[1])).
    
        
    _radius = 14
    def on_paint(self, event):
        buffer = wx.EmptyBitmap(*self.Size)
        dc = wx.BufferedPaintDC(self, buffer)
        gc = wx.GraphicsContext.Create(dc)
        gc.PushState()

        #gc.SetPen(wx.WHITE_PEN)
        w, h = self.Size
        
        
        p1 = self.model.p1
        p2 = self.model.p2
        #alpha = math.atan2((p1[1]-p2[1]), p2[0]-p1[0])
        alpha = self.model.alpha
        # Alpha >0 bedeutet eine Drehung des Bildes im Uhrzeigersinn!
        gc.Rotate(-alpha)
        
        zoom = self.model.zoom
        #gc.Scale(zoom, zoom)

        shift = self._shift
        shift = self.model.xshift, self.model.yshift # XXX
        #gc.Translate(-shift[0], -shift[1])
        

        bmp = self.bmp
        if bmp:
            gc.DrawBitmap(bmp, -0, -0, bmp.Width, bmp.Height)

        r = self._radius/zoom
        d = 2*r
        w = 2.0/zoom    
        pen = wx.Pen(colour="red", width=w)
        gc.SetPen(pen)
        gc.DrawEllipse(p1[0]-r, p1[1]-r, d, d)
        gc.DrawEllipse(p2[0]-r, p2[1]-r, d, d)
        
        p = self._transient
        if p:
            pen = wx.Pen(colour="grey", width=2.0/zoom)
            gc.SetPen(pen)
            gc.DrawEllipse(p[0]-r, p[1]-r, d, d)

        trafo =  gc.GetTransform()
        if 0:
            print ("wx", trafo.Get())
            t2 = geometry.IDENTITY.Rotate(alpha).Scale(zoom, zoom).Translate((-shift[0], -shift[1]))
            print ("ce", t2.Get())
            import sys
            sys.trafo = t2
            sys.trafo_wx = trafo

            
        p1_ = trafo.TransformPoint(*p1)
        p2_ = trafo.TransformPoint(*p2)
        gc.PopState()

        t2 = self.get_trafo()
        pen = wx.Pen(colour="yellow", width=1)
        p1_ = t2.TransformPoint(p1)
        p2_ = t2.TransformPoint(p2)
        gc.DrawEllipse(p1_[0]-2, p1_[1]-2, 4, 4)
        gc.DrawEllipse(p2_[0]-2, p2_[1]-2, 4, 4)
        
        
        airfoil = self.model.airfoil
        if airfoil is None:
            return
        
        pen = wx.Pen(colour="green", width=2.0/zoom)
        gc.SetPen(pen)

        f = dist(p1_, p2_)
        alpha = math.atan2((p1_[1]-p2_[1]), p2_[0]-p1_[0])
        t2 = geometry.Scale(f, -f).Rotate(alpha).Translate(p1_)
        #print("scale factor:", f
        
        xv, yv = airfoil
        path = gc.CreatePath()
        first = True
        print(t2.TransformPoint((0, 0)), t2.TransformPoint((1, 0)))

        for p in zip(xv, yv):
            p_ = t2.TransformPointFloat(p)
            if first:
                first = False
                path.MoveToPoint(*p_)
            else:
                path.AddLineToPoint(*p_)
        gc.StrokePath(path)
        
    def load_image(self, imagefile):
        bmp = wx.EmptyBitmap(1, 1)
        bmp.LoadFile(imagefile, wx.BITMAP_TYPE_ANY) 
        self.bmp = bmp
        
    def set_zoom(self, zoom):
        if zoom != self._zoom:
            self._zoom = zoom
            self.Refresh()

    def set_shift(self, shift):
        if shift != self._shift:
            self._shift = shift
            self.Refresh()
            
    def set_transient(self, p):
        if p != self._transient:
            print("setting transient")
            old = self._transient
            self._transient = p
            d = 2*self._radius
            if old is not None:
                x, y = old
                self.RefreshRect((x-d, y-d, x+d, y+d))
            if p is not None:
                x, y = p
                self.RefreshRect((x-d, y-d, x+d, y+d))
                
            
    _dragstart = None # in screen coordinates
    def mouse_event(self, event):
        trafo = self.get_trafo()        
        p1 = wx.Point(*self.model.p1)
        p2 = wx.Point(*self.model.p2)
        p1_ = trafo(p1)
        p2_ = trafo(p2)

        inv = trafo.Inverse()
        p_ = event.Position
        p = inv.TransformPoint(p_)
        print("p2_=", p2_, "; p=", p)

        radius = self._radius

        if event.Moving():
            if dist(p1_, p_)<=radius:
                self._current = 1
                self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
            elif dist(p2_, p_)<=radius:
                self._current = 2
                self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
            else:
                self._current = None
                self.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
                
        if event.Dragging() and self._current:
            if self._dragstart is None:                
                self._dragstart = p_
            else:
                pass # ??? self.Refresh()
            points = None, p1_, p2_

            # transient ist in Bildkoordinaten, Position und Dragstart
            # dagegen in Window-Koordinaten
            delta = event.Position-self._dragstart
            self.transient = inv(points[self._current]+delta)
            #self.Refresh()
            
        elif event.ButtonUp():        
            #print "release"
            
            if self._transient is not None:
                if self._current == 1:
                    self.model.p1 = tuple(self._transient)
                elif self._current == 2:
                    self.model.p2 = tuple(self._transient)
            
            self._transient = None
            self._dragstart = None
            self._current = None
            

def load_airfoil(p):
    #import numpy
    #fn = "NHX021E DAT/NHX021E - 001.dat"
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
        xs, ys = l.split()
        xl.append(float(xs))
        yl.append(float(ys))
    return xl, yl


def demo_00():
    from .document import AnalysisModel
    doc = AnalysisModel()
    app = wx.App()
    f = wx.Frame(None)
    canvas = Canvas(f)
    canvas.set_model(doc)
    s = open("test/ah79k135.gif", "rb").read()
    doc.bmp = s
    f.Show()


    #canvas.transient = (50, 50)
    #canvas.zoom = 2
    canvas.p1 = 10, 100
    canvas.p2 = 500, 100
    doc.airfoil = load_airfoil("test/ag03.dat")
    #canvas.shift = 100, 0


def test_00():
    from .document import AnalysisModel
    doc = AnalysisModel()
    app = wx.App()
    f = wx.Frame(None)
    canvas = Canvas(f)
    canvas.set_model(doc)

    print(canvas.get_trafo())
    deg = 3.141592/180
    
    doc.alpha = 10*deg
    print(canvas.get_trafo())
    


