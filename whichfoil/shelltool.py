from pynotebook.nbview import NBView
import wx


class ShellTool(wx.Frame):
    def __init__(self, main):
        wx.Frame.__init__(self, main, style=wx.FRAME_FLOAT_ON_PARENT | wx.DEFAULT_FRAME_STYLE)
        self.main = main
        self.SetTitle("Python tool")
        win = wx.Panel(self)
        view = NBView(win)
        #if document is not None:
        #    view.set_model(document.script)
        pyclient = view._clients.get("python")
        ns = pyclient.namespace
        ns['document'] = main.document
        ns['main'] = main
        self.namespace = ns
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(view, 1, wx.ALL|wx.GROW, 1)
        win.SetSizer(box)
        win.SetAutoLayout(True)


def test_00():
    from document import AnalysisModel
    fn = r"../../igc/aussenlandung_twin_2018-06-17_86hxaaa1.igc"
    doc = AnalysisModel(igc_filename=fn)    
    app = wx.App()
    tool = ShellTool()
    app.MainLoop()


    
if __name__ == '__main__':
    test_00()
