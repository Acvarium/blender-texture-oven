# Copyright (C) Cogumelo Softworks
# License: http://www.gnu.org/licenses/gpl.html GPL version 3 or higher

import bpy

import random
import os, sys
import subprocess
import json
import io
import time

from . bt_utils import *
from . bt_autopack import *
from bpy_extras.image_utils import load_image

class BakeAtlas(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "textureoven.bakeatlas"
    bl_label = "TextureOven: Bake Atlas"

    job : bpy.props.StringProperty()

    def execute(self, context):
        Jobs = context.scene.TextureOven_Jobs.Jobs
        for j in Jobs:
            if(j.name == self.job):
                Cycles_DoAtlasBake(j)
        return {'FINISHED'}

class BakeIndividual(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "textureoven.bakeindividual"
    bl_label = "TextureOven: Bake Individual"

    job : bpy.props.StringProperty()

    def execute(self, context):
        Jobs = context.scene.TextureOven_Jobs.Jobs
        for j in Jobs:
            if(j.name == self.job):
                Cycles_DoIndividualBake(j)
        return {'FINISHED'}

def Cycles_DoAtlasBake(activeJob):
    print("Cycles_DoAtlasBake")
    if(not activeJob.enabled):
        reports = LoadBakeReports()
        jobList = reports["jobs"]

        for Job in jobList:
            if(Job["name"] == activeJob.name):
                Job["fileList"] = ""
                Job["status"] = "Baked"
                SaveBakeReport(reports)
                return
    else:

        settings = activeJob.job_settings
        listObjects = GetObjectListJob(activeJob,settings,True)
        listObjectsFrom = GetObjectListJob(activeJob,settings,False)
      

        passList = GetActivePasses(activeJob)

        reports = LoadBakeReports()
        jobList = reports["jobs"]

        outputFileList = []

        # Para Cada Passo Ativo
        for idx_pass,jobPass in enumerate(passList):

            JobReport = None
            for Job in jobList:
                if(Job["name"] == activeJob.name):
                    JobReport = Job

            reports["general"]["processCurrent"] = str(int(reports["general"]["processCurrent"])+1)
            JobReport["passCount"] = str(len(passList))
            JobReport["passCurrent"] = str(idx_pass + 1)
            SaveBakeReport(reports)

            #keepMaterials = []
            keepMaterialOutput = []
            AlreadyHandledMaterials = []

            #Setup materials for object, that will be baked from
            for idx_obj,obj in  enumerate(listObjectsFrom):
                currentObject = obj[0]
                for mat in currentObject.data.materials:

                    if(mat in AlreadyHandledMaterials):
                        SetTextureOvenUV(obj)
                        continue

                    print("FIXING MAT----------------------------------")
                    print(mat)

                    AlreadyHandledMaterials.append(mat)

                    node_tree = mat.node_tree
                    for node in node_tree.nodes:
                        node.select = False

                    FixUVNodes(mat,obj)

                    keepMaterialOutput.append([node_tree,SetCustomMaterial(currentObject,mat,jobPass,settings)])

                    SetTextureOvenUV(obj)


            # Para Cada Objeto
            for idx_obj,obj in enumerate(listObjects):

                reports = LoadBakeReports()
                jobList = reports["jobs"]

                JobReport = None
                for Job in jobList:
                    if(Job["name"] == activeJob.name):
                        JobReport = Job

                JobReport["objCurrent"] = str(len(listObjects))
                JobReport["objCount"] = str(len(listObjects))

                SaveBakeReport(reports)

                currentObject = obj[0]
                tempImage = CreateImage(activeJob,currentObject,jobPass,True)

                #keepMaterials.append(ApplyExternalMaterial(currentObject,jobPass.type_simple));

                # Para cada Material
                for mat in currentObject.data.materials:

                    if(mat in AlreadyHandledMaterials):
                        SetTextureOvenUV(obj)
                        continue

                    print("FIXING MAT----------------------------------")
                    print(mat)

                    AlreadyHandledMaterials.append(mat)

                    # Desseleciona Todos os Nodes
                    node_tree = mat.node_tree
                    for node in node_tree.nodes:
                        node.select = False

                    FixUVNodes(mat,obj)

                    keepMaterialOutput.append([node_tree,SetCustomMaterial(currentObject,mat,jobPass,settings)]);

                    # Cria Image Nodes
                    image_node = node_tree.nodes.new('ShaderNodeTexImage')
                    image_node.location = (100,100)
                    image_node.image = tempImage
                    image_node.select = True
                    image_node.update()

                    # Torna Imagem Ativa
                    mat.node_tree.nodes.active = image_node

                    SetTextureOvenUV(obj)

            #Configura o Render Settings
            SetRenderSettings(jobPass,settings)

            #Bake -------------------------------
            # Se estiver utilizando target
            if settings.target != "":

                #Cria Lista de Objetos a serem usados como source
                ListBake = []
                for obj_name in activeJob.job_objs.coll:
                    for obj in bpy.context.scene.objects:
                        if obj_name.name == obj.name:
                            ListBake.append((obj,obj_name))

                # Seleciona todos os objetos da lista e o target e o torna ativo
                for obj in bpy.context.scene.objects:
                    obj.select_set(False)
                    for obj2 in ListBake:
                        if obj == obj2[0]:
                            obj.select_set(True)

                for obj in listObjects:
                    obj[0].select_set(True)
                    bpy.context.view_layer.objects.active = obj[0]

            else:
                # Desseleciona todos os objetos da cena e seleciona Apenas os Objetos da Lista
                bpy.ops.object.select_all(action="DESELECT")
                for obj in listObjects:
                    obj[0].select_set(True)
                    bpy.context.view_layer.objects.active = obj[0]

            # BAKE
            if(settings.profile_type == "TEXTUREOVEN"):
                jobPass.type = SetupTextureOvenPass(jobPass,settings)

            # BAKE!
            if settings.target == "":
                bpy.ops.object.bake(type=jobPass.type,
                                    use_clear=True,
                                    use_selected_to_active=False,
                                    normal_r = jobPass.normal_r,
                                    normal_g = jobPass.normal_g,
                                    normal_b = jobPass.normal_b,
                                    normal_space = jobPass.normal_space,
                                    margin = GetFixedMargin(jobPass))
            else:
                _cage = False
                if settings.cage != "":
                    _cage = True



                bpy.ops.object.bake(type=jobPass.type,
                                    use_clear=True,
                                    use_selected_to_active=True,
                                    cage_extrusion=settings.distance,
                                    normal_r = jobPass.normal_r,
                                    normal_g = jobPass.normal_g,
                                    normal_b = jobPass.normal_b,
                                    cage_object = settings.cage,
                                    normal_space = jobPass.normal_space,
                                    margin = GetFixedMargin(jobPass),
                                    use_cage = _cage)

            RestoreCustomOutput(keepMaterialOutput)

            #Save Image
            path = SaveImage(activeJob,currentObject,jobPass,tempImage,True)
            outputFileList.append(path)

            # Refaz o output Node
            print("-------------- REFAZ OUTPUT NODE ------------")
            print(keepMaterialOutput[:])

        reports = LoadBakeReports()
        jobList = reports["jobs"]

        for Job in jobList:
            if(Job["name"] == activeJob.name):
                Job["fileList"] = outputFileList
                Job["status"] = "Baked"
                SaveBakeReport(reports)

def Cycles_DoIndividualBake(activeJob):

    if(not activeJob.enabled):
        reports = LoadBakeReports()
        jobList = reports["jobs"]

        for Job in jobList:
            if(Job["name"] == activeJob.name):
                Job["fileList"] = ""
                Job["status"] = "Baked"
                SaveBakeReport(reports)
                return
    else:
        settings = activeJob.job_settings
        listObjects = GetObjectListJob(activeJob,settings,False)
        passList = GetActivePasses(activeJob)

        reports = LoadBakeReports()
        jobList = reports["jobs"]

        outputFileList = []

        # Para cada objeto da Lista
        for idx_obj,objData in enumerate(listObjects):

            JobReport = None
            for Job in jobList:
                if(Job["name"] == activeJob.name):
                    JobReport = Job

            JobReport["objCurrent"] = str(idx_obj + 1)
            JobReport["objCount"] = str(len(listObjects))
            JobReport["passCount"] = str(len(passList))

            SaveBakeReport(reports)

            # Para cada Passo Ativo
            for idx_pass,jobPass in enumerate(passList):

                JobReport["passCurrent"] = str(idx_pass + 1)
                reports["general"]["processCurrent"] = str(int(reports["general"]["processCurrent"])+1)

                SaveBakeReport(reports)

                # Seleciona o Objeto para exibição
                currentObject = objData[0]
                bpy.ops.object.select_all(action="DESELECT")
                currentObject.select_set(True)
                bpy.context.view_layer.objects.active = currentObject

                # Cria a imagem para dar bake
                tempImage = CreateImage(activeJob,currentObject,jobPass,False)

                # Materiais que precisam ser importados ao objeto
                #keepMaterials = ApplyExternalMaterial(currentObject,jobPass.type_simple);

                keepMaterialOutput = []
                # Para cada Material
                for mat in currentObject.data.materials:

                    # Desseleciona Todos os Nodes (TODO VER SE PRECISA POIS ELE JÁ SETA O IMAGEM COMO ATIVO )
                    node_tree = mat.node_tree
                    for node in node_tree.nodes:
                        node.select = False

                    FixUVNodes(mat,objData)

                    CreateImageNode(mat,tempImage)

                    # Seta a UV ativa
                    SetTextureOvenUV(objData)

                    #Configura o Render Settings
                    SetRenderSettings(jobPass,settings)

                    # Configura Custom Materials
                    keepMaterialOutput.append([node_tree,SetCustomMaterial(currentObject,mat,jobPass,settings)]);

                # MODIFICADO AQUI, BAKE POR MATERIAL???
                # BAKE
                if(settings.profile_type == "TEXTUREOVEN"):
                    jobPass.type = SetupTextureOvenPass(jobPass,settings)

                bpy.ops.object.bake(type=jobPass.type,
                                    use_clear=True,
                                    use_selected_to_active=False,
                                    normal_r = jobPass.normal_r,
                                    normal_g = jobPass.normal_g,
                                    normal_b = jobPass.normal_b,
                                    normal_space = jobPass.normal_space,
                                    margin = GetFixedMargin(jobPass))

                #RestoreMaterials(keepMaterials)
                RestoreCustomOutput(keepMaterialOutput)

                SaveBakeReport(reports)

                path = SaveImage(activeJob,currentObject,jobPass,tempImage,False)
                outputFileList.append(path)

        reports = LoadBakeReports()
        jobList = reports["jobs"]

        for Job in jobList:
            if(Job["name"] == activeJob.name):
                Job["fileList"] = outputFileList
                Job["status"] = "Baked"
                SaveBakeReport(reports)

def BakeCycles(context):
    print("-----------------------------START BAKE --------------------------------")
    jobList = context.scene.TextureOven_Jobs.Jobs
    jobList = [x for x in jobList if x.enabled == True]

    status = CheckBake(context,jobList)
    if status != True:
        print(status)
        return status

    # Informa ao report que iniciou o processo de bake
    context.scene.TextureOven_Jobs.is_baking = True;
    MakeUVs(context,jobList)

    # Salva a cena atual
    bpy.ops.wm.save_mainfile()

    # Reseta Variaveis de Report
    bpy.context.scene.TextureOven_ReportData.objCount = 0
    bpy.context.scene.TextureOven_ReportData.objCurrent = 0
    bpy.context.scene.TextureOven_ReportData.passCount = 0
    bpy.context.scene.TextureOven_ReportData.passCurrent = 0
    bpy.context.scene.TextureOven_ReportData.processCurrent = 0

    # TODO Calcular o ProgressCount baseado na cena
    processCount = 0
    bpy.context.scene.TextureOven_ReportData.jobCount = len(jobList)

    for activeJob in jobList:
        if(activeJob.job_settings.mode != "ATLAS"):
            passList = GetActivePasses(activeJob)
            settings = activeJob.job_settings
            objList = GetObjectListJob(activeJob,settings,False)
            processCount += (len(passList) * len(objList))
        else:
            passList = GetActivePasses(activeJob)
            processCount += len(passList)
            print("")
            print(processCount);
            print("")

    bpy.context.scene.TextureOven_ReportData.processCount = processCount

    # Inicializa o Json para essa sessão do Bake
    script_file = os.path.realpath(__file__)
    directory = os.path.dirname(script_file)

    reports = {}
    reports["general"] = {  "jobsCount" : 0,
                            "jobsCurrent" : 0,
                            "processCurrent" : 0
                            }
    reports["jobs"] = []
    for activeJob in jobList:
        activeJob = { "name" : activeJob.name,
                "status" : "Waiting",
                "objCount" : 0,
                "objCurrent" : 0,
                "passCount" : 0,
                "passCurrent" : 0
                }
        reports["jobs"].append(activeJob)


    with open(directory + "/report.json", 'w') as file:
        json.dump(reports, file, indent=2)

    # Carrega a Interface
    bpy.ops.textureoven.report()

    # Inicializa a Verificação de Progresso
    print("-----------------------------PROCESS JOB --------------------------------")
    bpy.app.timers.register(ProcessBakeJobProgress)
    return status

def ProcessBakeJobProgress():

    reports = LoadBakeReports()
    jobList = reports["jobs"]
    bpy.context.scene.TextureOven_ReportData.processCurrent = int(reports["general"]["processCurrent"])

    isProcessing = False
    for idx,job in enumerate(jobList):
        if(job["status"] == "Baking" or job["status"] == "Waiting"):
            isProcessing = True

        if(job["status"] == "Baking"):
            bpy.context.scene.TextureOven_ReportData.objCount = int(job["objCount"])
            bpy.context.scene.TextureOven_ReportData.objCurrent = int(job["objCurrent"])
            bpy.context.scene.TextureOven_ReportData.passCount = int(job["passCount"])
            bpy.context.scene.TextureOven_ReportData.passCurrent = int(job["passCurrent"])

        if(job["status"] == "Baked"):
            #activeJob = bpy.context.scene.TextureOven_Jobs.Jobs[idx]
            activeJob = bpy.context.scene.TextureOven_Jobs.Jobs[job["name"]]
            job["status"] = "Finished"
            SaveBakeReport(reports)
            PostBakeProcess(job,activeJob)


        # Se estiver aguardando ser chamado para o bake e finalizou ou ultimo ou é o primeiro então começa o bake desse passo
        if((job["status"] == "Waiting" and idx == 0) or (idx>0 and job["status"] == "Waiting" and jobList[idx-1]["status"] == "Finished" )):

            # Informa no status que iniciou o bake
            job["status"] = "Baking"
            SaveBakeReport(reports)

            #activeJob = bpy.context.scene.TextureOven_Jobs.Jobs[idx]
            activeJob = bpy.context.scene.TextureOven_Jobs.Jobs[job["name"]]

            filepath = bpy.data.filepath

            process = None

            if(activeJob.job_settings.mode != "ATLAS"):
                print("------------------------ BAKE INDIVIDUAL -----------------------------")
                process = subprocess.Popen([  bpy.app.binary_path,
                                        "--background",
                                        filepath,
                                        "--python-expr",
                                        'import bpy;p=bpy.ops.textureoven.bakeindividual(job ="'  + activeJob.name + '");'],
                                        shell=False)

            else:
                print("------------------------ BAKE ATLAS -----------------------------")

                process = subprocess.Popen([  bpy.app.binary_path,
                                        "--background",
                                        filepath,
                                        "--python-expr",
                                        'import bpy;p=bpy.ops.textureoven.bakeatlas(job ="'  + activeJob.name + '");'],
                                        shell=False)

            bpy.context.scene.TextureOven_ReportData.current_processPid = int(process.pid)
            bpy.context.scene.TextureOven_ReportData.jobCurrent = int(idx) + 1

    if(not isProcessing):
        bpy.app.timers.unregister(ProcessBakeJobProgress)
        bpy.context.scene.TextureOven_Jobs.is_baking = False;

    return 0.1

def PostBakeProcess(reportJob,activeJob):
    print("----------------- APPLY POST PROCESS----------------------")
    # Import Images
    if(activeJob.job_settings.postbake_importImages):
        for image in reportJob["fileList"]:
            img = load_image(image,check_existing=True,force_reload=True)
            img.name = os.path.splitext(os.path.basename(image))[0]

    if(activeJob.job_settings.postbake_createEevee and activeJob.job_settings.target == ""):
        if(activeJob.job_settings.mode != "ATLAS"):
            CreateIndividualEveeScene(activeJob)
