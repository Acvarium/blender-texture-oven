

if "bpy" in locals():
    import importlib
    importlib.reload(guic_utils)
else:
    from . import (guic_utils)
    
import bpy
import bgl
import gpu
from gpu_extras.batch import batch_for_shader

    
class GUIButton():
    def __init__(self,name, x, y, width, height,color="FFFFFFFF",parent=None):
        self.name = name
        self.enabled = True
        self.rect = guic_utils.Rect(x,y,width,height,1)
        self.parent = parent # Recursive Parent is not allowed
        
        self.color = color
        self.normal_color = "FFFFFFFF"
        self.hover_color = "FFAAFFFF"
        self.press_color = "AAFFFFFF"
        self.area_origin = str(bpy.context.area) # Freeze the context area value in the inicialization moment
        
        self.isDragable = False
        self.draging = False
        
        self.lastEvent = None
        self.current_mousePos = [0,0]
        self.last_mousePos = [0,0]
        self.deltaPos = [0,0]
        
        self.onClickActions = []
        self.onHoverActions = []
        
    # MOUSE EVENTS -----------------------------------------------------    
    def checkEvent(self,event):
                
        self.lastEvent = event
        self.current_mousePos = [event.mouse_region_x,event.mouse_region_y]
        self.deltaPos = [self.current_mousePos[0] - self.last_mousePos[0],self.current_mousePos[1] - self.last_mousePos[1]]
        
        onRect = guic_utils.BoxPolygon(self.rect,self.parent).CheckOnRect(self.current_mousePos[0],
                                                                                self.current_mousePos[1],
                                                                                bpy.context.area)
        self.color = self.normal_color
        
        if(onRect and not self.lastEvent.type == "LEFTMOUSE" ):
            self.color = self.hover_color
            self.onHover(event)

        elif(self.lastEvent.type == "LEFTMOUSE"):
        
            if(self.lastEvent.value == "PRESS" and onRect): 
                self.onClick(event)
                
                self.color = self.press_color
                self.last_mousePos = self.current_mousePos
                return True

            else:
                self.onRelease(event)

        if(event.type == 'MOUSEMOVE'):
            self.onMouseMove(event)
        
        self.last_mousePos = self.current_mousePos
        return False
    
        
    def onClick(self,event):
        self.draging = True
        
        for func in self.onClickActions:
            func(event)
        
    def onRelease(self,event):
        if(self.draging):
            self.draging = False
        
    def onMouseMove(self,event):
        if(self.draging and self.isDragable):
            self.rect.x += self.deltaPos[0]
            self.rect.y -= self.deltaPos[1]
            
    def onHover(self,event):
        for func in self.onHoverActions:
            func(event)
        

    # DRAW -----------------------------------------------------
    def draw(self):
        if(not self.check_enabled()):
            return
        
        vertices,indices = guic_utils.BoxPolygon(self.rect,self.parent).GetBoxPoints(bpy.context.area)

        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
        shader.bind()
        shader.uniform_float("color", guic_utils.ColorFromHex(self.color))
        
        bgl.glEnable(bgl.GL_BLEND)
        batch.draw(shader)
        bgl.glDisable(bgl.GL_BLEND)
        
    # UTILS -----------------------------------------------------
    def check_enabled(self):
        if(str(bpy.context.area) != self.area_origin or not self.enabled):
            return False
        return True
        
    
        
        
       