# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Noodler",
    "author": "BD3D",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "location": "Node Editor: (Shortcuts, Panel), Addonpreferences",
    "description": "Collection of useful tools/shortcuts for node editors",
    "doc_url": "https://blenderartists.org/t/bd3d-node-plugin/1297740",
    "category": "Node",
}


import bpy, blf
import os, sys 
from math import hypot
from mathutils import Vector

#add bl_ui to modules, we'll need to borrow a class later
scr = bpy.utils.system_resource('SCRIPTS')
pth = os.path.join(scr,'startup','bl_ui')
if pth not in sys.path:
    sys.path.append(pth)

from bl_ui.properties_paint_common import BrushPanel


#########################################################
# FUNCTIONS
#########################################################


def get_active_tree(context):
    """Get nodes from currently edited tree.
    If user is editing a group, space_data.node_tree is still the base level (outside group).
    context.active_node is in the group though, so if space_data.node_tree.nodes.active is not
    the same as context.active_node, the user is in a group.
    source: node_wrangler.py"""

    tree = context.space_data.node_tree
    path = []

    if tree.nodes.active:

        #Check recursively until we find the real active node_tree
        while (tree.nodes.active != context.active_node):
            tree = tree.nodes.active.node_tree
            path.append(tree)
            continue
    
    return tree, path

def set_all_node_select(nodes, select_state,):
    for n in nodes:
        n.select = select_state
    return None 

def popup_menu(msgs,title,icon):

    def draw(self, context):
        layout = self.layout
        for msg in msgs:
            layout.label(text=msg)
        return  

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
    return None 

def ensure_mouse_cursor(context, event,):
    """function needed to get cursor location, source: node_wrangler.py"""

    space = context.space_data
    v2d = context.region.view2d
    tree = space.edit_tree

    # convert mouse position to the View2D for later node placement
    if (context.region.type == "WINDOW"):
          space.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
    else: space.cursor_location = tree.view_center

    return None 

def get_node_location(node, nodes,):
    """find real location of a node (global space guaranteed)"""
    
    if (node.parent is None):
        return node.location

    else: x,y = node.location

    while (node.parent is not None):
        x += node.parent.location.x
        y += node.parent.location.y
        node = node.parent
        continue

    return x,y

def get_nodes_in_frame_box(boxf, nodes, frame_support=True,):
    """search node that can potentially be inside this boxframe created box"""

    for n in nodes:

        #we do not want information on ourselves
        if ((n==boxf) or (n.parent==boxf)):
            continue

        #for now, completely impossible to get a frame location..
        if (n.type=="FRAME"):
            continue

        locx,locy = get_node_location(n,nodes)

        if boxf.location.x <= locx <= (boxf.location.x + boxf.dimensions.x) and \
           boxf.location.y >= locy >= (boxf.location.y - boxf.dimensions.y):
            yield n

AllFonts = {} 

def blf_add_font(text="Hello World", size=[50,72], position=[2,180], color=[1,1,1,0.1], origin="BOTTOM LEFT", shadow={"blur":3,"color":[0,0,0,0.6],"offset":[2,-2],}):
    """draw fond handler"""

    global AllFonts

    Id = str(len(AllFonts.keys())+1)
    AllFonts[Id]= {"font_id":0, "handler":None,}

    def draw(self, context):
            
        font_id = AllFonts[Id]["font_id"]
    
        #Define X
        if "LEFT" in origin:
            pos_x = position[0]
        elif "RIGHT" in origin:
            pos_x = bpy.context.region.width - position[0]
        #Define Y
        if "BOTTOM" in origin:
            pos_y = position[1]
        elif "TOP" in origin:
            pos_y = bpy.context.region.height - position[1]


        blf.position(font_id, pos_x, pos_y, 0)

        blf.color(font_id, color[0], color[1], color[2], color[3])

        blf.size(font_id, size[0], size[1])

        if shadow is not None:
            blf.enable(font_id, blf.SHADOW)
            blf.shadow(font_id, shadow["blur"], shadow["color"][0], shadow["color"][1], shadow["color"][2], shadow["color"][3])
            blf.shadow_offset(font_id, shadow["offset"][0], shadow["offset"][1])

        blf.draw(font_id, text)

        return None 

    # #try to Load custom font?
    # import os
    # font_path = bpy.path.abspath('//Zeyada.ttf')
    # if os.path.exists(font_path):
    #       AllFonts["font_id"] = blf.load(font_path)
    # else: AllFonts["font_id"] = 0

    #add font handler 
    draw_handler = bpy.types.SpaceNodeEditor.draw_handler_add( draw, (None, None), 'WINDOW', 'POST_PIXEL')
    AllFonts[Id]["handler"] = draw_handler

    return Id

