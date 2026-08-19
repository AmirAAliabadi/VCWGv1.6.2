class Window(object):

    def __init__(self,W,H,Loc,Eff,BFace,opFrac,Scr):
        self.width = W #window width in meters
        self.height = H #window height in meters
        self.zCoord = Loc #window location above ground in meters
        self.screen = Scr #0 for no window insect screen. 1 for window insect screen
        self.state = 1.0 #window state. 1 = fully open. 0 = fully closed.
        self.effectiveness = Eff #ASHRAE parameter for window effectiveness
        self.face = BFace #building face location of this window. "X" for X-directed face. "Y" for Y-directed face.
        self.openAreaFraction = opFrac #Fraction of window area that can open
        