# Copyright (C) Cogumelo Softworks
# License: http://www.gnu.org/licenses/gpl.html GPL version 3 or higher

import bpy
import blf
import bgl
import imbuf
import os, sys
import json
import io
import time
import subprocess
from bpy_extras.node_shader_utils import PrincipledBSDFWrapper


from . bt_autopack import *

# Helper para propriedades do objeto na lista
class TargetGroup():
    name = ""
    uv = ""
    def __init__(self,_name,_uv):
        self.name = _name
        self.uv = _uv

def duplicateObject(scene, name, copyobj):
    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Create new object associated with the mesh
    ob_new = bpy.data.objects.new(name, mesh)

    # Copy data block from the old object into the new object
    ob_new.data = copyobj.data.copy()
    #ob_new.scale = copyobj.scale
    #ob_new.location = copyobj.location
    ob_new.matrix_world = copyobj.matrix_world

    # Link new object to the given scene and select it
    scene.collection.objects.link(ob_new)
    ob_new.select_set(True)

    return ob_new

def CheckVisible(ListObj):

    #Verifica visibilidade do Objeto na cena e se o objeto está em um layer ativo
    for item in ListObj:
        for obj in bpy.context.scene.objects:
            if bpy.context.scene.objects[item.name] not in bpy.context.visible_objects:
                return (False,obj)
    return (True,None)


def CheckRenderVisible(ListObj):
    for item in ListObj:
        obj = bpy.context.scene.objects[item.name]
        renderVis = IsObjRenderVisible(obj)
        if not IsObjRenderVisible(obj):
            return (False,obj)
    return (True,None)


def is_collection_render_visible(collection):
    """Recursively check if a collection and its parent collections are visible in the render."""
    # If this collection is hidden in render, return False
    if collection.hide_render:
        return False

    # Traverse parent collections in the scene hierarchy
    for parent_collection in bpy.data.collections:
        if collection.name in [child.name for child in parent_collection.children]:
            # Check the parent collection's visibility
            return is_collection_render_visible(parent_collection)
    
    return True  # No parent is hidden, so the collection is visible


def IsObjRenderVisible(obj):
    """Check if an object and its collections are visible in the render."""
    # Check the object's render visibility
    if obj.hide_render:
        return False

    # Check all collections the object belongs to
    for collection in obj.users_collection:
        if not is_collection_render_visible(collection):
            return False

    return True

#-----------------------------------------------------
def CheckEmptyMaterialSlots(ListObj):
    for item in ListObj:
        obj = bpy.context.scene.objects[item.name]
        for i in range(len(obj.data.materials)):
            if obj.data.materials[i] == None:
                return (False,obj)
    return (True,None)


def CheckForNoMaterial(ListObj):
    for item in ListObj:
        obj = bpy.context.scene.objects[item.name]
        if len(obj.data.materials) == 0:
            return (False,obj)
    return (True,None)


def GetObjectListJob(activeJob,settings,isAtlas):

    listObjects = []
    if settings.target != "" and isAtlas == True:
        # A lista é preenchida com os dados do Target
        target = bpy.context.scene.objects[settings.target]
        targetProps = TargetGroup(settings.target,settings.target_uv)
        listObjects.append((target,targetProps))
    else:

        for obj_name in activeJob.job_objs.coll:
            for obj in bpy.context.scene.objects:
                if obj_name.name == obj.name:
                    listObjects.append((obj,obj_name))
    return listObjects

def GetActivePasses(activeJob):
    passList = []
    for job in activeJob.job_pass.Pass:
        if job.enabled:
            passList.append(job)
    return passList

def FixUVNodes(mat,objData):

    for f in objData[0].data.uv_layers:
        if(f.active_render):
            baseUV = f.name

    node_tree = mat.node_tree
    for node in node_tree.nodes:
        if node.type == "TEX_IMAGE":
            imageUVInput = node.inputs[0]
            if len(node.inputs[0].links) == 0:
                uv_node = node_tree.nodes.new('ShaderNodeUVMap')
                uv_node.uv_map = baseUV
                uvNodeOutput = uv_node.outputs[0]
                node_tree.links.new(imageUVInput,uvNodeOutput)
                print("-------- FIXED UV ----------")