def blf_clear_all_fonts(Id=None):
    """clear all fond appended"""

    global AllFonts

    if (Id is not None): 
        if Id in AllFonts:
            bpy.types.SpaceNodeEditor.draw_handler_remove(AllFonts[Id]["handler"], "WINDOW")
            del AllFonts[Id]
        return None 

    for Id,font in AllFonts.items():
        bpy.types.SpaceNodeEditor.draw_handler_remove(font["handler"], "WINDOW")
    AllFonts.clear()

    return None 

def blf_temporary_msg(text="", size=[], position=[], origin="", color=None, shadow={}, clear_before=True, first_interval=1.0):

    blf_clear_all_fonts()
    Id = blf_add_font(text=text, size=size, position=position, origin=origin, color=color, shadow=shadow)
    def remove_handler_shortly():
        blf_clear_all_fonts(Id)
        return None 
    bpy.app.timers.register(remove_handler_shortly, first_interval=first_interval)

    return None 


#########################################################
# OPERATOR
#########################################################


class NOODLER_OT_draw_frame_box(bpy.types.Operator):

    bl_idname = "noodler.draw_frame_box"
    bl_label = "Internal Operator to get mouse position in space"
    bl_options = {'REGISTER'}

    def __init__(self): 
        #internal props for modal
        self.node_tree = None
        self.boxf = None
        self.old = (0,0)
        self.timer = None 
        self.selframerate = 0.350 #selection refreshrate in s, const

    @classmethod
    def poll(cls, context):
        
        space = context.space_data
        valid_trees = ["ShaderNodeTree","CompositorNodeTree","TextureNodeTree","GeometryNodeTree",]

        return (space.type=="NODE_EDITOR") and (space.node_tree is not None) and (space.tree_type in valid_trees)

    def invoke(self, context, event):

        ng , _ = get_active_tree(context)
        self.node_tree = ng

        ensure_mouse_cursor(context, event)
        self.old = context.space_data.cursor_location.copy()  

        boxf = ng.nodes.new("NodeFrame")
        self.boxf = boxf 
        boxf.bl_width_min = boxf.bl_height_min = 20
        boxf.width = boxf.height = 0
        boxf.select = False
        boxf.location = self.old

        noodle_scn = context.scene.noodler
        boxf.use_custom_color = noodle_scn.frame_use_custom_color
        boxf.color = noodle_scn.frame_color
        boxf.label = noodle_scn.frame_label
        boxf.label_size = noodle_scn.frame_label_size

        #start timer, needed to regulate a function refresh rate
        self.timer = context.window_manager.event_timer_add(self.selframerate, window=context.window)

        #start modal 
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):     

        context.area.tag_redraw()

        #if user confirm:
        
        if ((event.value=="RELEASE") or (event.type=="LEFTMOUSE")):
            
            nodes = list(get_nodes_in_frame_box(self.boxf,self.node_tree.nodes))

            if (len(nodes)==0):
                return {'FINISHED'}
        
            for n in nodes:
                n.parent = self.boxf
                continue

            set_all_node_select(self.node_tree.nodes,False)
            self.node_tree.nodes.active = self.boxf
            self.boxf.select = True

            context.area.tag_redraw()
            context.window_manager.event_timer_remove(self.timer)

            return {'FINISHED'}

        #if user cancel:

        elif event.type in ("ESC","RIGHTMOUSE"):
            
            self.node_tree.nodes.remove(self.boxf)
            set_all_node_select(self.node_tree.nodes,False)

            context.area.tag_redraw()
            context.window_manager.event_timer_remove(self.timer)

            return {'CANCELLED'}

        #else, adjust frame location/width/height:
    
        #else recalculate position & frame dimensions
        ensure_mouse_cursor(context, event)
        new = context.space_data.cursor_location
        old = self.old

        #new y above init y
        if (old.y<=new.y):
              self.boxf.location.y = new.y
              self.boxf.height = (new.y-old.y)
        else: self.boxf.height = (old.y-new.y)

        #same principle as above for width
        if (old.x>=new.x):
              self.boxf.location.x = new.x
              self.boxf.width = (old.x-new.x)
        else: self.boxf.width = (new.x-old.x)

        #dybamic selection:

        #enable every 100ms, too slow for python.. 
        if (event.type != 'TIMER'):
            return {'RUNNING_MODAL'}

        #show user a preview off the future node
        set_all_node_select(self.node_tree.nodes,False)
        for n in get_nodes_in_frame_box(self.boxf,self.node_tree.nodes):
            n.select = True
            continue

        return {'RUNNING_MODAL'}

