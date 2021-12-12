import wx


def extract_accel(s):
    return
    # Extract accelerator information from menu
    # labels. Currently only extracts simple accelerators of
    # the form 'Ctrl-A'. Many accelerators are not parsed
    # correctly, such as 'Shift-Return'. This is ok for now,
    # as these are already handled in nbview.  Extracting
    # accelerators became necessary with wxpython 3.0 on. I
    # think it is a bug.
    if not '\t' in s: return
    a, b = s.split("\t", 1)
    if not '-' in b:
        key = b
        modifier = None
    else:
        modifier, key = b.split('-', 1)
    #print repr(b)
    if len(key) == 0:
        keycode = ord("-")
    elif len(key) == 1:
        keycode = ord(key)
    else:
        keycode = dict(
            up = wx.WXK_UP,
            down = wx.WXK_DOWN,
            left = wx.WXK_LEFT,
            right = wx.WXK_RIGHT,
        )[key]
    m = dict(Ctrl=wx.ACCEL_CTRL, Alt=wx.ACCEL_ALT)
    #print repr(b), repr(modifier), ord(key)
    if not modifier in m:
        return
    return m[modifier], ord(key)

        
def mk_menu(handler, entries, updaters=None, accel=None):
    if updaters is None:
        updaters = []
    if accel is None:
        accel = []
    menu = wx.Menu()
    for entry in entries:
        if entry is None:
            menu.AppendSeparator()
        elif type(entry) is list:                    
            submenu = mk_menu(entry[1:])
            menu.AppendSubMenu(submenu, entry[0])
        else:
            fun = getattr(handler, entry)
            title = fun.__doc__
            item = menu.Append(-1, title)
            handler.Bind(wx.EVT_MENU, lambda e, fun=fun:fun(), item)
            shortcut = extract_accel(title)
            if shortcut is not None:
                accel.append(shortcut+(item.Id,))
            if hasattr(handler, 'can_'+entry):
                fun = getattr(handler, 'can_'+entry)
                def update(fun=fun, item=item, menu=menu):
                    menu.Enable(item.Id, fun())
                updaters.append(update)
                update()
    return menu


def make_ctxtmenu(handler):
    # Simple menu. No status updates and no accelerators.    
    menu = wx.Menu()
    for entry in handler.ctxt_entries:
        fun = getattr(handler, entry)
        active = True
        try:
            statefun = getattr(handler, 'can_'+entry)
            active = statefun()
        except AttributeError:
            pass                        
        title = fun.__doc__
        item = menu.Append(-1, title)
        menu.Enable(item.Id, active)
        menu.Bind(wx.EVT_MENU, fun, item)
    return menu

