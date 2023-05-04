
if "bpy" in locals():
    import importlib
    importlib.reload(guic)
    importlib.reload(guic_graph)
    importlib.reload(guic_box)
    importlib.reload(guic_graphButton)
else:
    from . import (guic)
    from . import (guic_graph)
    from . import (guic_box)
    from . import (guic_graphButton)

import bpy
import os

class TextureOvenReports(guic.GUIOperator):

    bl_idname = "textureoven.report"
    bl_label = "TextureOven Reports"
    bl_description = "TextureOven Reports"
    bl_options = {'REGISTER'}

    def execute(self,context):
        bpy.context.scene.TextureOven_Jobs.is_baking = True;
        return self.invoke(context, None)

    def LoadBakeReports():
        script_file = os.path.realpath(__file__)
        directory = os.path.dirname(script_file)
        try:
            reports = json.loads(open(directory + "/report.json").read())
        except:
            return None

        return reports


    def checkProgress(self):
        try:
            if(bpy.context.scene.TextureOven_Jobs.is_baking == False):
                self.finish()
                self.area = bpy.context.area
                return

            # Check if yet exist
            self.objectProgress.graph
        except:
            return

        data = bpy.context.scene.TextureOven_ReportData


        #self.panelAr2_Lb1.graph = "Baking Job: " +  str(data.jobCurrent) + "/" + str(data.jobCount)
        self.objectProgress.graph = "Baking Object: " +  str(data.objCurrent) + "/" + str(data.objCount)
        self.passProgress.graph = "Baking Pass: " +  str(data.passCurrent) + "/" + str(data.passCount)


        # Global Progress
        self.GlobalValue.graph = "Baking Image: " + str(max(data.processCurrent,0)  ) + " of " + str(data.processCount)
        percentProcess = 0
        if(data.processCount > 0):
            percentProcess = (data.processCurrent)/float(data.processCount)

        if(percentProcess < 1):
            self.GlobalPercent.graph = str(int(max(percentProcess*100,0))) + "%"
        else:
            self.GlobalPercent.graph = "99%"

        self.globalProgress.setFill(max(percentProcess,0))

        self.area.tag_redraw()
        return 0.03

    def __init__(self):
        super().__init__()

        script_file = os.path.realpath(__file__)
        directory = os.path.dirname(script_file)
        self.area = bpy.context.area

        # HEADER

        self.header = guic_graph.GUIGraph(200,200,200,90,guic_graph.GUIGraph.FORM_ROUNDED_BOX,color ="03AAD5FF")
        self.header.isDragable = True

        self.footer = guic_graph.GUIGraph(0,220,200,0,guic_graph.GUIGraph.FORM_ROUNDED_BOX,color ="03AAD5FF",parent = self.header)

        self.logo = guic_graph.GUICustom(20,-20,80,0,"D","forms2.ttf","FFFFFFFF",parent = self.header)

        self.bodyCircle = guic_graph.GUIGraph(-50,70,300,300,guic_graph.GUIGraph.FORM_CIRCLE,color ="03AAD5FF",parent=self.header)
        self.bodyC2 = guic_graph.GUIGraph(10,10,280,280,guic_graph.GUIGraph.FORM_CIRCLE,color ="FFFFFFFF",parent=self.bodyCircle)
        self.bodyC3 = guic_graph.GUIGraph(10,10,260,260,guic_graph.GUIGraph.FORM_CIRCLE,color ="424242FF",parent=self.bodyC2)


        self.GlobalPercent = guic_graph.GUICustom(70,50,60,0,"99%","roboto.ttf","FFFFFFFF",parent = self.bodyC3)
        self.GlobalValue = guic_graph.GUICustom(60,130,12,0,"10 of 13 Process","roboto.ttf","FFFFFFFF",parent = self.bodyC3)

        self.progressBg = guic_box.GUIBox(20,150,220,10,"343434FF",self.bodyC3)
        self.globalProgress = guic_box.GUIBox(20,150,220,10,"AAFFFFFF",self.bodyC3,0.5)

        self.objectProgress = guic_graph.GUICustom(60,180,10,0,"Baking Object:","roboto.ttf","FFFFFFFF",self.bodyC3)
        self.passProgress = guic_graph.GUICustom(60,200,10,0,"Baking Pass:","roboto.ttf","FFFFFFFF",self.bodyC3)

        self.abort = guic_graphButton.GUIGraphButton(15,160,170,20,guic_graphButton.GUIGraphButton.LONG_ROUNDED_BOX,color ="343434FF",parent =self.footer)
        self.abort.hover_color = "444444FF"
        self.abort.press_color = "949494FF"
        self.abort.onClickActions.append(self.AbortFunction)

        self.abortLabel = guic_graph.GUICustom(55,5,15,0,"Cancel","roboto.ttf","FFFFFFFF",self.abort)


        self.setGUIObjects()

        self.progress = bpy.app.timers.register(self.checkProgress)

    def AbortFunction(self,event):
        try:
            pid = bpy.context.scene.TextureOven_ReportData.current_processPid
            os.kill(pid, 9)
            print("------------------------------------ ABOOORT -----------------------------------")
            self.finish()
        except:
            self.finish()
            pass

    def finish(self):
        super().finish()
