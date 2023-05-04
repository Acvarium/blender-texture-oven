# Copyright (C) Cogumelo Softworks - TextureOven v1.41
# License: http://www.gnu.org/licenses/gpl.html GPL version 3 or higher

import bpy
import mathutils
from math import radians
from . import bt_utils


def DoUnwrapper(objName,context,margin,angle,job):

    # Desseleciona todos os objetos da cena
    bpy.ops.object.select_all(action="DESELECT")

    # Seleciona o objeto e o torna ativo
    obj = bpy.data.objects[objName]
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Cria nova UV se necessário
    uvName = "TEXTUREOVEN_" + job
    hasUV = False
    for uvtemp in obj.data.uv_layers:
        if uvtemp.name == uvName:
            uv = uvtemp
            hasUV = True
            obj.data.uv_layers.active = uv
            break
    if not hasUV:
        uv = obj.data.uv_layers.new(name  = "TEXTUREOVEN_" + job )
        obj.data.uv_layers.active = uv

    final_name = uv.name
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=radians(angle), island_margin=margin, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")

    return final_name

def DoAtlas(context,activeJob):

    # Pack UVs
    # Cria novamente a lista dos objetos para dar Packs
    listObjects = []
    for obj_name in activeJob.job_objs.coll:
        for obj in context.scene.objects:
            if obj_name.name == obj.name:
                listObjects.append((obj,obj_name))

    settings = activeJob.job_settings

    # Desseleciona todos os objetos da cena e seleciona Apenas os Objetos da Lista
    bpy.ops.object.select_all(action="DESELECT")

    # Cria uma lista das UVs atuais
    listActiveUV = []

    # Aplica a UV correta
    for _obj in context.scene.objects:
        for obj in listObjects:
            if obj[0] == _obj:
                obj[0].select_set(True)
                # Torna Ativa a UV selecionada
                active_uv = None
                for idx,f in enumerate(obj[0].data.uv_layers):
                    if(f.active_render):
                        listActiveUV.append([obj[0],idx])

                    if(f.name == obj[1].uv):
                        f.active = True
                        f.active_render = True
                        f.active_clone = True



    # Utiliza o modo de ediçao de multiplos objetos para facilitar o processo

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action = "SELECT")
    if(settings.atlas_autoPack_area):
        bpy.ops.uv.average_islands_scale()

    bpy.ops.uv.pack_islands(margin = settings.atlas_autoPack_margin)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Retorna lista de UVs atuais

    for obj in listActiveUV:

        obj[0].data.uv_layers[obj[1]].active = True
        obj[0].data.uv_layers[obj[1]].active_render = True
        obj[0].data.uv_layers[obj[1]].active_clone = True
