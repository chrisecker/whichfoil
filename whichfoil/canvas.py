# -*- coding:latin-1 -*-

# 05.12.21 -- Doppelpufferung repariert
#
# 19.07.19 -- Aufgeräumteres Konzept
#
# Wir haben unterschiedliche Arten von Canvas-Objekten, z.B.
# Zeichenelemente und Hilfslinien.
#
# Das interaktive Verhalten dieser Objekte wird durch Controller
# festgelegt. Dabei verhalten sich ähnliche Objekte auch ähnlich. Wir
# haben je einen Display-Controller und einen Drag-Controller für
# Zeichenlemente und Hilfslinien.
#
# Alle Objektspezifischen Details sollte durch Methoden in dem Objekt
# gegeben sein. Es wäre unübersichtlich, wenn sich Objekteigenschaften
# über mehrere Klassen (Objekt und diverse Kontroller verteilen).
#
# Zu klären:
#
# - wenn ein Controller ein bestimmtes Signal nicht behandelt, wird
#   dann dernächste Controller aufgerufen? -- Wäre nicht erwünscht, zB
#   manche Tastatur-Eingaben müssen gesperrt sein.
#
# - In anderen Fällen wäre genau das nötig. ZB Paint-Events brauchen
#   nicht modifiziert zu werden.
#
# ERGEBNIS:
#
# - der tiefere Event-Handler wird aufgerufen, wenn der Event in dem
#   Controller behandelt wird!
# - Event-Behandlungen müssen also geziel gesperrt werden!

# 19.07.19 Konzept zu Controllern
#
# Creator: wird durch das Menu installiert
#
# Editor: jedes Canvas-Objekt kann einen Editor haben. Der Editor wird
# installiert (zB durch das Selektieren des Objektes). Bei einem Drag
# kann der Editor wiederum einen DragController installieren. Denkbar
# wäre auch, dass er dazu wieder auf das Objekt zugreift (zB Methode
# get_drag_controller ...)
#
# Drag Controller: wird beendet durch Loslassen der Maustaste oder
# durch ESC. Verschiebt das Objekt im Canvas. Für andere Objekte
# könnte stattdessen auch DND zu anderem Fenster durchgeführt werden.
# 


# TODO:
#
# Der Wechsel der Controller sollte über das Drawable
# erfolgen. Drawables sollten jeweils *ihre* Controller besitzen.
#
# class Box:
#   drag_controller
#   create_controller
#   ...
#
# Drawable-Methoden sollten sich auf Eigenschaften des Drawable
# beziehen, z.B.
# - set_current
# - move
#
# Controller-Methoden sollten sich dagegen auf die EIngabe beziehen,
# z.B. mouse_event, drag_start, ...



#
# Drucken über PrintCanvas. Dazu sollte der Canvas eine Methode
# get_printcanvas() haben. Von allen Zeichenobjekten werden dazu 
# Kopien angefertigt.
#

import wx
import geometry # this will install a couple of methods to wx
from properties import Properties, overridable_property
from model import Model



