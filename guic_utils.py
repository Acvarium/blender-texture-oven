import bpy

def GetTransform(obj):

    eol = False
    cur_x = obj.rect.x
    cur_y = obj.rect.y
    currentObj = obj
    while not eol:
        if(currentObj.parent == None):
            eol = True
        else:
            cur_x += currentObj.parent.rect.x
            cur_y += currentObj.parent.rect.y  
            currentObj = currentObj.parent

    return (cur_x , cur_y)

# Color Functions
def ColorFromHex(color):
    r = color[:2]
    g = color[2:4]
    b = color[4:6]
    a = color[6:8]
    
    col = (int(r,16)/255.0,int(g,16)/255.0,int(b,16)/255.0,int(a,16)/255.0)
    return col

# Rect Classs
class Rect():
    def __init__(self,x,y,w,h,wf):
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        self.widthFill =wf
        
class RectGraph():
     def __init__(self,x,y,w,h):
        self.x = x
        self.y = y
        self.width = w
        self.height = h 

# Polygon Classes
class BoxGraph():
    def __init__(self,obj):
        self.x = obj.rect.x
        self.y = obj.rect.y
        self.width = obj.rect.width
        self.height = obj.rect.height
        self.aspect = self.height/self.width
        self.obj = obj        
            
    def CheckOnRect(self,x,y,area):
        us = bpy.context.preferences.view.ui_scale
        xFinal,yFinal = GetTransform(self.obj)

        x1 = (xFinal) * us;
        y1 = (area.height - (yFinal)) * us;
        x2 = (x1 + self.width * us) ;
        y2 = (y1 - self.height * us) ;
        
        if(x > x1 and x < x2):
            if(y < y1 and y > y2):
                return True
        return False
        
    def GetGraphCoords(self,area):
        us = bpy.context.preferences.view.ui_scale
        xFinal,yFinal = GetTransform(self.obj)

        x1 = (xFinal) * us;
        y1 = (area.height - (yFinal) - self.width) * us;

        return x1,y1,int(self.width * us),self.aspect

class BoxPolygon():
    def __init__(self,obj,rect):
        self.x = rect.x
        self.y = rect.y
        self.width = rect.width
        self.height = rect.height
        self.widthFill = rect.widthFill
        self.obj = obj
           
    def CheckOnRect(self,x,y,area):
        us = bpy.context.preferences.view.ui_scale
        xFinal,yFinal = GetTransform(self.obj)

        x1 = (xFinal) * us;
        y1 = (area.height - (yFinal)) * us;
        x2 = (x1 + self.width - self.widthFill * us) ;
        y2 = (y1 - self.height * us) ;
        
        vertices = (
            (x1,y1),
            (x2,y1),
            (x1,y2), 
            (x2,y2)
        )
        
        if(x > x1 and x < x2):
            if(y < y1 and y > y2):
                return True
        return False
        
    def GetBoxPoints(self,area):
        # Vertex Struct
        # 2 - 3
        # |   |
        # 0 - 1
        
        us = bpy.context.preferences.view.ui_scale
        xFinal,yFinal = GetTransform(self.obj)

        x1 = (xFinal) * us;
        y1 = (area.height - (yFinal)) * us;
        x2 = (x1 + (self.width - self.widthFill) * us) ;
        y2 = (y1 - self.height * us) ;
        
        vertices = (
            (x1,y1),
            (x2,y1),
            (x1,y2), 
            (x2,y2)
        )
        
        indices = ((0, 1, 2), (2, 1, 3))
        return vertices, indices
        

    
        
