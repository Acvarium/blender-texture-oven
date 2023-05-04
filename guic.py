# GUIC - Graphical User Interface of Cogumelo
# Use to Create Graphical User Interfaces for Blender 2.8 addons

# Features:
# - Panels
# - Use Graphical Forms and custom icons
# - Labels
# - Buttons
# - Load Images from Blender Data and External

import bpy

class GUIOperator(bpy.types.Operator):

    bl_idname = "textureoven.makepanel"
    bl_label = "TextureOven Reports"
    bl_description = "TextureOven Reports"
    bl_options = {'REGISTER'}

    def __init__(self):
        # User Configurables
        self.escToEnd = False

        # Internal Objects
        self.drawHandle = None
        self.guiObjects = []
        self.area = None
        self.areaOwner = ""
        self.editor = ""
        self.guiObjects = []
        self.markToRemove = False
        self.GUIUpdate = []

    def setGUIObjects(self):
        for attr, value in self.__dict__.items():
            if("guic_" in str(type(value))):
                self.guiObjects.append(value)

    def unregisterHandlers(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self.drawHandle, "WINDOW")

        self.drawHandle = None
        self.guiObjects.clear()

    def registerHandlers(self, args, context):
        self.drawHandle = bpy.types.SpaceView3D.draw_handler_add(self.drawGUI, args, "WINDOW", "POST_PIXEL")

    def checkEvents(self, event):

        # Update Events
        result = False
        for guiObject in self.guiObjects:
            if guiObject.checkEvent(event):
                result = True

        return result

    def modal(self, context, event):
        # Check if yet valid
        hasArea = False

        for area in bpy.context.screen.areas:
            if(self.areaOwner == str(bpy.context.area)):
                if(bpy.context.area):
                    if(self.editor == bpy.context.area.spaces[0].type):
                        hasArea = True

        if(not hasArea):
            self.unregisterHandlers(context)
            return {'CANCELLED'}


        if context.area:
            context.area.tag_redraw()

        if self.checkEvents(event):
            return {'RUNNING_MODAL'}


        if event.type in {"ESC"}:
            if(self.escToEnd == True):
                self.unregisterHandlers(context)
                return {'CANCELLED'}

        if(self.markToRemove):
            self.unregisterHandlers(context)
            return {'CANCELLED'}

        return {"PASS_THROUGH"}

    def finish(self):
        self.markToRemove = True

    def invoke(self, context, event):
        self.areaOwner = str(bpy.context.area)
        self.area = bpy.context.area
        self.editor = bpy.context.area.spaces[0].type

        args = (self, context)
        self.registerHandlers(args, context)
        context.window_manager.modal_handler_add(self)
        bpy.app.timers.register(self.Update)
        return {"RUNNING_MODAL"}

    def StartGUI(self):
        self.setGUIObjects()

    def ForceRedraw(self):
        if(self.area != None):
            self.area.tag_redraw()

    def Update(self):
        try:
            for func in self.GUIUpdate:
                func()
        except:
            return
        return 0.01

    def drawGUI(self, op, context):
        if(not self.markToRemove):
            for guiObject in self.guiObjects:
                guiObject.draw()
