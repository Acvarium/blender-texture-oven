

if "bpy" in locals():
    import importlib
    importlib.reload(guic_utils)
else:
    from . import (guic_utils)
    
import bpy
import bgl
import gpu
import os

from gpu_extras.batch import batch_for_shader
import bpy_extras.image_utils as img_utils

    
class GUIImage():
    def __init__(self,name, x, y, width, height,path):
        self.name = name
        self.enabled = True
        self.rect = guic_utils.Rect(x,y,width,height)
        self.parent = None # Recursive Parent is not allowed
        
        self.color = "FFFFFFFF"
        self.area_origin = str(bpy.context.area) # Freeze the context area value in the inicialization moment
        
        self.isDragable = True
        self.draging = False
        
        self.lastEvent = None
        self.current_mousePos = [0,0]
        self.last_mousePos = [0,0]
        self.deltaPos = [0,0]
        
        
        if(path != ""):
            self.image = img_utils.load_image(self.path)
            self.image.gl_load()
        
    # MOUSE EVENTS -----------------------------------------------------    
    def checkEvent(self,event):
                
        self.lastEvent = event
        self.current_mousePos = [event.mouse_region_x,event.mouse_region_y]
        self.deltaPos = [self.current_mousePos[0] - self.last_mousePos[0],self.current_mousePos[1] - self.last_mousePos[1]]

        if(self.lastEvent.type == "LEFTMOUSE"):
            onRect = guic_utils.BoxPolygon(self.rect,self.parent).CheckOnRect(self.current_mousePos[0],
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
        
        shader = gpu.shader.from_builtin('2D_IMAGE')
        vertices,indices = guic_utils.BoxPolygon(self.rect,self.parent).GetBoxPoints(bpy.context.area)
        
        batch = batch_for_shader(
            shader, 'TRI_FAN',
            {
                "pos": (vertices[0],vertices[1],vertices[3],vertices[2]),
                "texCoord": ((0, 0), (1, 0), (1, -1), (0, -1)),
            },
        )

        bgl.glActiveTexture(bgl.GL_TEXTURE0)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, self.image.bindcode)

        shader.bind()
        shader.uniform_int("image", 0)
        
        bgl.glEnable(bgl.GL_BLEND)
        batch.draw(shader)
        bgl.glDisable(bgl.GL_BLEND)
        
    # UTILS -----------------------------------------------------
    def check_enabled(self):
        if(str(bpy.context.area) != self.area_origin or not self.enabled):
            return False
        return True
        
    
        
        
       