class Drawable(Properties):
    is_selectable = False
    is_draggable = False

    bounds = overridable_property('bounds', 
        "The position and size of the drawing object. Read only.")
    position = overridable_property('position', 
        "The position part of bounds. Read/Write.")
    size = overridable_property('size', 
        "The size part of bounds. Read/Write.")
    border = overridable_property('border', 
        "Read/Write.")
    visible = overridable_property('visible', 
        "If visible is false, the object is not drawn. Read/Write.")
    selected = overridable_property('selected', 
        "If true, the object is drawn as selected. Read/Write.")
        
    _position = wx.Point(0, 0)
    _size = wx.Point(0, 0)
    _border = 1
    _selected = False
    _dragstart = None
            
    def __init__(self, canvas, *args, **kwds):
        self._canvas = canvas
        Properties.__init__(self, **kwds)  
        
    def destroy(self):
        #print "destroy: ", repr(self)
        self._canvas = None                

    def on_idle(self):
        # Wird von Canvas aufgerufen
        pass

    def refresh(self):
        border = self._border
        self._canvas.refresh(self.bounds.Grown(border, border))
        
    def get_bounds(self):
        x, y = self._position
        w, h = self._size
        return wx.Rect(x, y, w, h)
        
    def get_position(self):
        return self._position
        
    def set_position(self, position):
        if self._position == position:
            return
        old = self._position
        new = wx.Point(*position)
        self.refresh()        
        self._position = new
        self.refresh()        
        
    def get_border(self):
        return self._border

    def set_border(self, border):
        self._border = border
        
    def get_size(self):
        return self._size
        
    def set_size(self, size):
        w, h = size
        self._size = wx.Point(w, h)
        
    def set_selected(self, selected):
        if selected != self._selected:
            self._selected = selected
            self.refresh()
            
    def get_selected(self):
        return self._selected
        
    def drawable2canvas(self, pos):
        "Konvertiert aus dem Objekt KS zu dem Canvas KS"
        return self.position+pos

    def draw_bbox(self, dc, fill=True):
        "Zeichnet die Bounding Box. Nur zum Testen"
        if fill:
            pass
        else:
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRectangleRect(self.bounds.Moved(-self.position))    
                
    """
      You must implement the following functions
    """
    def draw(self, dc):
        """
          You must implement this routine to do draw
        """
        assert (False)

    def draw_mask(self, dc):
        """
          optionally implement this routine to draw a mask
        """
        pass
        
    def hit_test(self, pos):
        """
          You must implement this routine to do hit testing for dragable region
        of drawable object
        """
        return True

    def get_dragcontroller(self, pos):
        # Erzeugt einen Dragcontroller. Pos ist die Position relativ
        # zu self.position, an der der Drag begonnen wurde.
        return MovingDragController(self._canvas, pos)
    
    def mouse_event(self, event):
        """
          Mouse events werden empfangen, wenn das Drawable "current"
          ist. Es ist wichtig, mit dem Rückgabewert anzugeben, ob die
          Eventbahndlung abgelschlossen ist, oder nicht. Andernfalls
          können z.B. keine Kontext-Menü Events behandelt werden.
        """
        return False
        
    def mouse_entered(self, pos):
        pass
        
    def mouse_exited(self, pos):
        pass
       
        

class Controller(wx.EvtHandler):
    mode = "NORMAL"
    allows_drag = False
    allows_edit = False
    allows_select = False
    
        