def CreateImageNode(mat,tempImage):
    # Cria Image Nodes
    image_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    image_node.location = (100,100)
    image_node.image = tempImage
    image_node.select = True
    image_node.update()

    # Torna Imagem Ativa
    mat.node_tree.nodes.active = image_node

def SetTextureOvenUV(objData):
    active_uv = None
    for f in objData[0].data.uv_layers:
        if(f.name == objData[1].uv):
            f.active = True
            f.active_render = True
            f.active_clone = True
            data = f.data
            active_uv = f

    objData[0].data.update()

def CreateImageAtlas(activeJob,currentObject,jobPass):
    # Cria nova imagem com o nome do Objeto + Passo se não houver
    hasit = False
    tempImage = None
    for image in bpy.data.images:
        if image.name == activeJob.name + "_" + jobPass.name:
            hasit = True
            tempImage = image
    y_size = x_size = int(jobPass.size)
    if not jobPass.square_render:
        y_size = jobPass.y_size
    if not hasit:
        tempImage = bpy.data.images.new(name = activeJob.name + "_" + jobPass.name, width = x_size, height = y_size,alpha=True,float_buffer=True)

    tempImage.source = "GENERATED"
    tempImage.use_generated_float = True;
    tempImage.generated_width = x_size
    tempImage.generated_height = y_size

    return tempImage


def CreateImage(activeJob,currentObject,jobPass,isAtlas):
    # Cria nova imagem com o nome do Objeto + Passo se não houver
    hasit = False
    tempImage = None

    print("---------------------------- ALIASING")
    print(jobPass.aliasing)

    y_size = x_size = int(jobPass.size)
    if not jobPass.square_render:
        y_size = int(jobPass.y_size)

    if(jobPass.aliasing == "2x"):
        x_size *= 2
        y_size *= 2

    if(jobPass.aliasing == "4x"):
        x_size *= 4
        y_size *= 4

    if(isAtlas):
        name = activeJob.name + "_" + jobPass.name
    else:
        name = activeJob.name + "_" + currentObject.name + "_" + jobPass.name

    for image in bpy.data.images:
        if image.name == name :
            hasit = True
            tempImage = image

    if not hasit:
        if isAtlas:
            tempImage = bpy.data.images.new(name = name, width = x_size, height= y_size, alpha=True, float_buffer=True)
        else:
            tempImage = bpy.data.images.new(name = name, width = x_size, height= y_size, alpha=True, float_buffer=True)

    tempImage.source = "GENERATED"

    tempImage.use_generated_float = True;
    tempImage.generated_width = int(x_size)
    tempImage.generated_height = int(y_size)

    # Configure ColorSpace
    tempImage.colorspace_settings.name = jobPass.colors_space

    return tempImage

def SaveImage(activeJob,currentObject,jobPass,tempImage,isAtlas):
    settings = activeJob.job_settings

    if(isAtlas):
        name = activeJob.name + "_" + jobPass.name
    else:
        name = activeJob.name + "_" + currentObject.name + "_" + jobPass.name

    if settings.path != "":
        cacheType = bpy.context.scene.render.image_settings.file_format
        cacheColorMode = bpy.context.scene.render.image_settings.color_mode
        cacheColorDept = bpy.context.scene.render.image_settings.color_depth
        cacheCompression = bpy.context.scene.render.image_settings.compression
        cacheQuality = bpy.context.scene.render.image_settings.quality

        bpy.context.scene.render.image_settings.file_format = settings.format

        try:
            bpy.context.scene.render.image_settings.color_mode = "RGBA"
        except:
            bpy.context.scene.render.image_settings.color_mode = "RGB"

        try:
            bpy.context.scene.render.image_settings.color_depth = "32"
        except:
            try:
                bpy.context.scene.render.image_settings.color_depth = "16"
            except:
                bpy.context.scene.render.image_settings.color_depth = "8"

        path_format = ""
        if settings.format == "JPEG":
            path_format = ".jpeg"
        if settings.format == "PNG":
            path_format = ".png"
        if settings.format == "TIFF":
            path_format = ".tiff"
        if settings.format == "OPEN_EXR":
            path_format = ".exr"
        if settings.format == "TARGA":
            path_format = ".tga"

        bpy.context.scene.render.image_settings.compression = 100
        bpy.context.scene.render.image_settings.quality = 100

        path = bpy.path.abspath(settings.path) + name + path_format
        tempImage.save_render(path)

        y_size = x_size = int(jobPass.size)
        if not jobPass.square_render:
            y_size = int(jobPass.y_size)

        #Apply AA
        if(jobPass.aliasing != "None"):
            img = bpy.data.images.load(path)
            img.scale(x_size, y_size)
            img.filepath_raw = path
            img.file_format = 'PNG'  # або інший формат, якщо потрібно
            img.save()
        return path


