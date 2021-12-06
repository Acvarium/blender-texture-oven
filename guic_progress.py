if "bpy" in locals():
    import importlib
    importlib.reload(guic_utils)
else:
    from . import (guic_utils)
    
import bpy
import bgl
import gpu
from gpu_extras.batch import batch_for_shader
    
class GUIProgress():
    def __init__(self, x, y, width, height,progress,color="FFFFFFFF",parent=None):
        self.enabled = True
        self.rect = guic_utils.Rect(x,y,width,height,0)
        self.parent = parent # Recursive Parent is not allowed

        self.progress = progress
        self.color = color
        self.progress_color = "FFFFFFFF"
        self.area_origin = str(bpy.context.area) # Freeze the context area value in the inicialization moment
        
        self.isDragable = False
        self.draging = False
        
        self.lastEvent = None
        self.current_mousePos = [0,0]
        self.last_mousePos = [0,0]
        self.deltaPos = [0,0]
        
    # MOUSE EVENTS -----------------------------------------------------    
    def checkEvent(self,event):
                
        self.lastEvent = event
        self.current_mousePos = [event.mouse_region_x,event.mouse_region_y]
        self.deltaPos = [self.current_mousePos[0] - self.last_mousePos[0],self.current_mousePos[1] - self.last_mousePos[1]]

        if(self.lastEvent.type == "LEFTMOUSE"):
            onRect = guic_utils.BoxPolygon(self,self.rect).CheckOnRect(self.current_mousePos[0],
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

        # BACKGROUND
        vertices,indices = guic_utils.BoxPolygon(self,self.rect).GetBoxPoints(bpy.context.area)

        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
        shader.bind()
        shader.uniform_float("color", guic_utils.ColorFromHex(self.color))
        bgl.glEnable(bgl.GL_BLEND)
        batch.draw(shader)
        bgl.glDisable(bgl.GL_BLEND)

        
        # PROGRESS
        rectProgress = guic_utils.Rect(self.rect.x,self.rect.y,self.rect.width,self.rect.height,self.rect.width * (1-min(self.progress,1)))
        vertices2,indices2 = guic_utils.BoxPolygon(self,rectProgress).GetBoxPoints(bpy.context.area)
        
        shader2 = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch2 = batch_for_shader(shader2, 'TRIS', {"pos": vertices2}, indices=indices2)
        shader2.bind()
        shader2.uniform_float("color", guic_utils.ColorFromHex(self.progress_color))
        bgl.glEnable(bgl.GL_BLEND)
        batch2.draw(shader)
        bgl.glDisable(bgl.GL_BLEND)
        
    # UTILS -----------------------------------------------------
    def check_enabled(self):
        if(str(bpy.context.area) != self.area_origin or not self.enabled):
            return False
        return True

    def setProgress(self,value):
        self.progress = self.rect.width * (1-min(value,1))