class NOODLER_OT_dummy(bpy.types.Operator, ):

    bl_idname = "noodler.dummy"
    bl_label = ""
    bl_description = ""
        
    def execute(self, context, ):

        return {'FINISHED'}


#########################################################
#  GUI
#########################################################


class NOODLER_PT_tool_search(bpy.types.Panel):

    bl_idname = "NOODLER_PT_tool_search"
    bl_label = "Node Search"
    bl_category = "Tool"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    def draw(self, context):

        layout = self.layout
        noodle_scn = context.scene.noodler
            
        row = layout.row(align=True)
        row.prop(noodle_scn,"search_keywords",text="",icon="VIEWZOOM")
        row.prop(noodle_scn,"search_center",text="",icon="ZOOM_ALL")

        layout.label(text="Search Filters:")

        layout.use_property_split = True

        layout.prop(noodle_scn,"search_labels")
        layout.prop(noodle_scn,"search_types")
        layout.prop(noodle_scn,"search_socket_names")
        layout.prop(noodle_scn,"search_socket_types")
        layout.prop(noodle_scn,"search_names")
        layout.prop(noodle_scn,"search_input_only")
        layout.prop(noodle_scn,"search_frame_only")

        s = layout.column()
        s.label(text=f"Found {noodle_scn.search_found} Element(s)")
    
        return None 

class NOODLER_PT_tool_color_palette(bpy.types.Panel,BrushPanel):
    #palette api is a bit bad, it is operatiors designed for unified paint tools
    #so we are hijacking the context for us then.

    bl_idname = "NOODLER_PT_tool_color_palette"
    bl_label = "Assign Palette"
    bl_category = "Tool"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):

        layout = self.layout
        noodle_scn = context.scene.noodler
        settings = context.tool_settings.vertex_paint
        unified = context.tool_settings.unified_paint_settings

        if settings is None: 
            col = layout.column()
            col.active = False
            col.scale_y = 0.8
            col.label(text="Please go in vertex-paint to")
            col.label(text="initiate the palette API.")
            return None 
        
        layout.template_ID(settings, "palette", new="palette.new")

        if settings.palette:
            row = layout.row(align=True)
            colo = row.row(align=True)
            colo.prop(unified,"color",text="")
            colo.prop(noodle_scn,"palette_prop",text="")

            row.operator("noodler.reset_color",text="",icon="LOOP_BACK",)
            layout.template_palette(settings, "palette", color=True,)

        return None 

