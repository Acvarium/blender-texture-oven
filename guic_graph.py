if "bpy" in locals():
    import importlib
    importlib.reload(guic_utils)
else:
    from . import guic
    from . import guic_utils

import bpy
import bgl
import blf
import gpu
import os
import math

from gpu_extras.batch import batch_for_shader

class GUIGraphBase():
    def __init__(self,x, y, width,height,index,source,color = "FFFFFFFF",parent = None,rotation=0):
        self.enabled = True
        self.rect = guic_utils.RectGraph(x,y,width,height)
        self.parent = parent # Recursive Parent is not allowed

        self.color = color
        self.area_origin = str(bpy.context.area) # Freeze the context area value in the inicialization

        self.isDragable = False
        self.draging = False
        self.useShadow = False

        self.lastEvent = None
        self.current_mousePos = [0,0]
        self.last_mousePos = [0,0]
        self.deltaPos = [0,0]
        self.dpi = 96
        self.rotation = math.radians(rotation)

        script_file = os.path.realpath(__file__)
        directory = os.path.dirname(script_file)

        graphPath = directory + "/" + source
        if os.path.exists(graphPath):
            self.graphTable = blf.load(graphPath)
        self.graph = index

    # MOUSE EVENTS -----------------------------------------------------
    def checkEvent(self,event):

        self.lastEvent = event
        self.current_mousePos = [event.mouse_region_x,event.mouse_region_y]
        self.deltaPos = [self.current_mousePos[0] - self.last_mousePos[0],self.current_mousePos[1] - self.last_mousePos[1]]

        if(self.lastEvent.type == "LEFTMOUSE"):
            onRect = guic_utils.BoxGraph(self).CheckOnRect(self.current_mousePos[0],
                                                                                self.current_mousePos[1],
                                                                                bpy.context.area)
            if(self.lastEvent.value == "PRESS" and onRect):
                self.onPress(event)
                self.last_mousePos = self.current_mousePos
                return True

            elif(self.lastEvent.value == "CLICK" and onRect ):
                self.onClickInside(event)
                self.last_mousePos = self.current_mousePos
                return True

            else:
                self.onRelease(event)

        if(event.type == 'MOUSEMOVE'):
            self.onMouseMove(event)

        self.last_mousePos = self.current_mousePos
        return False

    def onClickInside(self,event):
        pass

    def onPress(self,event):
        self.draging = True
        pass

    def onRelease(self,event):
        if(self.draging):
            self.draging = False

    def onMouseMove(self,event):
        if(self.draging and self.isDragable):
            self.rect.x += self.deltaPos[0]
            self.rect.y -= self.deltaPos[1]

    # DRAW -----------------------------------------------------
    def draw(self):

        if(not self.check_enabled()):
            return

        x,y,size,aspect = guic_utils.BoxGraph(self).GetGraphCoords(bpy.context.area)

        blf.position(self.graphTable, x, y, 0)
        col = guic_utils.ColorFromHex(self.color)
        blf.color(self.graphTable,col[0],col[1],col[2],col[3])

        us = bpy.context.preferences.view.ui_scale
        blf.size(self.graphTable, size, self.dpi )

        #blf.aspect(self.graphTable,1.0)
        blf.enable(self.graphTable,1)
        blf.rotation(self.graphTable,self.rotation)

        if(self.useShadow == True):
            blf.enable(self.graphTable,4)
            blf.shadow(self.graphTable,3,0,0,0,0.1)
            blf.shadow_offset(self.graphTable,2,-2)
        else:
            blf.disable(self.graphTable,4)

        blf.draw(self.graphTable, self.graph)
        blf.disable(self.graphTable,1)

    # UTILS -----------------------------------------------------
    def check_enabled(self):
        if(str(bpy.context.area) != self.area_origin or not self.enabled):
            return False
        return True

class GUIGraph(GUIGraphBase):

    FORM_BOX = "E"
    FORM_ROUNDED_BOX = "A"
    FORM_ROUNDED_CORNER = "H"
    FORM_CIRCLE = "F"

    def __init__(self,x,y,width,height,form,color ="FFFFFFFF",parent = None,rotation = 0):
            super().__init__(x,y,width,height,form,"forms2.ttf",color = color,parent = parent,rotation = rotation)

class GUICustom(GUIGraphBase):
    def __init__(self,x,y,width,height,value,source,color ="FFFFFFFF",parent = None,rotation =0):
            super().__init__(x,y,width,height,value,source,color = color,parent = parent,rotation = rotation)