def CheckBake(context,jobList):

    # Verifica se o arquivo está salvo
    if not bpy.data.is_saved:
        status = 'TEXTUREOVEN ABORTED: Save the File before bake'
        return status

    for activeJob in jobList:
        if not activeJob.enabled:
            continue

        if activeJob.job_settings.mode == "ATLAS":
            if activeJob.job_settings.target == "":
                status = 'ABORTED: on the job: "' + activeJob.name + '". No target object assigned'
                return status
            if not activeJob.job_settings.target in bpy.data.objects.keys():
                status = 'ABORTED: on the job: "' + activeJob.name + '". Target object does not exist'
                return status
            target_obj = bpy.context.scene.objects[activeJob.job_settings.target]
            if target_obj not in bpy.context.visible_objects:
                status = 'ABORTED: on the job: "' + activeJob.name + '". Target object is not visible'
                return status
            if not IsObjRenderVisible(target_obj):
                status = 'ABORTED: on the job: "' + activeJob.name + '". Target object is not visible in render'
                return status


        objectList = activeJob.job_objs.coll

        if(len(objectList) == 0):
            status = 'ABORTED: on the job: "' + activeJob.name + '" - No valid object to bake in Bake List'
            return status

        # Verifica se existe um path válido para salvar as imagens
        if(not os.path.exists(bpy.path.abspath(activeJob.job_settings.path))):
            status = 'ABORTED: on the job: "' + activeJob.name + '". save path do not exist'
            return status

        # Verifica se existem  objetos na lista e se todos os objetos da lista estão visíveis
        checkstatus, objError = CheckVisible(objectList)
        if(checkstatus == False):
            status = 'ABORTED: on the job: "' + activeJob.name + '". Object "' + objError.name + '" is not visible in the scene'
            return status

        checkRenderVisStatus, objRenderVisError = CheckRenderVisible(objectList)
        if(checkRenderVisStatus == False):
            status = 'ABORTED: on the job: "' + activeJob.name + '". Object "' + objRenderVisError.name + '" is not visible in render'
            return status

        checkNoMaterialsStatus, noMatError = CheckForNoMaterial(objectList)
        if(checkNoMaterialsStatus == False):
            status = 'ABORTED: on the job: "' + activeJob.name + '". Object "' + noMatError.name + '" has no materials'
            return status
        
        checkMatSlotStatus, objMatSlotError = CheckEmptyMaterialSlots(objectList)
        if(checkMatSlotStatus == False):
            status = 'ABORTED: on the job: "' + activeJob.name + '". Object "' + objMatSlotError.name + '" has an empty metarial slot'
            return status
        
        #Seta Objeto Ativo para Objetct Mode se não estiver
        try:
            bpy.ops.object.mode_set(mode="OBJECT")
        except:
            pass

        listObjects = []
        settings = activeJob.job_settings

        ErrorMessage = ""
        # Verifica se irá fazer Atlas e se irá utilizar Target
        if settings.mode == "ATLAS" and settings.target != "":
            '''
            target = context.scene.objects[settings.target]
            if not target.is_visible(context.scene):
                status = 'TEXTUREOVEN ABORTED: "' + activeJob.name + '" - Active Target object is not visible'
                return status
            '''

            for obj_name in activeJob.job_objs.coll:
                if obj_name.name == settings.target:
                    status = 'TEXTUREOVEN ABORTED: "' + activeJob.name + '" - Target object is in the source list, change it'
                    return status

            # A lista é preenchida com os dados do Target
            target = context.scene.objects[settings.target]
            targetProps = TargetGroup(settings.target,settings.target_uv)
            listObjects.append((target,targetProps))

        else:
            # Cria lista com os objetos baseado em seus nomes e propriedades
            for obj_name in activeJob.job_objs.coll:
                for obj in context.scene.objects:
                    if obj_name.name == obj.name:
                        listObjects.append((obj,obj_name))

        # Verifica se os objetos da Lista possuem material do Cycles:
        for obj in listObjects:
            if len(obj[0].material_slots) == 0:
                status = 'TEXTUREOVEN ABORTED: "' + activeJob.name + '" - One or more objects in the List to Bake do not have a valid material: ' + obj[0].name
                return status
            for mat in obj[0].material_slots:
                if mat.material == None:
                    status = 'TEXTUREOVEN ABORTED: "' + activeJob.name + '" - One or more objects in the List to Bake do not have a valid material: ' + obj[0].name
                    return status
                else:
                    valid = False
                    if mat.material.use_nodes == True:
                        for node in mat.material.node_tree.nodes:
                            if node.bl_idname == "ShaderNodeOutputMaterial":
                                valid = True
                        if not valid:
                            status = 'TEXTUREOVEN ABORTED: "' + activeJob.name + '" - One or more objects in the List to Bake do not have a valid node material'
                            return status
                    else:
                        status = 'TEXTUREOVEN ABORTED: "' + activeJob.name + '" - One or more objects in the List to Bake don not have a valid cycles node material'
                        return status

        # Verifica se os objetos da Lista possuem UV ativa se não estiver gerando UVs:
        if( not activeJob.job_settings.generate_uvwrap):
            for obj in listObjects:
                if(obj[1].uv == ""):
                    status = 'TEXTUREOVEN ABORTED: "' + activeJob.name + '" - Object in the List to Bake do not have a valid uv set'
                    return status

        # Verifica se existe ao menos 1 passo habilitado
        hasPass = False
        for job in activeJob.job_pass.Pass[:]:
            if job.enabled:
                hasPass = True
        if not hasPass:
            status = 'TEXTUREOVEN ABORTED: "' + activeJob.name + '" You need at least one enabled pass to Bake'
            return status

    print ("--------------------- STATUS CHECK -----------------")

    return True