class NOODLER_PT_tool_frame(bpy.types.Panel):

    bl_idname = "NOODLER_PT_tool_frame"
    bl_label = "Draw Frame"
    bl_category = "Tool"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    def draw(self, context):

        layout = self.layout
        noodle_scn = context.scene.noodler
        
        layout.use_property_split = True

        layout.prop(noodle_scn,"frame_use_custom_color")
        col = layout.column()
        col.prop(noodle_scn,"frame_sync_color")
        col.active = noodle_scn.frame_use_custom_color
        col.prop(noodle_scn,"frame_color")
        layout.prop(noodle_scn,"frame_label")
        layout.prop(noodle_scn,"frame_label_size")

        return None 

class NOODLER_PF_node_framer(bpy.types.AddonPreferences):
    bl_idname = __name__

    def draw(self, context):

        layout = self.layout

        kc = bpy.context.window_manager.keyconfigs.addon

        #draw shortcuts items:
        for km, kmi, name, icon in addon_keymaps:
            #tweaked snippets from `rna_keymap_ui.py`

            col = layout.column(align=True)

            row = col.box().row()
            row.label(text=name, icon=icon,)
            row.prop(kmi,"active",text="",emboss=False,)

            box = col.box()
            box.active = kmi.active
            split = box.split(factor=0.4)
            sub = split.row()

            if km.is_modal:
                  sub.prop(kmi, "propvalue", text="")
            else: sub.prop(kmi, "idname", text="")

            if kmi.map_type not in {'TEXTINPUT', 'TIMER'}:

                sub = split.column()
                subrow = sub.row(align=True)

                if (kmi.map_type=='KEYBOARD'):

                    subrow.prop(kmi, "type", text="", event=True)
                    subrow.prop(kmi, "value", text="")
                    subrow_repeat = subrow.row(align=True)
                    subrow_repeat.active = kmi.value in {'ANY', 'PRESS'}
                    subrow_repeat.prop(kmi, "repeat", text="Repeat", toggle=True)

                elif kmi.map_type in {'MOUSE', 'NDOF'}:

                    subrow.prop(kmi, "type", text="")
                    subrow.prop(kmi, "value", text="")

                subrow = box.row()
                mainkey = subrow.row()
                mainkey.scale_x = 1.3
                mainkey.separator(factor=0.2)
                #subrow.prop(kmi, "any", text="Any",) #what's the use of this? 
                mainkey.prop(kmi, "shift", text="",icon="EVENT_SHIFT")
                mainkey.prop(kmi, "ctrl", text="",icon="EVENT_CTRL")
                mainkey.prop(kmi, "alt", text="",icon="EVENT_ALT")
                mainkey.prop(kmi, "oskey", text="",icon="EVENT_OS")

                keymod = subrow.row(align=True)
                keymod.alignment = "RIGHT"
                keymod.scale_x = 2
                keymod.label(text="KeyMod:")
                keymod.prop(kmi, "key_modifier", text="", event=True)

            # Operator properties
            box.template_keymap_item_properties(kmi)

            # Modal key maps attached to this operator
            if not km.is_modal:
                kmm = kc.keymaps.find_modal(kmi.idname)
                if kmm:
                    draw_km(addon_keymaps, kc, kmm, None, layout, level + 1)
                    layout.context_pointer_set("keymap", km)

            continue
        
        return None 


#########################################################
#  COLOR PALETTE 
#########################################################


#color palette api is completely broken, it only works with paint tools..
#we need to check if context is node editor and and find active nodetree from msgbus function.. 
#the problem is that context is not accessible from message bus, the following code is a workaround

mouse_coord = (0,0) 

class NOODLER_OT_get_mouse_location(bpy.types.Operator):

    bl_idname = "noodler.get_mouse_location"
    bl_label = ""
    bl_options = {'REGISTER'}

    def invoke(self, context, event):

        global mouse_coord
        mouse_coord = event.mouse_x,event.mouse_y

        return {'FINISHED'}

