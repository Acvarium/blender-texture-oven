# Copyright (C) Cogumelo Softworks
# License: http://www.gnu.org/licenses/gpl.html GPL version 3 or higher

# ##### BEGIN GPL LICENSE BLOCK #####
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "BakeTool",
    "author": "Cogumelo Softworks",
    "version": (2,5,1),
    "blender": (3,0,0),
    "location": "3DView > Render> BakeTool",
    "description": "Bake Solution for Cycles",
    "wiki_url":  "http://cgcookiemarkets.com/blender/all-products/baketool/?view=docs",
    "warning": "",
    "category": "Render"}

# Import Modules -------------------------------------------

if "bpy" in locals():
    import importlib
    importlib.reload(bt_autopack)
    importlib.reload(bt_utils)
    importlib.reload(bt_cyclesbake)
    importlib.reload(bt_reports)
else:
    from . import (bt_utils)
    from . import (bt_autopack)
    from . import (bt_cyclesbake)
    from . import (bt_reports)

import bpy
import random
import os

# BAKETOOL OPERATORS ----------------------------------------------------------------------------------------
class BakeTool_MakeAtlas(bpy.types.Operator):
    """Make a Atlas with Active UVs of selected objects"""
    bl_idname = "baketool.make_atlas"
    bl_label = "Make UV Atlas"
    bl_options = {'REGISTER', 'UNDO'}

    margin : bpy.props.FloatProperty(name = "Margin", default=0.1, min = 0.0, max = 1.0)
    area_weight : bpy.props.BoolProperty(name="Area Weight", default = True)

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        status = bt_autopack.DoAtlas(context,self.margin,self.area_weight,None)

        if status:
            self.report({'INFO'},status)

        return {'FINISHED'}

    def invoke(self, context, event):
         return context.window_manager.invoke_props_dialog(self)

    def draw(self,context):
        lay = self.layout
        lay.prop(self,"margin")
        lay.prop(self,"area_weight")

# CYCLES BAKE -------------------------------------------------------------------------------------------------
class BakeTool_CyclesBake(bpy.types.Operator):
    """ Bake this scene as config"""
    bl_idname = "baketool.cyclesbake"
    bl_label = "Bake"

    @classmethod
    def poll(cls,context):
        #if(context.scene.BakeTool_Jobs.is_baking == True):
            #return False;
        return True

    def execute(self, context):

        status = bt_cyclesbake.BakeCycles(context)
        if status != True:
            self.report({"ERROR"}, status)
            return {'FINISHED'}

        return {'FINISHED'}

# GROUPS AND SCENE CONFIGS -----------------------------------------------------------------------------------------
class BakeTool_Settings(bpy.types.PropertyGroup):


    format_enum = [ ("PNG","PNG","",1),
                    ("JPEG","JPEG","",2),
                    ("TIFF","TIFF","",3),
                    ("OPEN_EXR","EXR","",4),
                    ("TARGA","TGA","",5)]

    mode_enum = [   ("INDI","Individual","",1),
                    ("ATLAS","Atlas & Target","",2)]

    profile_type_enum =[             ("BAKETOOL","BakeTool","",1),
                                ("BLENDER","Build-in","",2)]

    profile_type : bpy.props.EnumProperty(name="PassMode",default = "BAKETOOL", items = profile_type_enum,description="Select the Pass Bake Mode")

    mode : bpy.props.EnumProperty(name = "Bake Mode",  description = "Atlas = Bake all Objects to one texture group, Individual = Bake all objects as individual", default= "INDI", items = mode_enum)

    path : bpy.props.StringProperty(default=bpy.utils.user_resource('SCRIPTS', path = "addons") + "/baketool/results/",subtype="DIR_PATH", description = "Save images in this location")
    #keep : bpy.props.BoolProperty(default=True, description = "Save images inside Blender too")
    target : bpy.props.StringProperty(description = "if Target is filled it will bake all passes and objects for the target selected")
    target_uv : bpy.props.StringProperty()
    cage : bpy.props.StringProperty(description = "Cast Rays to target object from a Cage")
    distance : bpy.props.FloatProperty(min=0.0, max=1.0, default = 0.5)
    bias : bpy.props.FloatProperty(min=0.0, max=1.0, default = 0.1)
    format : bpy.props.EnumProperty(name="Format", default = "PNG", items = format_enum, description = "File format to save the texture baked as")

    atlas_autoPack : bpy.props.BoolProperty(default=True, description = "Automatic Pack the UV of the Bake Objects in a single Atlas")
    atlas_autoPack_margin : bpy.props.FloatProperty(min=0.0, max=50.0, default = 0.05)
    atlas_autoPack_area : bpy.props.BoolProperty(default=True, description = "Use or not the Area Weight")

    generate_uvwrap : bpy.props.BoolProperty(default=True, description = "Automaticaly generate UVs for ojects in the list when it's not set")
    uvwrapper_margin : bpy.props.FloatProperty(default = 0.1, description = "Margin between islands")
    uvwrapper_angle : bpy.props.FloatProperty(default = 80.0, max = 89.0, description = "Max angle to break islands")

    postbake_importImages : bpy.props.BoolProperty(default=True, description = "Import image to current scene after bake")
    postbake_createEevee : bpy.props.BoolProperty(default=False, description = "Create Eevee scene with automatic materials")
    postBake_eeveePass : bpy.props.BoolProperty()

    device_enum = [("GPU","GPU","",1),("CPU","CPU","",2)]
    render_device : bpy.props.EnumProperty(name = "Device", default = "GPU", items = device_enum, description="The Compute Device used to Bake, GPU is recomended for speed and CPU for compatibility")