def MakeUVs(context,jobList):
    # UV Unwrapper Systemm

    for activeJob in jobList:
        # Abre a UV de cada objeto de cada Job que precisa
        #listObjects = []
        if(activeJob.job_settings.generate_uvwrap):
            if(activeJob.job_settings.target == ""):
                for obj in activeJob.job_objs.coll:
                    if(obj.overwriteUV != ""):
                        obj.uv = obj.overwriteUV
                    else:
                        obj.uv = DoUnwrapper(  obj.name,
                                                    context,
                                                    activeJob.job_settings.uvwrapper_margin,
                                                    activeJob.job_settings.uvwrapper_angle,
                                                    activeJob.name)
            else:
                activeJob.job_settings.target_uv = DoUnwrapper(   activeJob.job_settings.target,
                                        context,
                                        activeJob.job_settings.uvwrapper_margin,
                                        activeJob.job_settings.uvwrapper_angle,
                                        activeJob.name)

        # Aplica Pack em cada job que precisa
        if activeJob.job_settings.mode == "ATLAS" and activeJob.job_settings.target == "" and activeJob.job_settings.atlas_autoPack:
            DoAtlas(context,activeJob)

def SaveBakeReport(reports):
    script_file = os.path.realpath(__file__)
    directory = os.path.dirname(script_file)

    with open(directory + "/report.json", 'w') as file:
        json.dump(reports, file, indent=2)

def LoadBakeReports():
    script_file = os.path.realpath(__file__)
    directory = os.path.dirname(script_file)
    try:
        reports = json.loads(open(directory + "/report.json").read())
    except:
        ("Can't Load Report Trying again")
        time.sleep(1)   # Delays for 5 seconds. You can also use a float value.
        reports = json.loads(open(directory + "/report.json").read())
    return reports