class NOODLER_OT_reset_color(bpy.types.Operator, ):

    bl_idname = "noodler.reset_color"
    bl_label = "Reset Color"
    bl_description = "Reset Color"
        
    def execute(self, context, ):
        
        ng , _ = get_active_tree(context)
        for n in ng.nodes:
            if n.select:
                n.use_custom_color = False

        return {'FINISHED'}

def find_space_data_from_mouse(x,y):
    
    areas =  bpy.context.window.screen.areas
    for a in areas:
        if (a.x<x<a.x+a.width) and (a.y<y<a.y+a.height):
            return a.spaces[0]
    return None 

palette_msgbus_owner = object()

def palette_callback(*args):
    """execute this function everytime user is clicking on a palette color""" 
    #bpy.ops.noodler.reset_color()

    bpy.ops.noodler.get_mouse_location(('INVOKE_DEFAULT'))
    global mouse_coord

    space = find_space_data_from_mouse(mouse_coord[0], mouse_coord[1])
    if (space is None) or (space.type!="NODE_EDITOR"):
        return None 

    if not bpy.context.scene.tool_settings.unified_paint_settings.use_unified_color:
        bpy.context.scene.tool_settings.unified_paint_settings.use_unified_color = True 
    palette_color = bpy.context.tool_settings.unified_paint_settings.color

    noodle_scn = bpy.context.scene.noodler
    noodle_scn.palette_prop = list(palette_color)[:3]
    if noodle_scn.frame_sync_color:
        noodle_scn.frame_color = list(palette_color)[:3]

    ng = space.node_tree
    for n in ng.nodes:
        if n.select:
            n.use_custom_color=True
            n.color = palette_color

    return None 

def palette_prop_upd(self, context):

    if context.space_data is None:
        return None 
        
    ng , _ = get_active_tree(context)
    for n in ng.nodes:
        if n.select:
            if not n.use_custom_color:
                n.use_custom_color = True
            n.color = self.palette_prop

    return None 


#########################################################
#  SHORTCUT 
#################################################\u2605=★


def get_shortcuts(nodes, index=None):

    shortcuts = []

    for n in nodes:
        if n.name.startswith("★"):
            shortcuts.append(n)
        continue

    def namesort(elem):
        return elem.name
    shortcuts.sort(key=namesort)

    if (index is not None):
        for i,n in enumerate(shortcuts):
            if (i==index):
                return n
        return None 

    return shortcuts

def shortcut_index_upd(self, context):

    ng , _ = get_active_tree(context)

    n = get_shortcuts(ng.nodes, index=self.shortcut_index)
    if n is None:
        return None 

    set_all_node_select(ng.nodes, False,)
    n.select = True 

    override = bpy.context.copy()
    override["area"] = context.area
    override["space"] = context.area.spaces[0]
    override["region"] = context.area.regions[3]
    bpy.ops.node.view_selected((override))
        
    return None

class NOODLER_OT_shortcut_add(bpy.types.Operator):

    bl_idname      = "noodler.shortcut_add"
    bl_label       = "Add shortcuts reroute"
    bl_description = "Add shortcuts reroute"

    def invoke(self, context, event):

        ng = context.space_data.node_tree
        noodle_scn = context.scene.noodler

        idx = 1
        name = f"★{idx:02}"
        while name in [n.name for n in ng.nodes]:
            idx +=1
            name = f"★{idx:02}"

        if (idx>50):
            popup_menu([f"You reached {idx-1} shortcuts.","Won't do more. Sorry mate."],"Congratulation!","FUND")
            return {"FINISHED"}

        sh = ng.nodes.new("NodeReroute")
        sh.name = sh.label = name
        ensure_mouse_cursor(context, event)
        sh.location = context.space_data.cursor_location

        blf_temporary_msg(text=f"Added Shortcut '{sh.label}'", size=[45,66], position=[30,70], origin="BOTTOM LEFT", color=[0.9,0.9,0.9,0.9], shadow={"blur":3,"color":[0,0,0,0.4],"offset":[2,-2],})
        context.area.tag_redraw()

        return {"FINISHED"}