class MovingDragController(Controller):
    mode = "MOVE"
    _drag_start = None
    def __init__(self, canvas, drag_start):
        self._canvas = canvas
        self._current = canvas.current
        self._old_pos = canvas.current.position
        self._drag_start = drag_start
        Controller.__init__(self)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.mouse_event)
        self.Bind(wx.EVT_KEY_DOWN, self.keydown_event)
        #self.Bind(wx.EVT_CONTEXT_MENU, self.contextmenu_event)
        canvas.cursor = wx.CURSOR_CROSS #BLANK

    def mouse_event(self, event):
        canvas = self._canvas
        if event.ButtonUp():
            canvas.controller = None
        if event.Dragging():
            self._current.position = event.Position-self._drag_start-canvas.scroll

    def keydown_event(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            self._current.position = self._old_pos
            self._canvas.controller = None
        else:
            # Call skip to allow other event handlers to process this
            # event
            event.Skip()

        
        

    
class CanvasBase(Model): 
    """
Der Canvas hat ein eigenes Koordinatenssystem, dass sich je nach Scroll-Zustand von 
dem des Fensters unterscheiden kann. Es wird als "Canvas"-KS bezeichnet.

canvas2window
window2canvas

    """
    window = overridable_property('window', 
        "The wx.Window. Readonly.")
    cursor = overridable_property('cursor', 
        "The stock cursor id of the windows cursor. Read/ Write.")
    controller = overridable_property('controller', 
        "Read/write.")
    scroll = overridable_property('scroll', 
        "Read/write.")
    origin = overridable_property('origin', 
        "Read.")
    current = overridable_property('current', 
        "The current drawable under the mouse pointer or None. Readonly")
    controller = overridable_property('controller', 
        "The current controller. Read / Write")
    mode = overridable_property('mode', 
        "The current mode. Readonly")
        
    _new_cursor = wx.CURSOR_DEFAULT 
    _cursor = None
    _controller = None
    # The cursor is not set directly, instead set_cursor sets the new_cursor-
    # flag. In the idle_event routine, _new_cursor is compared to _cursor, and
    # if necessary, the window cursor is set and _cursor is changed.
    
    _current = None
    _drawables_under_cursor = ()
    _scroll = (0, 0)
    
    def __init__(self, parent, *args, **kwds):
        self._window = wx.Window(parent, *args, **kwds)

        self._window.Bind(wx.EVT_ERASE_BACKGROUND, lambda x: None)
        self._window.Bind(wx.EVT_WINDOW_DESTROY, self.destroy_event)
        self._window.Bind(wx.EVT_MOUSE_EVENTS, self.mouse_event)
        self._window.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.capturelost_event)
        #self._window.Bind(wx.EVT_IDLE, self.idle_event)
        self._window.Bind(wx.EVT_PAINT, lambda e: self.repaint())

        if 0:
            # Create a frame which displays the update region. Good
            # for debugging the double buffering code.
            self.f = wx.Frame(None, title='update region')
            self.f.Bind(wx.EVT_PAINT, lambda e: self.repaint_test())
            self.f.Show()

        
    def destroy_event(self, event):
        self.destroy()
        # We want other event handlers to be called, so we have to
        # skip! ("However if the handler calls event.Skip() during its
        # execution, this event handler is skipped and the search
        # continues.")
        event.Skip()

    def destroy(self):
        # Die drawables müssen zerstört werden, damit sie die
        # Möglichkeit haben, ihre Nachrichtenkanäle abzubestellen.
        for item in self.iter_drawables():
            item.destroy()
        
        # https://wiki.wxpython.org/PushEventHandler: Since the
        # development cycle 2.9, you will also need to pop the event
        # handler with PopEventHandler.
        self._controller = None
                    
    def capturelost_event(self, event):
        print "Capture lost in canvas.py", event
        pass

    def mouse_event(self, event):
        # XXX hier sollte das Folgende passieren:
        # - bei mouse move current anpassen
        # - wenn curent angepasst wird cursor anpassen
        # - beim Klicken Element selektieren
        # - beim Dragggen: Dragcontroller einsetzen
        
        # XXX current sollte eigentlich immer das element unter dem
        # Cursor sein, selected/active sollte das gewählte Element
        # sein.
        if event.IsButton():
            # Mausklick links (einfach oder doppelt)
            self.window.SetFocus()
        pos = self.window2canvas(event.Position)
        if event.Moving():
            self.update_current(pos)
        current = self.current
        if current is None:
            return
        assert self.controller is None
        if event.Dragging():
            self.controller = current.get_dragcontroller(pos-current.position)

    def update_current(self, pos):
        # make sure, current holds the elemt under the cursor (or
        # None) and the cursor icon is updated.
        current = self.pick(pos)

        # Always set the cursor! This is expected from update_current.
        if current is None:
            self.cursor = wx.CURSOR_DEFAULT
        elif current.is_selectable or current.is_dragable:
            # XXX nur wenn entspr. Flag auf Objekt gesetzt ist, zB
            # moveable
            self.cursor = wx.CURSOR_HAND
        # set current only if needed
        if current is not self._current:
            self._current = current
        
    def iter_drawables(self):
        "Implement this"
        assert (False)
        
    def get_origin(self):
        return self._scroll
        
    def get_scroll(self):
        return self._scroll
        
    def set_scroll(self, scroll):
        if scroll == self._scroll:
            return
        dx = scroll[0] - self._scroll[0]  
        dy = scroll[1] - self._scroll[1]       
        self._scroll = scroll
        
        # 1. Kinder verschieben
        self.notify_views('scroll_changed')
        # 2. Das Fenster scrollen (dabei werden dreckige Bereiche neu gezeichnet)
        self._window.ScrollWindow(dx, dy)
                  
    def set_controller(self, controller):
        if controller is None:
            if self.controller is not None:
                self.window.PopEventHandler()
                pos = self.screen2canvas(wx.GetMousePosition())
                self.update_current(pos)
        else:
            if self.controller is not None:
                raise Exception("Controller already set.")
            self.window.PushEventHandler(controller)   
            controller.SetEvtHandlerEnabled(True)
        self._controller = controller

    def get_controller(self):
        return self._controller

    def get_mode(self):
        if self._controller is not None:
            return self._controller.mode
        return "NORMAL"
    
    def get_window(self):
        return self._window
        
    def get_current(self):
        return self._current
        
    def get_cursor(self):
        return self._cursor
        
    def set_cursor(self, cursor):
        if self._cursor == cursor:
            return
        self._window.SetCursor(wx.StockCursor(cursor))
        self._cursor = cursor
        
    def canvas2window(self, point):
        return wx.Point(*point) + self.origin
        
    def window2canvas(self, point):
        return wx.Point(*point) - self.origin

    def canvas2screen(self, point):
        return wx.Point(*point) + self.origin # XXX kann nicht richtig sein!
        
    def screen2canvas(self, *point):
        return self._window.ScreenToClient(*point) - self.origin
        
    def refresh(self, rect):
        "rect is in canvas coordinates"
        x_, y_, w, h = tuple(rect)
        x, y = self.canvas2window((x_, y_))
        self._window.RefreshRect(wx.Rect(x, y, w, h))

    buffer = None # store the buffer for debugging
    def repaint_test(self):
        # Show the buffer in the debug frame
        buffer = self.buffer
        if buffer is None:
            return
        w, h = buffer.Size
        dc = wx.PaintDC (self.f)
        dc.DrawBitmap(buffer, 0, 0)
        
    def repaint(self): 
        """
        Neuzeichnen der als dreckig markierten Bereiche. Muss aus paint-
        Event heraus aufgerufen werden. Benutzt draw() und draw_background().
        """    
        canvasx0, canvasy0 = self.origin
        paintDC = wx.PaintDC (self._window)
            
        if 0: # Repaint whole canvas
            w, h = self._window.Size
            region = wx.Region(0, 0, w, h)
            self.draw_background(paintDC, region)
            self.draw(paintDC, region)

        else: # Repaint changed region only
            region = self._window.GetUpdateRegion()        
            updateRect = region.GetBox()
            bufferX = updateRect.GetLeft() 
            bufferY = updateRect.GetTop() 
            bufferWidth = updateRect.GetWidth()
            bufferHeight = updateRect.GetHeight()

            memoryDC = wx.MemoryDC()
            offscreenBuffer = wx.EmptyBitmap (bufferWidth, bufferHeight)
            self.buffer = offscreenBuffer
            memoryDC.SelectObject (offscreenBuffer)
            memoryDC.SetDeviceOrigin (-bufferX+canvasx0, -bufferY+canvasy0)
            
            dc = memoryDC        
            self.draw_background(dc, region)
            self.draw(dc, region)
            
            paintDC.Blit (bufferX, bufferY, # dest
                          bufferWidth, bufferHeight, 
                          memoryDC,
                          bufferX-canvasx0, bufferY-canvasy0) # source
            if 0:
                paintDC.SetBrush(wx.TRANSPARENT_BRUSH)
                paintDC.DrawRectangle(bufferX, bufferY, bufferWidth, bufferHeight)
                self.f.Refresh()

    def draw(self, dc, region=None):
        canvasx, canvasy = self.origin
        gcdc = wx.GCDC(dc)
        for drawable in tuple(self.iter_drawables()):
            bounds = drawable.bounds
            winbounds = bounds.Moved((canvasx, canvasy))
            position = drawable.position

            if (region is None or region.ContainsRect(winbounds) != wx.OutRegion):
                gcdc.SetDeviceOrigin(*position)
                drawable.draw(gcdc)                
        gcdc.Destroy() # Das ist wichtig!!!! Ich weiss nicht warum
            
    def draw_background(self, dc, region=None):
        bg = wx.Brush(self._window.GetBackgroundColour())
        dc.SetBackground(bg)
        dc.Clear()
        return
        
    def pick(self, pos):
        # Wählt das drawable an Position pos und gibt es zurück,
        # bzw. None.
        drawables = reversed(tuple(self.iter_drawables()))
        for drawable in drawables:
            if drawable.bounds.Inside(pos) and drawable.hit_test(pos):
                return drawable
        return None

    def contextmenu_event(self, event):
        event.Skip()


        