def SetCustomMaterial(obj,mat,jobPass,settings):
    print("--------------- SET CUSTOM MATERIAL ------------------------")
    node_tree = mat.node_tree

    if(jobPass.custom_output != ""): # Custom Output
        print(jobPass.name + " Using Custom Output")
        originalOut = GetOutputByName(node_tree.nodes,jobPass.custom_output)
        if(originalOut != None):
            SetActiveNode(node_tree,originalOut)
            print(originalOut.name)
        else:
            originalOut = GetActiveNode(node_tree.nodes)
    else:
        originalOut = GetActiveNode(node_tree.nodes)
    bprincipled = originalOut.inputs[0].links[0].from_node
    
    nodeOut = node_tree.nodes.new('ShaderNodeOutputMaterial')

    if(settings.profile_type != "BLENDER"):
        if(jobPass.type_simple == "ALBEDO"):
            try:
                principled = originalOut.inputs[0].links[0].from_node
                if(principled.type == "BSDF_PRINCIPLED"):
                    if(principled.inputs["Metallic"].is_linked):         #Metallic
                        link = principled.inputs["Metallic"].links[0]    #Metallic
                        node_tree.links.new(link.from_socket, principled.inputs["Anisotropic"])
                        node_tree.links.remove(link)
                    if (principled.inputs["Metallic"].default_value > 0.0):   #Metallic
                        principled.inputs["Anisotropic"].default_value = principled.inputs["Metallic"].default_value 
                    principled.inputs["Metallic"].default_value = 0.0
            except:
                pass
        if(jobPass.type_simple == "SPECULAR"):
            try:
                # Get current Principled
                principled = originalOut.inputs[0].links[0].from_node
                if(principled.type == "BSDF_PRINCIPLED"):
                    # Get specular value or texture and connect to the new output
                    if(principled.inputs["Specular Tint"].is_linked):
                        texture = principled.inputs["Specular Tint"].links[0].from_socket
                        mat.node_tree.links.new(texture, nodeOut.inputs[0])
                    else:
                        nodeValue = node_tree.nodes.new('ShaderNodeValue')
                        nodeValue.outputs[0].default_value = principled.inputs["Specular Tint"].default_value
                        mat.node_tree.links.new(nodeValue.outputs[0], nodeOut.inputs[0])
                    SetActiveNode(node_tree,nodeOut)
            except:
                pass
        if(jobPass.type_simple == "ALPHA"):
            try:
                # Get current Principled
                principled = originalOut.inputs[0].links[0].from_node
                if(principled.type == "BSDF_PRINCIPLED"):
                    # Get specular value or texture and connect to the new output
                    if(principled.inputs["Alpha"].is_linked):
                        texture = principled.inputs["Alpha"].links[0].from_socket
                        mat.node_tree.links.new(texture, nodeOut.inputs[0])
                    else:
                        nodeValue = node_tree.nodes.new('ShaderNodeValue')
                        nodeValue.outputs[0].default_value = principled.inputs["Alpha"].default_value
                        mat.node_tree.links.new(nodeValue.outputs[0], nodeOut.inputs[0])
                    SetActiveNode(node_tree,nodeOut)
            except:
                pass
        if(jobPass.type_simple == "METALLIC"):
            
            print("METALLIC__________________")
            try:
                # Get current Principled
                principled = originalOut.inputs[0].links[0].from_node
                if(principled.type == "BSDF_PRINCIPLED"):
                    # If there was an attempt to correct the effect of metallic on the albedo
                    # Reverse the action and 

                    # Connect input from Anisotropic back to the Metallic 
                    if (principled.inputs["Anisotropic"].is_linked):
                        link = principled.inputs["Anisotropic"].links[0]    #Metallic
                        node_tree.links.new(link.from_socket, principled.inputs["Metallic"])

                    # Set the value from input Anisotropic back to the Metallic input
                    elif (principled.inputs["Anisotropic"].default_value > 0.0):
                        principled.inputs["Metallic"].default_value = principled.inputs["Anisotropic"].default_value

                
                
                    # Get metallic value or texture and connect to the new output
                    if (principled.inputs["Metallic"].is_linked):
                        texture = principled.inputs["Metallic"].links[0].from_socket
                        mat.node_tree.links.new(texture, nodeOut.inputs[0])
                    else:
                        nodeValue = node_tree.nodes.new('ShaderNodeValue')
                        nodeValue.outputs[0].default_value = principled.inputs["Metallic"].default_value
                        mat.node_tree.links.new(nodeValue.outputs[0], nodeOut.inputs[0])
                    SetActiveNode(node_tree,nodeOut)
                    
            except:
                pass

        if(jobPass.type_simple == "ID"):
            try:
                script_file = os.path.realpath(__file__)
                directory = os.path.dirname(script_file)
                filepath = directory + "/ressources/mat.blend"

                with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
                    data_to.node_groups = data_from.node_groups

                group = node_tree.nodes.new("ShaderNodeGroup")
                group.node_tree = bpy.data.node_groups['TO_ID']
                mat.node_tree.links.new(group.outputs[0], nodeOut.inputs[0])
                SetActiveNode(node_tree,nodeOut)
            except:
                pass

    return originalOut