class NOODLER_OT_shortcut_loop(bpy.types.Operator):

    bl_idname      = "short.shortcut_loop"
    bl_label       = "Loop over shortcuts"
    bl_description = "Loop over shortcuts"

    def execute(self, context):

        ng = context.space_data.node_tree
        noodle_scn = context.scene.noodler

        shortcuts = get_shortcuts(ng.nodes)
        shortcuts_len = len(shortcuts)

        if (shortcuts_len==0):

            blf_temporary_msg(text=f"No Shortcuts Found", size=[45,66], position=[30,70], origin="BOTTOM LEFT", color=[0.9,0.9,0.9,0.9], shadow={"blur":3,"color":[0,0,0,0.4],"offset":[2,-2],})
            context.area.tag_redraw()

            return {"FINISHED"}

        index = noodle_scn.shortcut_index
        if noodle_scn.shortcut_index>=(shortcuts_len-1):
              noodle_scn.shortcut_index = 0
        else: noodle_scn.shortcut_index += 1

        sh = get_shortcuts(ng.nodes, index=noodle_scn.shortcut_index)

        blf_temporary_msg(text=f"Looping to Shortcut '{sh.label}'", size=[45,66], position=[30,70], origin="BOTTOM LEFT", color=[0.9,0.9,0.9,0.9], shadow={"blur":3,"color":[0,0,0,0.4],"offset":[2,-2],})
        context.area.tag_redraw()

        return {"FINISHED"}

#########################################################
#  SEARCH
#########################################################


def search_upd(self, context):
    """search in context nodetree for nodes"""

    ng , _ = get_active_tree(context)

    keywords = self.search_keywords.lower().replace(","," ").split(" ")
    keywords = set(keywords)

    def is_matching(keywords,terms):
        matches = []
        for k in keywords:
            for t in terms:
                matches.append(k in t)
        return any(matches) 

    found = []
    for n in ng.nodes:
        terms = []

        if self.search_labels:
            name = n.label.lower()
            if not name:
                name = n.bl_label.lower()
            terms += name.split(" ")

        if self.search_types:
            terms += n.type.lower().split(" ")

        if self.search_names:
            name = n.name + " " + n.bl_idname
            terms += name.replace("_"," ").lower().split(" ")

        if self.search_socket_names:
            for s in [*list(n.inputs),*list(n.outputs)]:
                name = s.name.lower() 
                if name not in terms:
                    terms += name.split(" ")

        if self.search_socket_types:
            for s in [*list(n.inputs),*list(n.outputs)]:
                name = s.type.lower() 
                if name not in terms:
                    terms += name.split(" ")

        if not is_matching(keywords,terms):
            continue

        found.append(n)

        continue

    set_all_node_select(ng.nodes, False,)

    self.search_found = len(found)
    if (self.search_found==0):
        return None

    if self.search_input_only:
        for n in found.copy():
            if (len(n.inputs)==0 and (n.type!="FRAME")):
                continue
            found.remove(n)
            continue

    if self.search_frame_only:
        for n in found.copy():
            if (n.type!="FRAME"):
                found.remove(n)
            continue

    for n in found:
        n.select = True 

    if self.search_center:

        #from prop update,need some context override

        override = bpy.context.copy()
        override["area"] = context.area
        override["space"] = context.area.spaces[0]
        override["region"] = context.area.regions[3]
        bpy.ops.node.view_selected((override))
    
    return None


#########################################################
#  PROPERTIES
#########################################################