class SimpleCanvas(CanvasBase):
    def __init__(self, *args, **kwds):
        self._drawables = []
        CanvasBase.__init__(self, *args, **kwds)
        
    def iter_drawables(self):
        for drawable in self._drawables:
            yield drawable
        
    def insert_drawable(self, i, drawable):
        self._drawables.insert(i, drawable)
        self.refresh(drawable.bounds)
        
    def remove_drawable(self, drawable):
        self._drawables.remove(drawable)
        if drawable is self._current:
            self.select_current(None)
        self.refresh(drawable.bounds)
        
    def append_drawable(self, drawable):
        self._drawables.append(drawable)
        self.refresh(drawable.bounds)



class DrawingElement(Drawable):
    is_selectable = True
    
    line_color = overridable_property('line_color', 
        "Read/Write.")
    bg_color = overridable_property('bg_color', 
        "Read/Write.")
        
    def __init__(self, canvas, **kw):
        self._line_color = wx.Colour(0,  0,  0, 100)
        self._bg_color = wx.Colour(255,  255,  255, 100)
        Drawable.__init__(self, canvas, **kw)
            
    def get_line_color(self):
        return self._line_color
        
    def set_line_color(self, color):
        self._line_color = color
        self.refresh()        

    def get_bg_color(self):
        return self._bg_color
        
    def set_bg_color(self, color):
        self._bg_color = color
        self.refresh()        


    ### ab hier sollte alles weg!
    def mouse_event(self, event):
        if event.Dragging():
            handler = self._canvas.window.EventHandler
            start = handler.get_drag_start()
            delta = event.Position-start
            print delta
            self.position = event.Position
        return False
        
    #def hit_test(self, pos):
    #    return self._bounds.Inside(pos)
                
        

