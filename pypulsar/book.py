import wx
import wx.aui as Aui

#==============================
class AuiBook(Aui.AuiNotebook):
#==============================

#------------------------------------------------------------------------------
    def __init__(self,
                 parent,
##                 toolbar,
                 size=wx.DefaultSize,
                 style= wx.NO_BORDER|
                              Aui.AUI_NB_DEFAULT_STYLE|
                              Aui.AUI_NB_WINDOWLIST_BUTTON):
#------------------------------------------------------------------------------
           Aui.AuiNotebook.__init__(self, parent, size=size, style=style)
           self.parent=parent
           self.progress= parent.progress
