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



if wx.VERSION[0] <= 3:
    create_bitmap = wx.EmptyBitmap
    def image2bitmap(image):
        return image.ConvertToBitmap()
        
else:
    create_bitmap = wx.Bitmap
    image2bitmap = wx.Bitmap
    

                    
def overridable_property(name, doc = None):
    setter_name = 'set_' + name
    return property(
        lambda self: getattr(self, '_'+name),
        lambda self, value: getattr(self, setter_name)(value),
        None,
        doc)



class Canvas(wx.ScrolledWindow, ViewBase):
    # Canvas uses 3 coordinate system:
    # - image coordinates
    # - screen coordinates
    # - profile coordinates
    #
    # All points are stored as image coordinates.
    
    transient = overridable_property('transient', \
        'position of transient item in image coordinates or None')
    _transient = None
    bmp = None
    _current = None
    def update_scroll(self):
        if self.model is None:
            return
        m = self.get_image2window()
        bmp = self.bmp
        if bmp is None:
            w = h = 100
        else:
            w, h = bmp.Size
        xl = []
        yl = []
        for p in [(0, 0), (0, h), (w, h), (w, 0)]:
            x, y = m.TransformPoint(*p)
            xl.append(x)
            yl.append(y)
        vw = max(xl)-min(xl)
        vh = max(yl)-min(yl)
        virtual = wx.Point2D(vw, vh)
        self.SetVirtualSize((vw, vh))
        win = wx.Point2D(*self.Size)
        c_win = 0.5*win # window center 
        shift = m(0.5*wx.Point2D(w, h))-c_win
        scroll = 0.5*(virtual-win)-shift
        self.SetScrollPos(wx.HORIZONTAL, scroll[0])
        self.SetScrollPos(wx.VERTICAL, scroll[1])
        # calculate scrollbar positions
        #shifty = scroll-0.5*(virtual[1]-window[1])
        # set scrollbar positions
    
    def __init__(self, parent):
        ViewBase.__init__(self)
        wx.ScrolledWindow.__init__(self, parent)
        # not implemented. idiots. self.AlwaysShowScrollbars(True, True)
        self.SetBackgroundColour('white')
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda e: None)
        
        self.Bind(wx.EVT_MOUSE_EVENTS, self.mouse_event)
        #self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.capturelost_event)
        self.Bind(wx.EVT_SCROLL, self.on_scroll)
        self.Bind(wx.EVT_SCROLLBAR, self.on_scroll)
        self.Bind(wx.EVT_SCROLLWIN, self.on_scroll)
        
        self.SetFocus()
        self.SetScrollRate(1, 1)
        self.ShowScrollbars(True, True)
        wx.CallAfter(self.update_scroll)

    def model_added(self, model):
        self.bmp_changed(model, None)

    def update_bmp(self):
        model = self.model
        bmp = model.bmp
        hue = model.hue
        if bmp is None:
            self.bmp = None
        else:            
            f = StringIO(bmp)
            im = wx.ImageFromStream(f)
            if model.mirror:
                im = im.Mirror()

            if hue != 0.5:
                assert hue>=0
                assert hue<=1
                w, h = im.GetSize()
                bmp2 = create_bitmap(w, h)
                dc = wx.MemoryDC()
                dc.SelectObject(bmp2)
                
                dc.DrawBitmap(image2bitmap(im), 0, 0)
                if model.hue>0.5:
                    alpha = 500*hue-255
                    color = wx.Colour(255, 255, 255, alpha) # white
                else:
                    alpha = 255-500*hue
                    color = wx.Colour(0, 0, 0, alpha) # black
                brush = wx.Brush(color)
                dc.SetBrush(brush)
                dc.SetPen(wx.TRANSPARENT_PEN)
                dc.DrawRectangle(0, 0, w, h)
                dc.SelectObject(wx.NullBitmap)
                self.bmp = bmp2
            else:
                #print ("update bmp. brightness=", brightness, "transparancy=", transparency)
                #im = im.AdjustChannels(brightness, 1, 1, transparency)
                self.bmp = image2bitmap(im)
                
        self.update_scroll()
        self.Refresh()
        
    def bmp_changed(self, model, old):
        self.update_bmp()

    def hue_changed(self, model, old):
        self.update_bmp()

    def transparency_changed(self, model, old):
        self.update_bmp()
        
    def mirror_changed(self, model, old):
        self.bmp_changed(model, None)

    def alpha_changed(self, model, old):
        self.update_scroll()
        self.Refresh()

    def zoom_changed(self, model, old):
        self.update_scroll()
        self.Refresh()

    def focus_changed(self, model, old):
        self.update_scroll()
        self.Refresh()
            
    def p1_changed(self, model, old):
        self.Refresh()
    
    def p2_changed(self, model, old):
        self.Refresh()

    def yfactor_changed(self, model, old):
        self.Refresh()
        
    def airfoil_changed(self, model, old):
        self.Refresh()

    def xshift_changed(self, model, old):
        self.Refresh()

    def yshift_changed(self, model, old):
        self.Refresh()

    def get_shift(self):
        virtual = wx.Point2D(*self.VirtualSize)
        window = wx.Point2D(*self.Size)
        scrollx = self.GetScrollPos(wx.HORIZONTAL)
        scrolly = self.GetScrollPos(wx.VERTICAL)
        scroll = wx.Point2D(scrollx, scrolly)
        return 0.5*(virtual-window)-scroll

    def get_image2window(self):
        bmp = self.bmp
        if bmp is None:
            w = h = 100
        else:
            w, h = bmp.Size
        #alpha = math.atan2((p1[1]-p2[1]), p2[0]-p1[0])
        alpha = self.model.alpha*pi/180.0
        # Alpha >0 bedeutet eine Drehung des Bildes im Uhrzeigersinn!
        zoom = self.model.zoom

        scrollx = self.GetScrollPos(wx.HORIZONTAL)
        scrolly = self.GetScrollPos(wx.VERTICAL)
        scroll = wx.Point2D(scrollx, scrolly)

        m = create_matrix().Rotated(alpha) \
            .Translated((-0.5*w, -0.5*h)).Scaled(zoom, zoom)

        # achtung: die Anwendung der Matritzen erfolgt von rechts nach
        # links. Ein Punkt p wird als 1. Skaliert, 2. verscoben,
        # 3. Rotiert, ...

        focus_ = m(wx.Point2D(*self.model.focus))

        # jetzt so verschieben, dass focus_ im Mittelpunkt des Fensters (wc) liegt
        wc = 0.5*wx.Point2D(*self.Size)
        r = create_matrix().Translated(wc-focus_)(m)
        return r

    def get_image2virtual(self):
        bmp = self.bmp
        if bmp is None:
            w = h = 100
        else:
            w, h = bmp.Size
        alpha = self.model.alpha
        zoom = self.model.zoom

        m = create_matrix().Rotated(alpha) \
            .Translated((-0.5*w, -0.5*h)).Scaled(zoom, zoom)

        ic = wx.Point2D(0.5*w, 0.5*h) # image center
        ic_ = m(wx.Point2D(*ic))

        # jetzt so verschieben, dass center_ im Mittelpunkt (vc_) der virtuellen Fläche liegt. 
        vc_ = 0.5*wx.Point2D(*self.VirtualSize)
        r = create_matrix().Translated(vc_-ic_)(m)
        return r

    def get_profile2image(self):
        model = self.model
        p1 = wx.Point2D(*model.p1)
        p2 = wx.Point2D(*model.p2)
        f = (p2-p1).Length()
        alpha = -math.atan2((p1[1]-p2[1]), p2[0]-p1[0])
        m = create_matrix().Translated(p1).Rotated(alpha).Scaled(f, -f)
        return m
    
    def on_scroll(self, event):
        m = self.get_image2virtual()
        inv = m.Inverted()
        virtual = wx.Point2D(*self.VirtualSize)
        focus = self.model.focus
        focus_ = m(wx.Point2D(*focus))
        x, y = focus_-0.5*virtual
        xinc, yinc = self.GetScrollPixelsPerUnit()
        window = self.Size
        if event.GetOrientation() == wx.VERTICAL:
            s = yinc*event.GetPosition()
            y = s-0.5*(virtual[1]-window[1])
        else:
            s = xinc*event.GetPosition()
            x = s-0.5*(virtual[0]-window[0])
        shift = wx.Point2D(x, y)
        focus_ = 0.5*wx.Point2D(*virtual)+shift
        self.model.focus = tuple(inv(focus_))
        event.Skip()

    def _draw_edge_handle(self, gc, p):
        r = 14
        d = 2*r
        gc.DrawEllipse(p[0]-r, p[1]-r, d, d)
        e = 5
        gc.DrawLines([p-(e, 0), p+(e, 0)])
        gc.DrawLines([p-(0, e), p+(0, e)])
            
    def _draw_sub_handle(self, gc, p):
        e = 5
        gc.DrawLines([p+(-e, -e), p+(+e, +e)])
        gc.DrawLines([p+(-e, +e), p+(+e, -e)])
        
            
    _radius = 18
    def on_paint(self, event):
        buffer = wx.EmptyBitmap(*self.Size)
        dc = wx.BufferedPaintDC(self, buffer)
        gc = wx.GraphicsContext.Create(dc)
        
        image2window = self.get_image2window()

        model = self.model
        p1 = wx.Point2D(*model.p1)
        p2 = wx.Point2D(*model.p2)
        zoom = model.zoom
        yfactor = model.yfactor

        bmp = self.bmp
        if bmp:
            gc.PushState()
            gc.ConcatTransform(image2window)
            gc.DrawBitmap(bmp, -0, -0, bmp.Width, bmp.Height)
            gc.PopState()

        linewidth = 2.0
        pen = wx.Pen(colour="red", width=linewidth)        
        gc.SetPen(pen)
        color = wx.Colour(255, 0, 0, 50) # semi transparent red
        brush = wx.Brush(color)
        gc.SetBrush(brush)

        t = image2window
        for p in p1, p2:
            self._draw_edge_handle(gc, t(p))

        if self._transient:
            p_ = t(self._transient)
            pen = wx.Pen(colour="grey", width=linewidth)
            color = wx.Colour(128, 128, 128, 50)
            brush = wx.Brush(color)
            gc.SetBrush(brush)
            
            gc.SetPen(pen)
            if self._current in (6, 7):
                self._draw_edge_handle(gc, p_)
            else:
                self._draw_sub_handle(gc, p_)                
            
        profile2win = image2window(self.get_profile2image())

        if model.airfoil is not None:
            name, (xv, yv) = model.airfoil            
            path = gc.CreatePath()
            first = True
            for x, y in zip(xv, yv):
                p_ = profile2win(wx.Point2D(x, y*yfactor))
                if first:
                    first = False
                    path.MoveToPoint(*p_)
                else:
                    path.AddLineToPoint(*p_)
            pen = wx.Pen(colour="green", width=2)
            gc.SetPen(pen)
            gc.StrokePath(path)        

        pen = wx.Pen(colour="red", width=linewidth)        
        gc.SetPen(pen)        
        for x, y in zip(self.xpositions, model.sliders):
            p = wx.Point2D(x, y)
            self._draw_sub_handle(gc, profile2win(p))                
                
    # x-part of position of sliders. Fixed.    
    xpositions = (0.25, 0.25, 0.5, 0.5, 0.75, 0.75)
    
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
        profile2image = self.get_profile2image()
        profile2window = image2window(profile2image)

        model = self.model
        p1 = wx.Point2D(*model.p1)
        p2 = wx.Point2D(*model.p2)
        p12 = p2-p1
        
        p1_ = image2window(p1)
        p2_ = image2window(p2)

        hvec__ = [wx.Point2D(*p) for p in zip(self.xpositions, model.sliders)]
        hvec_ = [profile2window(p) for p in hvec__]
        hvec = [profile2image(p) for p in hvec__]
        
        inv = image2window.Inverted()
        p_ = wx.Point2D(*event.Position)
        p = inv(p_)

        radius = self._radius
        if event.Moving():
            flag = False
            for i, x_ in enumerate(hvec_+[p1_, p2_]):
                if (x_-p_).Length()<=radius:
                    self._current = i
                    self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
                    flag = True
            if not flag:
                self._current = None
                self.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))

        if event.LeftDown() and self._current is not None:
            self._dragstart = p
            points = hvec+[p1, p2]
            self.transient = points[self._current]
            
        elif event.Dragging() and self._current is not None:
            points = hvec+[p1, p2]
            delta = p-self._dragstart
            t = points[self._current]+delta
            if self._current<6:
                m = profile2image.Inverted()
                t__ = m(t)
                t__[0] = self.xpositions[self._current]
                t = profile2image(t__)
            self.transient = t
            
        elif event.LeftUp():
            transient = self._transient
            if transient is not None:
                i = self._current
                if i in range(6):
                    m = profile2image.Inverted()
                    sliders = list(model.sliders)
                    sliders[i] = m(transient)[1]
                    model.sliders = tuple(sliders)
                elif i == 6:
                    model.p1 = tuple(transient)
                elif i == 7:
                    model.p2 = tuple(transient)
                self.Refresh() # to remove the original 
            
            self.transient = None
            self._dragstart = None
            self._current = None

        elif event.WheelRotation > 0:
            model.zoom *= 1.5
            model.focus = p

        elif event.WheelRotation < 0:
            model.zoom /= 1.5
            model.focus = p

        else:
            event.Skip()
            

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


def demo_00():
    from .document import AnalysisModel
    from .airfoil import load_airfoil
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
    


