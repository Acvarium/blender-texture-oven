

if "bpy" in locals():
    import importlib
    importlib.reload(bt_gui_panel)
else:
    from . import (bt_gui_panel)
    
import bpy


class TextureOven_GUI(bpy.types.Operator):
    
    bl_idname = "textureoven.makepanel"
    bl_label = "TextureOven Reports"
    bl_description = "TextureOven Reports" 
    bl_options = {'REGISTER'}

    def __init__(self):
        # Init Handlers
        self.drawHandle = None
        self.eventHandle  = None
        self.guiObjects = []
        
        # Create GUIObjects
        self.panel = bt_gui_panel.GUIPanel("Panel",30, 30, 300, 30)
        self.guiObjects = [self.panel]
    
    def unregisterHandlers(self, context):
        print("Remove GUI")
        context.window_manager.event_timer_remove(self.eventHandle)
        bpy.types.SpaceView3D.draw_handler_remove(self.drawHandle, "WINDOW")
        self.drawHandle = None
        self.eventHandle  = None
        self.guiObjects.clear()
 
    def registerHandlers(self, args, context):
        self.drawHandle = bpy.types.SpaceView3D.draw_handler_add(self.drawGUI, args, "WINDOW", "POST_PIXEL")
        self.eventHandle = context.window_manager.event_timer_add(0.1, window=context.window)
        
    def checkEvents(self, event):
        result = False
        for guiObject in self.guiObjects:
            if guiObject.checkEvent(event):
                result = True
        return result
        
    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()
        
        if self.checkEvents(event):
            return {'RUNNING_MODAL'}   
  
        
        if event.type in {"ESC"}:
            self.unregisterHandlers(context)
            return {'CANCELLED'}
                    
        return {"PASS_THROUGH"}
        
    def finish(self):
        self.unregisterHandlers(context)
        return {"FINISHED"}
        
    def invoke(self, context, event):
        print("Start GUI")
        args = (self, context)     
        self.registerHandlers(args, context)      
        context.window_manager.modal_handler_add(self)
        
        for guiObject in self.guiObjects:
            guiObject.deploy(context)
        
        
        return {"RUNNING_MODAL"}
        
    # Draw handler to paint onto the screen
    def drawGUI(self, op, context):
        for guiObject in self.guiObjects:
            guiObject.draw()

        