"""
def RestoreMaterials(List):
    print("----------------- RESTORE ORIGINAL MATERIALS ------------------")
    for idx in range(len(List)):
        obj = List[idx][0]
        mat = List[idx][1]
        obj.material_slots[idx].material = mat
"""

def RestoreCustomOutput(List):
    for element in List:
        print("------------- RESTORE ORIGINAL OUTPUTS -----------")
        print(element[0])
        print(element[1])
        node_tree = element[0]
        output = element[1]

        for node in node_tree.nodes:
            if node.type == "OUTPUT_MATERIAL":
                node.is_active_output = False
        output.is_active_output = True


def SetActiveNode(node_tree,output):

    for node in node_tree.nodes:
        if node.type == "OUTPUT_MATERIAL":
            node.is_active_output = False

    for node in node_tree.nodes:
        if node.type == "OUTPUT_MATERIAL":
            if(node == output):
                node.is_active_output = True


def GetActiveNode(nodes):
        for node in nodes :
            if node.type == 'OUTPUT_MATERIAL' and node.is_active_output :
                    return node
        for node in nodes :
            if node.type == 'OUTPUT_MATERIAL' :
                    return node

def GetOutputByName(nodes,name):
    for node in nodes:
        if node.type == "OUTPUT_MATERIAL" and node.name == name:
            print("FOUND NODE: " + node.name)
            return node

def SetRenderSettings(jobPass,jobSettings):

    bpy.context.scene.cycles.samples = jobPass.samples

    # Configura o Device
    bpy.context.scene.cycles.device = jobSettings.render_device
    # Seta o Denoise
    bpy.context.scene.cycles.use_denoising = jobPass.use_denoising

    # Configura o Render Pass
    bpy.context.scene.render.bake.use_pass_diffuse = jobPass.use_pass_diffuse
    bpy.context.scene.render.bake.use_pass_glossy = jobPass.use_pass_glossy
    bpy.context.scene.render.bake.use_pass_transmission = jobPass.use_pass_transmission
    #bpy.context.scene.render.bake.use_pass_ambient_occlusion = jobPass.use_pass_ambient_occlusion
    bpy.context.scene.render.bake.use_pass_emit = jobPass.use_pass_emit

    # Cycles sub passes properties
    bpy.context.scene.render.bake.use_pass_color = jobPass.use_pass_color
    bpy.context.scene.render.bake.use_pass_direct = jobPass.use_pass_direct
    bpy.context.scene.render.bake.use_pass_indirect = jobPass.use_pass_indirect

def CreateIndividualEveeScene(activeJob):
    print("-------- CREATE EVEE SCENE ----------------")
    listObj = GetObjectListJob(activeJob,activeJob.job_settings,False)

    bpy.ops.object.select_all(action="DESELECT")

    # Remove Collection
    tempCollection = False
    for col in bpy.context.scene.collection.children:
        if(col.name == "TEXTUREOVEN_" + activeJob.name):
            for obj in col.objects:
                bpy.data.objects.remove(obj)
            bpy.data.collections.remove(col)

    # Create collection
    tempCollection = bpy.data.collections.new("TEXTUREOVEN_" + activeJob.name)
    bpy.context.scene.collection.children.link(tempCollection)

    # Atlas mode
    if(activeJob.job_settings.mode == "ATLAS"):
        pass

    # Create Objects
    for obj in listObj:
        # Duplicate Object
        #obj[0].select_set(True)
        obj = obj[0]
        newObj = obj.copy() # duplicate linked
        newObj.data = obj.data.copy() # optional: make this a real duplicate (not linked)
        newObj.name = "BK_" + obj.name

        newObj.data.uv_layers.active = obj.data.uv_layers.active

        for f in newObj.data.uv_layers:
            if("TEXTUREOVEN_" + activeJob.job_settings.name in f.name):
                f.active = True
                f.active_render = True
                f.active_clone = True

        # Assing objects to collection
        tempCollection.objects.link(newObj)

        newObj.data.materials.clear()

        # Cria Material
        mat = bpy.data.materials.get("TEXTUREOVEN_" + activeJob.name + "_"  + obj.name)
        if(mat is None):
            mat = bpy.data.materials.new(name="TEXTUREOVEN_" + activeJob.name + "_" + obj.name)
        newObj.data.materials.append(mat)

        # Configure Material
        mat.use_nodes = True

        for p in range(len(activeJob.job_pass.Pass)):
            '''
            if(activeJob.job_settings.profile_type != "TEXTUREOVEN"):
                jobTypeName = activeJob.job_pass.Pass[p].type
            else:
                jobTypeName = activeJob.job_pass.Pass[p].type_simple
            '''

            jobName = activeJob.job_pass.Pass[p].name

            # Check if Has Image node and Create if Not
            imgNode = None
            for node in mat.node_tree.nodes:
                if(node.type == "TEX_IMAGE" and node.name == "TEXTUREOVEN_" + jobName + "_" + obj.name):
                    imgNode = node

            if(imgNode == None):
                # Create image Node
                imgNode = mat.node_tree.nodes.new('ShaderNodeTexImage')
                imgNode.name = "TEXTUREOVEN_" + jobName + "_" + obj.name

                img = bpy.data.images[activeJob.name + "_" + obj.name + "_" + jobName]
                imgNode.image = img
                print(img)

            # Get Output
            for node in mat.node_tree.nodes:
                if node.type == "OUTPUT_MATERIAL":
                    mat.node_tree.links.new(node.inputs[0],imgNode.outputs[0])

            # REMOVE Principled
            for node in mat.node_tree.nodes:
                if node.type == "BSDF_PRINCIPLED":
                    mat.node_tree.nodes.remove(node)
                    #mat.node_tree.links.new(node.inputs[0],imgNode.outputs[0])


