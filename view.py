

import sys
import wx
import math
from math import sin, cos, pi, sqrt

def overridable_property(name, doc = None):
    setter_name = intern('set_' + name)
    return property(
        lambda self: getattr(self, '_'+name),
        lambda self, value: getattr(self, setter_name)(value),
        None,
        doc)


def dist(p1, p2):
    return sqrt((p1[0]-p2[0])**2+(p1[1]-p2[1])**2)
    
    
class Canvas(wx.Window):
    zoom = overridable_property('zoom')
    shift = overridable_property('shift')
    p1 = overridable_property('p1')
    p2 = overridable_property('p2')
    transient = overridable_property('transient')
    _zoom = 1.0
    _shift = 0.0, 0.0
    _p1 = (0, 50)
    _p2 = (100, 50)
    _transient = None
    bmp = None
    def __init__(self, *args, **kwds):
        wx.Window.__init__(self, *args, **kwds)
        
        self.SetBackgroundColour('white')
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda e: None)
        
        self.Bind(wx.EVT_MOUSE_EVENTS, self.mouse_event)
        #self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.capturelost_event)
        
        self.SetFocus()

    def on_paint(self, event):
        buffer = wx.EmptyBitmap(*self.Size)
        dc = wx.BufferedPaintDC(self, buffer)
        gc = wx.GraphicsContext.Create(dc)
        #gc.SetPen(wx.WHITE_PEN)
        #gc.PushState()
        w, h = self.Size
        
        shift = self._shift
        gc.Translate(-shift[0], -shift[1])
        
        p1 = self._p1
        p2 = self._p2
        alpha = math.atan2((p1[1]-p2[1]), p2[0]-p1[0])
        # Alpha >0 bedeutet eine Drehung des Bildes im Uhrzeigersinn
        gc.Rotate(alpha)
        
        zoom = self._zoom
        gc.Scale(zoom, zoom)
        
        self._trafo =  gc.GetTransform()
        #print self._trafo.Get()
        #print self.get_trafo()
        gc.SetPen(wx.RED_PEN)
        #gc.SetBrush(wx.YELLOW_BRUSH)

        bmp = self.bmp
        if bmp:
            gc.DrawBitmap(bmp, -0, -0, bmp.Width, bmp.Height)
            
        s = 10.0/zoom
        pen = wx.Pen(colour="red", width=2.0/zoom)
        gc.SetPen(pen)
        gc.DrawEllipse(p1[0], p1[1], s, s)
        gc.DrawEllipse(p2[0], p2[1], s, s)
        
        p = self._transient
        if p:
            pen = wx.Pen(colour="grey", width=2.0/zoom)
            gc.SetPen(pen)
            gc.DrawEllipse(p[0], p[1], s, s)
            
        #gc.PopState()
        
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
            
    def set_p1(self, p1):
        if p1 != self._p1:
            self._p1 = p1
            self.Refresh()

    def set_p2(self, p2):
        if p2 != self._p2:
            self._p2 = p2
            self.Refresh()

    def set_transient(self, p):
        if p != self._transient:
            self._transient = p
            self.Refresh()

    def get_trafo(self):
        p1 = self._p1
        p2 = self._p2
        alpha = math.atan2((p1[1]-p2[1]), p2[0]-p1[0])
        from geometry import Translation, Rotation, Stretch
        trafo = Translation(-wx.Point(*self._shift))
        trafo = trafo(Rotation(-alpha))
        # Achtung: der Ursprung des Koordinatensystems von wx liegt in
        # der linken oberen Ecke, y wächst nach unten. Dies entspricht
        # einem linkhändigen KS. Geometry geht dagegen von einem
        # rechtshändigen KS aus. Wir müssen daher alle Drehwinkel mit
        # -1 multiplizieren. 
        trafo = trafo(Stretch(self._zoom))
        #print "alpha=", alpha
        return trafo
            
    _dragstart = None # in screen coordinates
    def mouse_event(self, event):
        trafo = self.get_trafo()        
        p1 = wx.Point(*self._p1)
        p2 = wx.Point(*self._p2)
        p1_ = trafo(p1)
        p2_ = trafo(p2)
        
        inv = trafo.Inverse()
        #print "trafo=", trafo
        #print "inv=", inv

        #print "p screen=", event.Position
        #print "p bitmap=", trafo(event.Position)
        #print "p test=", inv(event.Position)

        if event.Moving():
            p = event.Position
            if dist(p1_, event.Position)<10:
                self._current = 1
                self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
            elif dist(p2_, event.Position)<10:
                self._current = 2
                self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
            else:
                self._current = None
                self.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
        if event.Dragging() and self._current:
            #print "current=", self._current
            inv = trafo.Inverse()
            p = inv.TransformPoint(event.Position)
            if self._dragstart is None:                
                self._dragstart = event.Position
            else:
                self.Refresh()
            points = None, p1_, p2_
            self._transient = inv(points[self._current]+event.Position-self._dragstart)
            self.Refresh()
        elif event.ButtonUp():        
            #print "release"
            
            if self._transient is not None:
                if self._current == 1:
                    self.p1 = self._transient
                elif self._current == 2:
                    self.p2 = self._transient
            
            self._transient = None
            self._dragstart = None
            self._current = None
            

if __name__ == '__main__':
    app = wx.App()
    f = wx.Frame(None)
    canvas = Canvas(f)
    canvas.load_image("ah79k135.gif")
    f.Show()


    canvas.transient = (50, 50)
    #canvas.zoom = 2
    canvas.p1 = 30, 40
    #canvas.shift = 100, 0
    
    import testing
    testing.pyshell(locals())
    app.MainLoop()


