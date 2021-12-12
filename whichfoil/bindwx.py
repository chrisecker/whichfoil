# -*- coding: latin-1 -*-


import wx

from .viewbase import ViewBase



class InvalidValue(Exception):
    pass


class Binder(ViewBase):
    _attrname = None    
    _widget_state = None
    _model_state = None

    def __init__(self, model, attrname, widget):
        ViewBase.__init__(self)
        self.set_model(model)
        self._attrname = attrname
        self._widget = widget
        widget.Bind(wx.EVT_WINDOW_DESTROY, self.widget_destroyed)
        self.update_widget()
        
    def widget_destroyed(self, event):
        event.Skip()
        self.destroy()

    def check_widget(self, *args):
        # Prüfen, ob widget sich gegenüber dem gespeicherten Zustand
        # verändert hat
        #print "received widget change"
        if self._widget_state == self.get_widget_state():
            return
        self.update_model()

    def model_changed(self, *args):
        # Called by model to notify changes.
        #print "binder: model changed"
        if self._model_state == self.get_model_value():
            return
        self.update_widget()

    def save_state(self):
        self._model_state = self.get_model_value()
        self._widget_state = self.get_widget_state()

    def update_model(self):
        # Wert aus Widget in Model eintragen
        try:
            value = self.get_widget_value()
        except InvalidValue:
            self.update_widget()
            return        
        self.set_model_value(value)
        self.save_state()

    def update_widget(self):
        # Set widget from model
        value = self.get_model_value()
        try:
            self.set_widget_value(value)
            self.save_state()
        except wx.PyDeadObjectError:
            self.destroy()

    def set_model_value(self, value):
        # helper
        setattr(self.model, self._attrname, value)
        self._model_state = value

    def get_model_value(self):
        # helper
        return getattr(self.model, self._attrname)

    ### to be implemented
    def get_widget_state(self):
        raise NotImplemented()

    def set_widget_value(self, value):
        raise NotImplemented()

    def get_widget_value(self):
        raise NotImplemented()

        

class TextBinder(Binder):
    def __init__(self, model, attrname, widget):
        Binder.__init__(self, model, attrname, widget)
        self._widget.Bind(wx.EVT_TEXT_ENTER, self.check_widget)
        self._widget.Bind(wx.EVT_KILL_FOCUS, self.check_widget)
        
    def get_widget_state(self):
        return self._widget.GetValue()

    def get_widget_value(self):
        s = self._widget.GetValue()
        return self.fromstr(s)

    def set_widget_value(self, value):
        s = self.tostr(value)
        self._widget.SetValue(s)

    def tostr(self, value):
        return value

    def fromstr(self, s):
        return s


