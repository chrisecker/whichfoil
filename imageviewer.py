# -*- coding: latin-1 -*-

"""
Idee: Widgte um Bilder von Prfilen anzuzeigen
- Zoomen
- Markieren von Start- und Endpunt [(0,0) bzw. (1, 0)
- Rotieren des Profile
- Skalieren des Koordinatensystems

"""


import sys
import wx
import random
from random import randrange
from math import sin, cos, pi, sqrt

        


class Canvas(wx.Window):
    zoom = 1.0
    def __init__(self, image, *args, **kwds):
        self.bmp = wx.EmptyBitmap(1, 1)
        self.bmp.LoadFile(image, wx.BITMAP_TYPE_ANY ) 
        wx.Window.__init__(self, *args, **kwds)
        
        self.SetBackgroundColour('white')
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda e: None)
        self.SetFocus()

    def on_paint(self, event):
        buffer = wx.EmptyBitmap(*self.Size)
        dc = wx.BufferedPaintDC(self, buffer)
        gc = wx.GraphicsContext.Create(dc)
        #gc.SetPen(wx.WHITE_PEN)
        #gc.PushState()
        w, h = self.Size
        #gc.Translate(w/2, h/2)
        #gc.Rotate((180+plane.direction)*pi/180.0)
        #gc.Translate(-x, -y)
        gc.Scale(self.zoom, self.zoom)
        bmp = self.bmp
        gc.SetPen(wx.RED_PEN)
        gc.SetBrush(wx.YELLOW_BRUSH)

        gc.DrawRectangle(-100, -100, 1000, 1000)
        gc.DrawBitmap(bmp, -0, -0, bmp.Width, bmp.Height)
        #gc.PopState()
        return

        gc.SetBrush(wx.TRANSPARENT_BRUSH)
        for shape in self.shapes:
            path = gc.CreatePath()
            for item in shape:
                cmd = item[0]
                points = item[1:] 
                if cmd == 'M':
                    x, y = points[0]
                    path.MoveToPoint(x, y)
                elif cmd == 'L':
                    x, y = points[0]
                    path.AddLineToPoint(x, y)
                elif cmd == 'Q':
                    (cx, cy), (x, y) = points
                    path.AddQuadCurveToPoint(cx, cy, x, y)
                elif cmd == 'Z' or cmd == 'z':
                    path.CloseSubpath()
                else: 
                    raise ValueError(cmd) # unknown command
            gc.DrawPath(path)

        # Steigen einzeichnen
        if self.show_climb:
            gc.SetBrush(wx.BLACK_BRUSH)
            az = None
            for x, y, z, d in self.track[-100:]:
                if az is not None:
                    r = (z-az)*10
                    if r>1:
                        gc.DrawEllipse(x-r, y-r, 2*r, 2*r)
                az = z

        l = 5
        for x, y in self.markers:
            #gc.DrawText('X', x, y)
            gc.DrawLines([(x-l, y-l), (x+l, y+l)])
            gc.DrawLines([(x-l, y+l), (x+l, y-l)])

        # Flugzeugindikator einzeichnen
        gc.PopState()
        font = wx.Font(10, wx.NORMAL, wx.ITALIC, wx.NORMAL)
        gc.SetFont(font)
        brush = gc.CreateBrush(wx.WHITE_BRUSH)
        gc.DrawText(u'Steigen: %-.1f m/s'%plane.climb, 10, 20, brush)
        gc.DrawText(u'Höhe: %i m'%plane.height, 10, 35, brush)
        gc.DrawText(u'Richtung: %i°'% (360-plane.direction), 10, 50, brush)
        gc.SetBrush(wx.TRANSPARENT_BRUSH)
        gc.DrawRectangle(w/2-5, h/2-5, 10, 10)


class Main(wx.Frame):
    def __init__(self, image):
        wx.Frame.__init__(self, None)
        self.SetDoubleBuffered(True) # wichtig für Windows
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.canvas = Canvas(image, self)
        sizer.Add(self.canvas, 1, wx.EXPAND)        
        buttonbox = wx.Panel(self)
        sizer.Add(buttonbox, 0, wx.EXPAND)
        self.Sizer = sizer

        sizer = wx.BoxSizer(wx.VERTICAL)
        bhelp = wx.Button(buttonbox, label='Hilfe')
        bpause = wx.Button(buttonbox, label='Pause')
        bnewgame = wx.Button(buttonbox, label='Neu')
        sizer.Add(bhelp, 0)
        sizer.Add(bpause, 0)
        sizer.Add(bnewgame, 0)
        buttonbox.Sizer = sizer
        self.Bind(wx.EVT_CHAR, self.on_char)
        self.canvas.Bind(wx.EVT_CHAR, self.on_char)
        return
    
        

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_tick, self.timer)
        self.mmap.SetFocus()

    def on_char(self, event):
        print "on char"
        keycode = event.GetKeyCode()
        ctrl = event.ControlDown()
        shift = event.ShiftDown()
        alt = event.AltDown()        
        
        char = event.GetUnicodeKey()        
        #print repr(char), keycode, ctrl, alt

        canvas = self.canvas

        print keycode
        if keycode == 43: # plus
            canvas.zoom += 0.1
        elif keycode == 45: # minus
            canvas.zoom -= 0.1
        else:
            event.Skip()
        canvas.Refresh()




app = wx.App(False)
import sys
image = sys.argv[1]
print image
f = Main(image)
f.Show()  

app.MainLoop()
