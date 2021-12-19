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
from .geometry import create_matrix
from .viewbase import ViewBase


def overridable_property(name, doc = None):
    setter_name = 'set_' + name
    return property(
        lambda self: getattr(self, '_'+name),
        lambda self, value: getattr(self, setter_name)(value),
        None,
        doc)



class Canvas(wx.Window, ViewBase):
    # Canvas uses 3 coordinate system:
    # - image coordinates
    # - screen coordinates
    # - profile coordinates
    #
    # All points are stored as image coordinates.
    
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

        self.Refresh()
        # update shift etc.
        if self.bmp is not None:
            return # XXX
            alpha = self.model.alpha
            zoom = self.model.zoom
            trafo =  create_matrix().Rotate(alpha).Scale(zoom, zoom)
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

    def get_image2window(self):
        w, h = self.Size
        #alpha = math.atan2((p1[1]-p2[1]), p2[0]-p1[0])
        alpha = self.model.alpha
        # Alpha >0 bedeutet eine Drehung des Bildes im Uhrzeigersinn!
        zoom = self.model.zoom
        xshift = self.model.xshift
        yshift = self.model.yshift

        m = create_matrix().Translated((xshift, yshift)).Translated((0.5*w, 0.5*h)).Rotated(alpha) \
            .Translated((-0.5*w, -0.5*h)).Scaled(zoom, zoom)
        return m

    _radius = 14
    def on_paint(self, event):
        buffer = wx.EmptyBitmap(*self.Size)
        dc = wx.BufferedPaintDC(self, buffer)
        gc = wx.GraphicsContext.Create(dc)
        
        m = self.get_image2window()
        gc.ConcatTransform(m)

        p1 = wx.Point2D(*self.model.p1)
        p2 = wx.Point2D(*self.model.p2)
        zoom = self.model.zoom

        bmp = self.bmp
        if bmp:
            gc.DrawBitmap(bmp, -0, -0, bmp.Width, bmp.Height)

        r = self._radius/zoom
        d = 2*r
        linewidth = 2.0/zoom    
        pen = wx.Pen(colour="red", width=linewidth)
        gc.SetPen(pen)
        gc.DrawEllipse(p1[0]-r, p1[1]-r, d, d)
        gc.DrawEllipse(p2[0]-r, p2[1]-r, d, d)
        
        p = self._transient
        if p:
            pen = wx.Pen(colour="grey", width=linewidth)
            gc.SetPen(pen)
            gc.DrawEllipse(p[0]-r, p[1]-r, d, d)

        m = self.get_image2window()
        airfoil = self.model.airfoil
        if airfoil is None:
            return
        
        pen = wx.Pen(colour="green", width=linewidth)
        gc.SetPen(pen)

        f = (p2-p1).Length()
        alpha = -math.atan2((p1[1]-p2[1]), p2[0]-p1[0])
        m = create_matrix().Translated(p1).Rotated(alpha).Scaled(f, -f) # die Reihenfolge finde ich komisch!
        # ... entspricht aber wx. finde ich auch komisch.
        self.profile2image = m
        
        # wx skaliert leider auch die Strichbreite. Wir pushen profile2image daher nicht, 
        # sondern benutzen es um die Koordinaten manuell umzurechnen. 
        xv, yv = airfoil
        path = gc.CreatePath()
        first = True
        for p in zip(xv, yv):
            p_ = self.profile2image(wx.Point2D(*p))

            if first:
                first = False
                path.MoveToPoint(*p_)
            else:
                path.AddLineToPoint(*p_)
        gc.StrokePath(path)        
        gc.SetBrush(wx.TRANSPARENT_BRUSH)
        gc.DrawRectangle(0, 0, 1, 1)
        
    def set_transient(self, p):
        if p != self._transient:
            old = self._transient
            self._transient = p
            d = 2*self._radius
            image2window = self.get_image2window()
            if old is not None:
                x, y = image2window.TransformPoint(*old)
                self.RefreshRect((x-d, y-d, x+d, y+d))
            if p is not None:
                x, y = image2window.TransformPoint(*p)
                self.RefreshRect((x-d, y-d, x+d, y+d))
                            
    _dragstart = None # in image coordinates
    def mouse_event(self, event):
        image2window = self.get_image2window()
        p1 = wx.Point2D(*self.model.p1)
        p2 = wx.Point2D(*self.model.p2)
        p1_ = image2window(p1)
        p2_ = image2window(p2)

        inv = image2window.Inverted()
        p_ = wx.Point2D(*event.Position)
        p = inv(p_)
        #print("p2_=", p2_, "; p=", p)

        radius = self._radius

        if event.Moving():
            if (p1_-p_).Length()<=radius:
                self._current = 1
                self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
            elif (p2_-p_).Length()<=radius:
                self._current = 2
                self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
            else:
                self._current = None
                self.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        if event.Dragging() and self._current:
            if self._dragstart is None:                
                self._dragstart = p
            points = None, p1, p2

            # transient ist in Bildkoordinaten, Position und Dragstart
            # dagegen in Window-Koordinaten
            delta = p-self._dragstart
            self.transient = points[self._current]+delta
            
        elif event.ButtonUp():
            transient = self._transient
            if transient is not None:
                if self._current == 1:
                    self.model.p1 = tuple(transient)
                elif self._current == 2:
                    self.model.p2 = tuple(transient)
            
            self.transient = None
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
    app = wx.App(False)
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

    app.MainLoop()
    print ("demo_00 ok")
    return
    
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
    