class Rectangle(DrawingElement):
    def draw(self, dc):
        pen = wx.Pen(self._line_color)
        if not self._selected:
            bg = self._bg_color
        else:
            f = 1.5
            r, g, b = self._bg_color
            l = map(lambda x: min(255, (int(x))), (f*r, f*g, f*b, 255))
            bg = wx.Colour(*l)
        brush = wx.Brush(bg)
        w, h = self.size
        dc.SetBrush(brush) 
        dc.SetPen(pen)        
        dc.DrawRectanglePointSize((0,0), (w-1, h-1))

    def ssDrawMask(self, dc):
        dc.SetBrush(wx.WHITE_BRUSH) 
        w, h = self.bounds.size
        dc.DrawRectanglePointSize((0,0), (w-1, h-1))    


class Circle(DrawingElement):
    def draw(self, dc):
        pen = wx.Pen(self._line_color)
        if not self._selected:
            bg = self._bg_color
        else:
            f = 1.5
            r, g, b = self._bg_color
            l = map(lambda x: min(255, (int(x))), (f*r, f*g, f*b, 255))
            bg = wx.Colour(*l)
        brush = wx.Brush(bg)
        w, h = self.size
        dc.SetBrush(brush) 
        dc.SetPen(pen)        
        dc.DrawEllipseRect(wx.Rect(0, 0, w, h))
        

        
def open_shell(**locals):
    import wx.py
    f = wx.Frame(None)
    box = wx.BoxSizer(wx.HORIZONTAL)
    shell = wx.py.shell.Shell(f, -1, locals=locals)
    box.Add(shell, 1, wx.EXPAND)
    f.SetSizer(box)
    box.Fit(f)
    f.Fit()
    f.Show()
    
def test():
    class CanvasFrame(wx.Frame):
        def __init__(self, parent, *args, **kwds):
            wx.Frame.__init__(self, parent, *args, **kwds)
            self.canvas = SimpleCanvas(self)
    
    app = wx.App(False)
    frame = CanvasFrame(parent=None)
    canvas = frame.canvas
    rect = Rectangle(canvas, size=(80, 80), position=(10, 10))
    rect.bg_color = wx.Colour(0,  255,  0, 100)
    circle = Circle(canvas, size=(80,80), position=(60, 30))
    circle.bg_color = wx.Colour(255,  0,  0, 100)
        
    canvas.append_drawable(rect)
    canvas.append_drawable(circle)
    frame.Show()

    canvas.scroll = 100, 0
    import testing
    testing.pyshell(locals())
    app.MainLoop()
    
     
if __name__ == '__main__':
    test()