class BakeTool_ObjEntry(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty()
    uv : bpy.props.StringProperty()
    overwriteUV : bpy.props.StringProperty()

class BakeTool_ObjGroup(bpy.types.PropertyGroup):
    coll : bpy.props.CollectionProperty(type=BakeTool_ObjEntry)
    index : bpy.props.IntProperty()

class BakeTool_MaterialSettings(bpy.types.PropertyGroup):
    output : bpy.props.StringProperty()

class BakeTool_BakePass(bpy.types.PropertyGroup):

    cyclestype = [          ("COMBINED","Combined","",1),
                            ("AO","Ambient Occlusion","",2),
                            ("SHADOW","Shadow","",3),
                            ("NORMAL","Normal","",4),
                            ("UV","Uv","",5),
                            ("EMIT","Emit","",6),
                            ("ENVIRONMENT","Environment","",7),
                            ("DIFFUSE","Diffuse","",8),
                            ("GLOSSY","Glossy","",11),
                            ("ROUGHNESS","Roughness","",9),
                            ("TRANSMISSION","Transmission","",14),
                            ("SUBSURFACE","Subsurface","",17)]

    simplePassType = [      ("ALBEDO","Albedo","",1),
                            ("AO","Ambient Occlusion","",2),
                            ("NORMAL","Normal","",3),
                            ("ROUGHNESS","Roughness","",4),
                            ("METALLIC","Metallic","",5),
                            ("SUBSURFACE","Subsurface","",6),
                            ("SHADOWS","Shadows","",7),
                            ("ID","Id Map","",8),
                            ("SPECULAR","Specular","",9),
                            ("ALPHA","Alpha","",10)]

    sizetype = [                ("64","64","",1),
                                ("128","128","",2),
                                ("256","256","",3),
                                ("512","512","",4),
                                ("1024","1024","",5),
                                ("2048","2048","",6),
                                ("4096","4096","",7),
                                ("8192","8192","",8)]

    color_space_type = [        ("Linear","Linear","",1),
                                ("sRGB","sRGB","",2),
                                ("Non-Color","Non-Color","",3)]



    simpleNormalType =[                 ("+Y","Unity/OpenGL","",1),
                                        ("-Y","Unreal/DirectX","",2)]

    aliasing_type = [        ("None","None","",1),
                                ("2x","2x","",2),
                                ("4x","4x","",3)]

    colors_space : bpy.props.EnumProperty(name="Color Space",default = "Linear", items = color_space_type,description="Select The Color Space To Bake")

    type_simple : bpy.props.EnumProperty(name="Type",default = "ALBEDO", items = simplePassType,description="Select the Pass Bake Mode")

    normal_simple_mode : bpy.props.EnumProperty(name="Normal Type",default = "+Y", items = simpleNormalType,description="Select the Normal Map setup")

    # Cycles bake properties
    use_pass_diffuse : bpy.props.BoolProperty(default = True)
    use_pass_glossy : bpy.props.BoolProperty(default = True)
    use_pass_transmission : bpy.props.BoolProperty(default = True)
    #use_pass_ambient_occlusion : bpy.props.BoolProperty(default = True)
    use_pass_emit : bpy.props.BoolProperty(default = True)

    # Cycles sub passes properties
    use_pass_color : bpy.props.BoolProperty(default = True)
    use_pass_direct : bpy.props.BoolProperty(default = True)
    use_pass_indirect : bpy.props.BoolProperty(default = True)

    # Cycles Denoise
    use_denoising : bpy.props.BoolProperty(default = True)

    # Normal properties
    normal_space_cycles_enum = [("TANGENT","Tangent","",1),("OBJECT","Object","",2)]
    normal_space_bi_enum = [("CAMERA","Camera","",1),("WORLD","World","",2),("OBJECT","Object","",2),("TANGENT","Tangent","",4)]
    normal_axis_enum = [("POS_X","+X","",1),("POS_Y","+Y","",3),("POS_Z","+Z","",5),("NEG_X","-X","",2),("NEG_Y","-Y","",4),("NEG_Z","-Z","",6)]
    normal_space : bpy.props.EnumProperty(name="Space",default = "TANGENT", items = normal_space_cycles_enum,description="The normal space type to bake")
    normal_space_bi : bpy.props.EnumProperty(name="Space",default = "TANGENT", items = normal_space_bi_enum,description="The normal space type to bake")
    normal_r : bpy.props.EnumProperty(name="Red Channel",default = "POS_X", items = normal_axis_enum)
    normal_g : bpy.props.EnumProperty(name="Green Channel",default = "POS_Y", items = normal_axis_enum)
    normal_b : bpy.props.EnumProperty(name="Blue Channel",default = "POS_Z", items = normal_axis_enum)

    # Common properties
    name : bpy.props.StringProperty(name = "Name", default = "Pass")
    type : bpy.props.EnumProperty(name = "Bake Type", default = "COMBINED", items = cyclestype,description="Channel to Bake")

    samples : bpy.props.IntProperty(default = 32,description="Number of Samples, high values gives more quality and more render times")
    enabled : bpy.props.BoolProperty()

    size : bpy.props.EnumProperty(name="Size",default = "1024", items = sizetype,description="The texture size to bake")
    '''
    size_x : bpy.props.IntProperty(default = 512, min = 16,description="The width value, square values are recomended")
    size_y : bpy.props.IntProperty(default = 512, min = 16,description="The height value, square values are recomended")
    '''
    margin : bpy.props.IntProperty(default = 6 ,description="Pixel bledding beyond the islands, values > 0 <  12 are recomended")
    custom_output : bpy.props.StringProperty(description = "Try to find the output node with this name and assign it to bake on this pass")
    aliasing : bpy.props.EnumProperty(name="Aliasing",default = "None", items = aliasing_type,description="Use SuperSampler Aliasing")



class BakeTool_PassGroup(bpy.types.PropertyGroup):
    Pass : bpy.props.CollectionProperty(type=BakeTool_BakePass)
    index : bpy.props.IntProperty()

class BakeTool_JobSettings(bpy.types.PropertyGroup):
    name : bpy.props.StringProperty()
    enabled : bpy.props.BoolProperty(default = True)
    job_objs : bpy.props.PointerProperty(type=BakeTool_ObjGroup)
    job_pass : bpy.props.PointerProperty(type=BakeTool_PassGroup)
    job_settings : bpy.props.PointerProperty(type=BakeTool_Settings)

class BakeTool_Jobs(bpy.types.PropertyGroup):
    Jobs : bpy.props.CollectionProperty(type=BakeTool_JobSettings)
    is_baking : bpy.props.BoolProperty()
    status : bpy.props.StringProperty()
    index : bpy.props.IntProperty()

class BakeTool_ReportData(bpy.types.PropertyGroup):
    processCount : bpy.props.IntProperty()
    processCurrent : bpy.props.IntProperty()
    jobCurrent : bpy.props.IntProperty()
    jobCount : bpy.props.IntProperty()
    objCount : bpy.props.IntProperty()
    objCurrent : bpy.props.IntProperty()
    passCount : bpy.props.IntProperty()
    passCurrent : bpy.props.IntProperty()
    individualUVs : bpy.props.IntProperty()
    atlasUVs: bpy.props.IntProperty()
    current_processPid: bpy.props.IntProperty()

# INTERFCE ------------------------------------------------------------------------------------------------------
class BAKETOOL_UL_Joblist(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row(align = False)
        row.prop(item,"enabled", text = "")
        row.prop(item,"name", text = "", emboss = False, icon = "RENDERLAYERS")


# Pass LIST ----------------------------------
class BAKETOOL_UL_Passlist(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row(align=True)
        row.prop(item,"name", text = "", emboss= False, icon = "RENDERLAYERS")

        Job = bpy.context.scene.BakeTool_Jobs
        ActiveJob = Job.Jobs[Job.index]

        if(ActiveJob.job_settings.profile_type == "BLENDER"):
            row.prop(item,"type",text="")
        else:
            row.prop(item,"type_simple",text="")



# OBJECT LIST ----------------------------------

def AddObjList(context):
    Job = bpy.context.scene.BakeTool_Jobs
    ActiveJob = Job.Jobs[Job.index]

    for actObj in context.selected_objects:
        inList = False
        if actObj.type == "MESH":
            for item in ActiveJob.job_objs.coll:
                if item.name == actObj.name:
                    inList = True
            if not inList:
                item = ActiveJob.job_objs.coll.add()
                item.name = actObj.name
                # Tenta adicionar a UV ativa se houver
                try:
                    item.uv = actObj.data.uv_textures.active.name
                except:
                    pass

def RemoveObjList(context,objname):
    Job = bpy.context.scene.BakeTool_Jobs
    ActiveJob = Job.Jobs[Job.index]
    ObjList = ActiveJob.job_objs
    #for ob in bpy.context.scene.objects:
    for idx,_obj in enumerate(ObjList.coll):
        if objname == _obj.name:
            ObjList.coll.remove(idx)

def RemoveFromScene(context):
    Job = bpy.context.scene.BakeTool_Jobs
    ActiveJob = Job.Jobs[Job.index]

    ObjList = ActiveJob.job_objs
    for obj in bpy.context.selected_objects:
        for idx,_obj in enumerate(ObjList.coll):
            if obj.name == _obj.name:
                ObjList.coll.remove(idx)

def SelectFromScene(context,single):
    Job = bpy.context.scene.BakeTool_Jobs
    ActiveJob = Job.Jobs[Job.index]
    ObjList = ActiveJob.job_objs
    if single:
        for ob in bpy.context.scene.objects:
            if ob.name == ObjList.coll[ObjList.index].name:
                ob.select_set(True)
            else:
                ob.select_set(False)
    else:
        for idx,_obj in enumerate(ObjList.coll):
            for ob in bpy.context.scene.objects:
                if ob.name == _obj.name:
                    ob.select = True

def ActiveToTarget(context):
    Job = bpy.context.scene.BakeTool_Jobs
    ActiveJob = Job.Jobs[Job.index]

    ActiveJob.job_settings.target = context.active_object.name
    try: # Se tiver uma UV utiliza ela
        ActiveJob.job_settings.target_uv = context.active_object.data.uv_textures[context.active_object.data.uv_textures.active_index].name
    except:
        ActiveJob.job_settings.target_uv = ""

class BAKETOOL_UL_ObjList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row(align = True)
        Job = bpy.context.scene.BakeTool_Jobs
        ActiveJob = Job.Jobs[Job.index]
        try:
            a = context.scene.objects[item.name]
            row.label(text = item.name, icon = "OBJECT_DATAMODE")
            #row.prop(item, "name" , text="", icon="OBJECT_DATAMODE")
            if(not ActiveJob.job_settings.generate_uvwrap and ActiveJob.job_settings.target == "" ):
                if(item.uv == ""):
                    row.prop_search(item,"uv", context.scene.objects[item.name].data,"uv_layers", icon = "ERROR", text = "")
                else:
                    row.prop_search(item,"uv", context.scene.objects[item.name].data,"uv_layers", icon = "UV", text = "")

            remove = row.operator(BakeTool_RemoveObj.bl_idname, icon ="X", text = "")
            remove.Obj = item.name
        except:
            row.label(text = "Invalid object")
            remove = row.operator(BakeTool_RemoveObj.bl_idname, icon ="X", text = "")
            remove.Obj = item.name

class BakeTool_AddObj(bpy.types.Operator):
    """ Add the selected objects of the scene"""
    bl_idname = "baketool.add_obj"
    bl_label = "Add Active Object to the List"

    def execute(self, context):
        AddObjList(context)
        return {'FINISHED'}

class BakeTool_RemoveObj(bpy.types.Operator):
    """Remove the selected object of list"""
    bl_idname = "baketool.remove_obj"
    bl_label = "Remove Active Object to the List"
    Obj : bpy.props.StringProperty();

    def execute(self, context):
        RemoveObjList(context,self.Obj)
        return {'FINISHED'}

class BakeTool_RemoveObjFromScene(bpy.types.Operator):
    """Remove the selected objects of the scene"""
    bl_idname = "baketool.remove_selected"
    bl_label = "Remove All Selected Objects From The Scene"

    def execute(self, context):
        RemoveFromScene(context)
        return {'FINISHED'}

class BakeTool_SelectObjFromScene(bpy.types.Operator):
    """Select on the scene the objects of the list"""
    bl_idname = "baketool.selectlist"
    bl_label = "Select From Scene"
    single : bpy.props.BoolProperty();

    def execute(self, context):
        SelectFromScene(context,self.single)
        return {'FINISHED'}

class BakeTool_AddObjToTarget(bpy.types.Operator):
    """Use the active object as the target"""
    bl_idname = "baketool.add_target"
    bl_label = "Active Object to Target"

    def execute(self, context):
        ActiveToTarget(context)
        return {'FINISHED'}

# ------------------------------- UI JOBS --------------------------------------
def DuplicateJob(context,id):
    Job = bpy.context.scene.BakeTool_Jobs
    if Job.index >= len(Job.Jobs):
        return
    ActiveJob = Job.Jobs[Job.index]
    Bake_Pass = bpy.context.scene.BakeTool_Jobs.Jobs.add()
    Bake_Pass.id = random.randint(0, 9999)
    Bake_Pass.name = "Job " + str(len(bpy.context.scene.BakeTool_Jobs.Jobs))
    Bake_Pass.job_settings.mode = ActiveJob.job_settings.mode
    Bake_Pass.job_settings.profile_type = ActiveJob.job_settings.profile_type
    Bake_Pass.job_settings.path = ActiveJob.job_settings.path
    Bake_Pass.job_settings.target = ActiveJob.job_settings.target
    Bake_Pass.job_settings.target_uv = ActiveJob.job_settings.target_uv
    Bake_Pass.job_settings.cage = ActiveJob.job_settings.cage
    Bake_Pass.job_settings.distance = ActiveJob.job_settings.distance
    Bake_Pass.job_settings.bias = ActiveJob.job_settings.bias
    Bake_Pass.job_settings.format = ActiveJob.job_settings.format
    Bake_Pass.job_settings.atlas_autoPack = ActiveJob.job_settings.atlas_autoPack
    Bake_Pass.job_settings.atlas_autoPack_margin = ActiveJob.job_settings.atlas_autoPack_margin
    Bake_Pass.job_settings.atlas_autoPack_area = ActiveJob.job_settings.atlas_autoPack_area
    Bake_Pass.job_settings.generate_uvwrap = ActiveJob.job_settings.generate_uvwrap
    Bake_Pass.job_settings.uvwrapper_margn = ActiveJob.job_settings.uvwrapper_margin
    Bake_Pass.job_settings.uvwrapper_angle = ActiveJob.job_settings.uvwrapper_angle
    Bake_Pass.job_settings.postbake_importImages = ActiveJob.job_settings.postbake_importImages
    Bake_Pass.job_settings.postbake_createEevee = ActiveJob.job_settings.postbake_createEevee
    Bake_Pass.job_settings.postBake_eeveePass = ActiveJob.job_settings.postBake_eeveePass
    Bake_Pass.job_settings.render_device = ActiveJob.job_settings.render_device
    for item in ActiveJob.job_objs.coll:
        new_item = Bake_Pass.job_objs.coll.add()
        new_item.name = item.name
    for active_pass in ActiveJob.job_pass.Pass:
        new_pass = Bake_Pass.job_pass.Pass.add()
        new_pass.id = random.randint(0, 9999)
        new_pass.name = active_pass.name
        new_pass.colors_space = active_pass.colors_space
        new_pass.type_simple = active_pass.type_simple
        new_pass.normal_simple_mode = active_pass.normal_simple_mode
        new_pass.use_pass_diffuse = active_pass.use_pass_diffuse
        new_pass.use_pass_glossy = active_pass.use_pass_glossy
        new_pass.use_pass_transmission = active_pass.use_pass_transmission
        new_pass.use_pass_ambient_occlusion = active_pass.use_pass_ambient_occlusion
        new_pass.use_pass_emit = active_pass.use_pass_emit
        new_pass.use_pass_color = active_pass.use_pass_color
        new_pass.use_pass_direct = active_pass.use_pass_direct
        new_pass.use_pass_indirect = active_pass.use_pass_indirect
        new_pass.normal_space = active_pass.normal_space
        new_pass.normal_space_bi = active_pass.normal_space_bi
        new_pass.normal_r = active_pass.normal_r
        new_pass.normal_g = active_pass.normal_g
        new_pass.normal_b = active_pass.normal_b
        new_pass.type = active_pass.type
        new_pass.samples = active_pass.samples
        new_pass.size = active_pass.size
        new_pass.margin = active_pass.margin
        new_pass.custom_output = active_pass.custom_output
        new_pass.aliasing = active_pass.aliasing
        new_pass.enabled = active_pass.enabled

def AddJob():
    Bake_Pass = bpy.context.scene.BakeTool_Jobs.Jobs.add()
    Bake_Pass.id = random.randint(0, 9999)
    Bake_Pass.name = "Job " + str(len(bpy.context.scene.BakeTool_Jobs.Jobs))

def RemoveJob(context,id):
    bpy.context.scene.BakeTool_Jobs.Jobs.remove(bpy.context.scene.BakeTool_Jobs.index)

class BakeTool_AddJob(bpy.types.Operator):
    """Add a new pass to bake"""
    bl_idname = "baketool.add_job"
    bl_label = "Add Job"

    def execute(self, context):
        AddJob()
        return {'FINISHED'}

class BakeTool_DuplicateJob(bpy.types.Operator):
    """Duplicate selected job"""
    bl_idname = "baketool.duplicate_job"
    bl_label = "Duplicate Job"

    id : bpy.props.IntProperty()

    def execute(self, context):
        DuplicateJob(context,self.id)
        return {'FINISHED'}

class BakeTool_RemoveJob(bpy.types.Operator):
    """Remove this pass of the list"""
    bl_idname = "baketool.remove_job"
    bl_label = "Remove Job"

    id : bpy.props.IntProperty()

    def execute(self, context):
        RemoveJob(context,self.id)
        return {'FINISHED'}

# ------------------------------- UI PASSES --------------------------------------

def AddPass():
    Job = bpy.context.scene.BakeTool_Jobs
    ActiveJob = Job.Jobs[Job.index]
    Bake_Pass = ActiveJob.job_pass.Pass.add()
    Bake_Pass.id = random.randint(0, 9999)
    Bake_Pass.enabled = True
    Bake_Pass.name = "Pass " + str(len(ActiveJob.job_pass.Pass))

def RemovePass(context,id):
    Job = bpy.context.scene.BakeTool_Jobs
    ActiveJob = Job.Jobs[Job.index]
    ActiveJob.job_pass.Pass.remove(ActiveJob.job_pass.index)

def PassPreview():
    Job = bpy.context.scene.BakeTool_Jobs
    activeJob = Job.Jobs[Job.index]
    '''
    if(activeJob.job_settings.profile_type != "BAKETOOL"):
        jobTypeName = activeJob.job_pass.Pass[activeJob.job_pass.index].type
    else:
        jobTypeName = activeJob.job_pass.Pass[activeJob.job_pass.index].type_simple
    '''

    jobName = activeJob.job_pass.Pass[activeJob.job_pass.index].name

    for mat in bpy.data.materials:
        imgNode = None
        if("BAKETOOL_" + activeJob.name in mat.name):
            for node in mat.node_tree.nodes:
                if(node.type == "TEX_IMAGE" and jobName in node.name):
                    imgNode = node
            if(imgNode != None):
                for node in mat.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL":
                        mat.node_tree.links.new(node.inputs[0],imgNode.outputs[0])



class BakeTool_AddPass(bpy.types.Operator):
    """Add a new pass to bake"""
    bl_idname = "baketool.add_pass"
    bl_label = "Add Pass"


    def execute(self, context):
        AddPass()
        return {'FINISHED'}

class BakeTool_RemovePass(bpy.types.Operator):
    """Remove this pass of the list"""
    bl_idname = "baketool.remove_layer"
    bl_label = "Remove Pass"

    id : bpy.props.IntProperty()

    def execute(self, context):
        RemovePass(context,self.id)
        return {'FINISHED'}

class BakeTool_PassPreview(bpy.types.Operator):
    """Pass Preview"""
    bl_idname = "baketool.pass_preview"
    bl_label = "Pass Preview"

    id : bpy.props.IntProperty()

    def execute(self, context):
        PassPreview()
        return {'FINISHED'}

#  -------------------------PAINEL PRINCIPAL ------------------------------

class BAKETOOL_PT_UV(bpy.types.Panel):
    bl_label = "UV Settings"
    bl_idname = "BAKETOOL_PT_UV"
    bl_parent_id = "BAKETOOL_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_context = "render"

    @classmethod
    def poll(cls,context):
        if bpy.context.scene.render.engine == "CYCLES":
            try:
                Job = bpy.context.scene.BakeTool_Jobs
                ActiveJob = Job.Jobs[Job.index]
                return True
            except:
                return False
            return True
        else:
            return False

    def draw(self,context):

        layout = self.layout
        layout.use_property_split = True # Active single-column layout

        Mode = bpy.context.scene.render.engine
        Job = bpy.context.scene.BakeTool_Jobs

        try:
            ActiveJob = Job.Jobs[Job.index]
        except:
            layout.label(text="Select a Job to start")
            return

        layout.prop(ActiveJob.job_settings, "generate_uvwrap", text = "Generate Object UVs:")
        if(ActiveJob.job_settings.generate_uvwrap):
            layout.prop(ActiveJob.job_settings, "uvwrapper_margin", text = "Margin")
            layout.prop(ActiveJob.job_settings, "uvwrapper_angle", text = "Angle")


        if(ActiveJob.job_settings.mode == "ATLAS"):
            if(ActiveJob.job_settings.target == ""):
                layout.separator()
                layout.prop(ActiveJob.job_settings, "atlas_autoPack", text = "Generate Atlas UV")
                if(ActiveJob.job_settings.atlas_autoPack):
                    layout.prop(ActiveJob.job_settings, "atlas_autoPack_margin", text = "Marge")
                    layout.prop(ActiveJob.job_settings, "atlas_autoPack_area", text = "Area Weight")

class BAKETOOL_PT_PostRender(bpy.types.Panel):
    bl_label = "Post Render Settings"
    bl_idname = "BAKETOOL_PT_PostRender"
    bl_parent_id = "BAKETOOL_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_context = "render"

    @classmethod
    def poll(cls,context):
        if bpy.context.scene.render.engine == "CYCLES":
            try:
                Job = bpy.context.scene.BakeTool_Jobs
                ActiveJob = Job.Jobs[Job.index]
                return True
            except:
                return False
            return True
        else:
            return False

    def draw(self,context):
        layout = self.layout
        layout.use_property_split = True # Active single-column layout

        Mode = bpy.context.scene.render.engine
        Job = bpy.context.scene.BakeTool_Jobs

        try:
            ActiveJob = Job.Jobs[Job.index]
        except:
            layout.label(text="Select a Job to start")
            return

        layout.prop(ActiveJob.job_settings, "postbake_importImages", text = "Load Images")
        if ActiveJob.job_settings.mode != "ATLAS":
            layout.prop(ActiveJob.job_settings, "postbake_createEevee", text = "Create Eevee Scene")

class BAKETOOL_PT_PassList(bpy.types.Panel):
    bl_label = "Pass Settings"
    bl_idname = "BAKETOOL_PT_PassList"
    bl_parent_id = "BAKETOOL_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_context = "render"

    @classmethod
    def poll(cls,context):
        if bpy.context.scene.render.engine == "CYCLES":
            try:
                Job = bpy.context.scene.BakeTool_Jobs
                ActiveJob = Job.Jobs[Job.index]
                return True
            except:
                return False
            return True
        else:
            return False

    def draw(self,context):
        # Objects Setttings
        layout = self.layout
        layout.use_property_split = True # Active single-column layout

        Mode = bpy.context.scene.render.engine
        Job = bpy.context.scene.BakeTool_Jobs
        try:
            ActiveJob = Job.Jobs[Job.index]
        except:
            layout.label(text="Select a Job to start")
            return
        # PASS LIST ----------------------------------------------
        col = layout.row(align = True)
        col.template_list("BAKETOOL_UL_Passlist", "", ActiveJob.job_pass, "Pass", ActiveJob.job_pass, "index",rows=2, type = "DEFAULT")
        col = col.column(align = True)
        col.operator(BakeTool_AddPass.bl_idname, text = "",icon = "ADD")
        col.operator(BakeTool_RemovePass.bl_idname, text ="", icon ="REMOVE")
        col.operator(BakeTool_PassPreview.bl_idname, text ="", icon ="SHADING_RENDERED")

        # Existe um passo ativo
        try:
            Pass = ActiveJob.job_pass.Pass[ActiveJob.job_pass.index]
        except:
            return

        layout.separator()
        layout.label(text= "General Settings:", icon ="RENDERLAYERS")
        row = layout.row()

        row = layout.column(align = True)
        row.prop(Pass,"use_denoising",text="Use Denoise")
        row.prop(Pass,"enabled",text="Enabled")
        row.prop(Pass,"size",text="Resolution")
        row.prop(Pass,"aliasing",text="AA")
        row.prop(Pass,"margin",text="Margin")
        row.prop(Pass,"colors_space",text= "Color Space")

        # Blender Mode
        if(ActiveJob.job_settings.profile_type == "BLENDER"):
            row.prop(Pass,"samples", text= "Samples")
            row.prop(Pass,"margin",text="Margin")

            layout.separator()

            row = layout.row(align = False)

            row.prop(Pass,"type", text = "Type")

            # Normal properties
            if(Pass.type == "NORMAL"):
                Row = layout.row()
                Row.prop(Pass,"normal_space")
                Row = layout.row(align = True)
                Row.label(text = "Swizzle:")
                Row.prop(Pass,"normal_r", text="")
                Row.prop(Pass,"normal_g", text="")
                Row.prop(Pass,"normal_b", text="")

            if(Pass.type == "COMBINED"):
                row = layout.column(align = True)
                row.prop(Pass,"use_pass_direct", text="Direct",toggle = True, icon = "OUTLINER_OB_LIGHT")
                row.prop(Pass,"use_pass_indirect", text="Indirect",toggle = True, icon = "OUTLINER_OB_LIGHT")
                Lin = layout.row()
                Row = Lin.column(align = True)
                Row.prop(Pass,"use_pass_diffuse", text="Diffuse",toggle = True, icon = "SHADING_TEXTURE")
                Row.prop(Pass,"use_pass_glossy", text="Glossy",toggle = True, icon = "SHADING_TEXTURE")
                Row.prop(Pass,"use_pass_transmission", text="Transm",toggle = True, icon = "SHADING_TEXTURE")
                Row = Lin.column(align = True)
                #Row.prop(Pass,"use_pass_ambient_occlusion", text="AO",toggle = True, icon = "SHADING_TEXTURE")
                Row.prop(Pass,"use_pass_emit", text="Emit",toggle = True, icon = "SHADING_TEXTURE")

            if(Pass.type == "DIFFUSE" or Pass.type == "GLOSSY" or Pass.type == "TRANSMISSION" or Pass.type == "SUBSURFACE"):
                row = layout.row(align = True)
                row.use_property_split = False
                row.prop(Pass,"use_pass_direct", text="Direct",toggle = True, icon = "LIGHT")
                row.prop(Pass,"use_pass_indirect", text="Indirect",toggle = True, icon = "LIGHT")
                row.prop(Pass,"use_pass_color", text="Color",toggle = True, icon = "LIGHT")

            # Custom Output
            layout.separator()
            layout.label(text= "Other Settings:", icon ="RENDERLAYERS")
            layout.prop(Pass, "custom_output", text = "Custom Output" , icon ="SHADING_TEXTURE" )

        # Baketool profile
        else:
            row = layout.column()
            row.prop(Pass,"type_simple")

            # Normal properties
            if(Pass.type_simple == "NORMAL"):
                Row = layout.column(align = True)
                Row.prop(Pass,"normal_space")
                Row.prop(Pass,"normal_simple_mode")

            if(Pass.type_simple == "SUBSURFACE"):
                Row = layout.column(align = True)
                Row.prop(Pass,"normal_space")
                Row.prop(Pass,"normal_simple_mode")

            if(Pass.type_simple == "AO" or Pass.type_simple == "SHADOWS" ):
                row = layout.row()
                row.prop(Pass,"samples", text= "Samples")

class BAKETOOL_PT_ObjList(bpy.types.Panel):
    bl_label = "Object Settings"
    bl_idname = "BAKETOOL_PT_ObjList"
    bl_parent_id = "BAKETOOL_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_context = "render"

    @classmethod
    def poll(cls,context):
        if bpy.context.scene.render.engine == "CYCLES":
            try:
                Job = bpy.context.scene.BakeTool_Jobs
                ActiveJob = Job.Jobs[Job.index]
                return True
            except:
                return False
            return True
        else:
            return False

    def draw(self,context):
        # Objects Setttings
        layout = self.layout
        layout.use_property_split = True # Active single-column layout

        Mode = bpy.context.scene.render.engine
        Job = bpy.context.scene.BakeTool_Jobs

        try:
            ActiveJob = Job.Jobs[Job.index]
        except:
            layout.label(text="Required at least one Job")
            return
        ActiveJob.job_settings.mode == "ATLAS"

        col = layout.row(align = True)
        col.template_list("BAKETOOL_UL_ObjList", "", ActiveJob.job_objs, "coll", ActiveJob.job_objs, "index",rows=3, type = "DEFAULT")
        col = col.column(align = True)
        col.operator(BakeTool_AddObj.bl_idname, icon ="EYEDROPPER", text = "")
        col.operator(BakeTool_RemoveObjFromScene.bl_idname, icon ="CANCEL", text = "")
        single = col.operator(BakeTool_SelectObjFromScene.bl_idname, icon ="VIEWZOOM", text = "")
        single.single = True
        multiple = col.operator(BakeTool_SelectObjFromScene.bl_idname, icon ="BORDERMOVE", text = "")
        multiple.single = False

        # OVERWRITE UV

        try:
            Obj = ActiveJob.job_objs.coll[ActiveJob.job_objs.index]
            if(ActiveJob.job_settings.generate_uvwrap and Obj and ActiveJob.job_settings.target == "" ):
                layout.prop_search(Obj,"overwriteUV", context.scene.objects[Obj.name].data,"uv_layers", icon = "UV", text = "Overwrite UV")

        except:
            return

        # TARGET MANAGER ------------------------------------------------
        if ActiveJob.job_settings.mode == "ATLAS":
            layout.label(text = "Bake To Target:", icon = "OBJECT_DATAMODE")
            layout.prop_search(ActiveJob.job_settings, "target",  bpy.context.view_layer, "objects", text="Target:")
            #row.operator(BakeTool_AddObjToTarget.bl_idname, text = "",icon = "EYEDROPPER")

            if ActiveJob.job_settings.target != "":

                if bpy.context.view_layer.objects[ActiveJob.job_settings.target.lstrip()].type == "MESH":
                    if(not ActiveJob.job_settings.generate_uvwrap):
                        layout.prop_search(ActiveJob.job_settings, "target_uv", context.scene.objects[ActiveJob.job_settings.target.lstrip()].data,"uv_layers", icon="SHADING_TEXTURE", text="UV")
                    layout.prop_search(ActiveJob.job_settings, "cage",  context.scene, "objects", text="Cage")
                    distance_text = "Distance"
                    if ActiveJob.job_settings.cage != "":
                        if context.scene.objects[ActiveJob.job_settings.cage].type != "MESH":
                            layout.label("WARNING: Select a Mesh Object as a Cage")
                        else:
                            distance_text = "Cage Extrusion"

                    layout.prop(ActiveJob.job_settings,"distance", text=distance_text)
                    layout.prop(ActiveJob.job_settings,"bias", text="Bias")

                else:
                    layout.label(text= "WARNING: Select a Mesh Object")

class BAKETOOL_PT_Panel(bpy.types.Panel):
    """Main panel with bake properties for Bake Tool"""
    bl_label = "BakeTool 2.5.1"
    bl_idname = "BAKETOOL_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BakeTool"

    def draw(self,context):
        if bpy.context.scene.render.engine != "CYCLES":
            layout = self.layout
            layout.label(text="Select CYCLES RENDER",icon="ERROR")
            return

        layout = self.layout

        layout = self.layout
        layout.use_property_split = True # Active single-column layout

        Mode = bpy.context.scene.render.engine
        Job = bpy.context.scene.BakeTool_Jobs

        row = layout.row()
        row.scale_y = 2
        row.operator(BakeTool_CyclesBake.bl_idname, icon= "RENDER_STILL", text = "BAKE")
        layout.separator()
        layout.label(text = "Jobs Settings:", icon = "WINDOW")
        col = layout.row(align = True)
        col.template_list("BAKETOOL_UL_Joblist", "", Job, "Jobs", Job, "index",rows=2, type = "DEFAULT")
        col = col.column(align = True)
        col.operator(BakeTool_AddJob.bl_idname, text = "",icon = "ADD")
        col.operator(BakeTool_RemoveJob.bl_idname, text ="", icon ="REMOVE")
        col.operator(BakeTool_DuplicateJob.bl_idname, text ="", icon ="DUPLICATE")

        # Job houver um job ativo
        try:
            ActiveJob = Job.Jobs[Job.index]
        except:
            return

        # Job Settings
        layout.separator()


        #layout.prop(ActiveJob.job_settings, "keep", text = "Keep Textures in Blender")

        layout.label(text = "Bake Settings:", icon = "TEXTURE")
        layout.prop(ActiveJob.job_settings, "mode", text = "Bake Mode:",expand=True)
        layout.prop(ActiveJob.job_settings,"profile_type", text="Profile Setup",toggle = True, icon = "LIGHT",expand=True)

        layout.prop(ActiveJob.job_settings, "path", text = "Save Path")

        if ActiveJob.job_settings.path != "":
            layout.prop(ActiveJob.job_settings,"format")

        userpref = bpy.context.preferences
        if(not userpref.addons['cycles'].preferences.compute_device_type == "NONE"):
            row = layout.row()
            row.prop(ActiveJob.job_settings, "render_device", text="Render Device")

class BakeTool_MT_Menu(bpy.types.Menu):
    bl_label = "BakeTool Operators"
    bl_idname = "OBJECT_MT_BakeTool_MT_Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("baketool.make_atlas")

def VIEW3D_BakeTool_MT_Menu(self, context):
    self.layout.menu(BakeTool_MT_Menu.bl_idname)

classes = (
    BakeTool_ObjEntry,
    BakeTool_ObjGroup,
    BakeTool_BakePass,
    BakeTool_PassGroup,
    BakeTool_MaterialSettings,
    BakeTool_Settings,
    BakeTool_JobSettings,
    BakeTool_Jobs,
    BakeTool_ReportData,

    BAKETOOL_UL_ObjList,
    BAKETOOL_UL_Passlist,
    BAKETOOL_UL_Joblist,

    BakeTool_AddObj,
    BakeTool_RemoveObj,
    BakeTool_RemoveObjFromScene,
    BakeTool_AddObjToTarget,
    BakeTool_AddPass,
    BakeTool_RemovePass,
    BakeTool_PassPreview,
    BakeTool_AddJob,
    BakeTool_RemoveJob,
    BakeTool_DuplicateJob,
    BakeTool_SelectObjFromScene,
    BakeTool_CyclesBake,

    BakeTool_MT_Menu,
    BAKETOOL_PT_Panel,
    BAKETOOL_PT_UV,
    BAKETOOL_PT_ObjList,
    BAKETOOL_PT_PassList,
    BAKETOOL_PT_PostRender,

    BakeTool_MakeAtlas,
    bt_cyclesbake.BakeIndividual,
    bt_cyclesbake.BakeAtlas,
    bt_reports.BakeToolReports,
    #bt_error_reports.BakeToolErrorReports
)

@bpy.app.handlers.persistent
def loadPost(scene):
    bpy.context.scene.BakeTool_Jobs.is_baking = False

def register():

    from bpy.utils import register_class
    for c in classes:
        register_class(c)

    bpy.types.Scene.BakeTool_Objects = bpy.props.PointerProperty(type=BakeTool_ObjGroup)
    bpy.types.Material.BakeTool_MaterialSettings = bpy.props.PointerProperty(type=BakeTool_MaterialSettings)
    bpy.types.Scene.BakeTool_Settings = bpy.props.PointerProperty(type=BakeTool_Settings)
    bpy.types.Scene.BakeTool_Jobs = bpy.props.PointerProperty(type=BakeTool_Jobs)
    bpy.types.Scene.BakeTool_ReportData = bpy.props.PointerProperty(type=BakeTool_ReportData)

    bpy.app.handlers.load_post.append(loadPost)
    bpy.types.VIEW3D_MT_object.append(VIEW3D_BakeTool_MT_Menu)

def unregister():

    bpy.types.VIEW3D_MT_object.remove(VIEW3D_BakeTool_MT_Menu)

    from bpy.utils import unregister_class
    for c in classes:
        unregister_class(c)

    bpy.app.handlers.load_post.remove(loadPost)