class NOODLER_PR_scene(bpy.types.PropertyGroup): 
    """noodle_scn = bpy.context.scene.noodler"""

    frame_use_custom_color: bpy.props.BoolProperty(default=False,name="Frame Color")
    frame_color: bpy.props.FloatVectorProperty(default=(0,0,0),subtype="COLOR",name="Color")
    frame_sync_color: bpy.props.BoolProperty(default=True,name="Sync Color",description="Synchronize with palette") 
    frame_label: bpy.props.StringProperty(default=" ",name="Label")
    frame_label_size: bpy.props.IntProperty(default=16,min=0,name="Label Size")

    palette_prop: bpy.props.FloatVectorProperty(default=(0,0,0),subtype="COLOR",name="Color",update=palette_prop_upd)

    search_keywords: bpy.props.StringProperty(default=" ",name="Keywords",update=search_upd)
    search_center: bpy.props.BoolProperty(default=True,name="Recenter View",update=search_upd) 
    search_labels: bpy.props.BoolProperty(default=True,name="Label",update=search_upd)
    search_types: bpy.props.BoolProperty(default=True,name="Type",update=search_upd)
    search_names: bpy.props.BoolProperty(default=False,name="Internal Name",update=search_upd)
    search_socket_names: bpy.props.BoolProperty(default=False,name="Socket Names",update=search_upd)
    search_socket_types: bpy.props.BoolProperty(default=False,name="Socket Types",update=search_upd)
    search_input_only: bpy.props.BoolProperty(default=False,name="Input Only",update=search_upd)
    search_frame_only: bpy.props.BoolProperty(default=False,name="Frame Only",update=search_upd)
    search_found: bpy.props.IntProperty(default=0)

    shortcut_index : bpy.props.IntProperty(default=0,update=shortcut_index_upd,)

#########################################################
#  REGISTER
#########################################################


addon_keymaps = []

# entry: (identifier, key, action, CTRL, SHIFT, ALT, props, name, icon) props: ( (property name, property value), )

kmi_defs = ( 
    (NOODLER_OT_draw_frame_box.bl_idname, "F", "PRESS", False, False, False, (), "Operator: Draw Frame", "ALIGN_TOP"),
    (NOODLER_OT_shortcut_loop.bl_idname,  "S", "PRESS", False, False, False, (), "Operator: Loop Shortcuts", "SOLO_OFF"),
    (NOODLER_OT_shortcut_add.bl_idname,   "S", "PRESS", False, True,  False, (), "Operator: Add Shortcut",   "SOLO_OFF"),
    )

classes = (
    NOODLER_PF_node_framer,

    NOODLER_PT_tool_search,
    NOODLER_PT_tool_color_palette,
    NOODLER_PT_tool_frame,

    NOODLER_PR_scene,

    NOODLER_OT_draw_frame_box,
    NOODLER_OT_get_mouse_location,
    NOODLER_OT_reset_color,
    NOODLER_OT_shortcut_add,
    NOODLER_OT_shortcut_loop,
    NOODLER_OT_dummy,
    )


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    #properties
    bpy.types.Scene.noodler = bpy.props.PointerProperty(type=NOODLER_PR_scene)

    #color palette update
    bpy.msgbus.subscribe_rna(
        key=bpy.types.PaletteColor,#get notified when active color change
        owner=palette_msgbus_owner,
        notify=palette_callback,
        args=(bpy.context,),
        options={"PERSISTENT"},
        )

    #keymaps
    addon_keymaps.clear()
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="Node Editor", space_type="NODE_EDITOR")
        for (identifier, key, action, CTRL, SHIFT, ALT, props, name, icon) in kmi_defs:
            kmi = km.keymap_items.new(identifier, key, action, ctrl=CTRL, shift=SHIFT, alt=ALT)
            if props:
                for prop, value in props:
                    setattr(kmi.properties, prop, value)
            addon_keymaps.append((km, kmi, name, icon))

def unregister():

    #keymaps
    for km, kmi, _, _ in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    #color palette update
    bpy.msgbus.clear_by_owner(palette_msgbus_owner)

    #properties 
    del bpy.types.Scene.noodler 

    #classes
    for cls in classes:
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