def SetupTextureOvenPass(jobPass,jobSettings):
    RemoveColorManagement()

    # BLENDER PROFILES
    if(jobSettings.profile_type == "BLENDER"):
        if(jobPass.type == "NORMAL"):
            return" NORMAL"

        if(jobPass.type_simple == "SUBSURFACE"):
            return "SUBSURFACE"

        if(jobPass.type_simple == "ALBEDO"):
            return "DIFFUSE"

    # TEXTUREOVEN PROFILES
    else:

        if(jobPass.type_simple == "NORMAL"):
            if(jobPass.normal_simple_mode == "+Y"):
                bpy.context.scene.render.bake.normal_g = "POS_Y"
            if(jobPass.normal_simple_mode == "-Y"):
                bpy.context.scene.render.bake.normal_g = "NEG_Y"
            return "NORMAL"

        if(jobPass.type_simple == "SUBSURFACE"):
            bpy.context.scene.render.bake.use_pass_color = True
            bpy.context.scene.render.bake.use_pass_direct = True
            bpy.context.scene.render.bake.use_pass_indirect = True
            return "SUBSURFACE"

        if(jobPass.type_simple == "ALBEDO"):
            bpy.context.scene.cycles.samples = 8
            bpy.context.scene.render.bake.use_pass_color = True
            bpy.context.scene.render.bake.use_pass_direct = False
            bpy.context.scene.render.bake.use_pass_indirect = False
            return "DIFFUSE"

    if(jobPass.type_simple == "AO"):
        return "AO"

    if(jobPass.type_simple == "SHADOWS"):
        return "SHADOW"

    if(jobPass.type_simple == "ROUGHNESS"):
        return "ROUGHNESS"

    if(jobPass.type_simple == "METALLIC"):
        bpy.context.scene.cycles.samples = 8
        return "EMIT"

    if(jobPass.type_simple == "SPECULAR"):
        bpy.context.scene.cycles.samples = 8
        return "EMIT"

    if(jobPass.type_simple == "ALPHA"):
        bpy.context.scene.cycles.samples = 8
        return "EMIT"

    if(jobPass.type_simple == "ID"):
        bpy.context.scene.cycles.samples = 8
        return "EMIT"

def RemoveColorManagement():
    bpy.context.scene.display_settings.display_device = "sRGB"
    bpy.context.scene.view_settings.view_transform = "Standard"
    bpy.context.scene.view_settings.look = "None"
    bpy.context.scene.view_settings.exposure = 0
    bpy.context.scene.view_settings.gamma = 1

def GetFixedMargin(jobPass):
    margin = jobPass.margin
    if(jobPass.aliasing == "2x"):
        margin *= 2
    if(jobPass.aliasing == "4x"):
        margin *= 4
    return margin
