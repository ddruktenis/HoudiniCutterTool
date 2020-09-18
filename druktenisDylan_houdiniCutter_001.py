### This script creates a boolean cutter tool with parameters to fracture geometry in Houdini ###
import hou
## OBJ LEVEL ##
obj = hou.node('/obj/') 
# Create geo node at object level
def create_geoNode():
    geo = obj.createNode('geo', "fractured_geo")
    geoLocation = hou.node('/obj/fractured_geo/')
    return geoLocation

##GEO LEVEL ##
# Create box node to create test geo for fracture at geo level
def create_boxGeo(geoNode):
    boxGeo= geoNode.createNode('box')
    boxLocation = hou.node('/obj/fractured_geo/box1')
    boxGeo.parm("type").set("polymesh")
    boxGeo.parm("scale").set(5)
    boxGeo.parmTuple("divrate").set([10,10,10])
    return boxLocation

# Create file node to import custom geo at geo level
def create_fileGeo(geoNode,pathInput):
    fileGeo= geoNode.createNode('file')
    fileLocation = hou.node('/obj/fractured_geo/file1')
    fileGeo.parm("file").set(pathInput)
    return fileLocation
    
# Create subnet with an input of box node at geo level
def create_subnet(geoNode,boxNode):
    subnetGeo = geoNode.createNode('subnet', "cutterTool")
    subnetLocation = hou.node('/obj/fractured_geo/subnet/cutterTool/')
    parm_group = subnetGeo.parmTemplateGroup()
    parm_folder = hou.FolderParmTemplate("folder", "Cutter Tool")
    parm_folder.addParmTemplate(hou.IntParmTemplate("cutterNum", "Number of Cutters", 1, (10, 100, 100),(1), (24)))
    parm_folder.addParmTemplate(hou.IntParmTemplate("detailValue", "Detail Value", 1, (1, 100, 100),(1), (24)))
    parm_group.append(parm_folder)
    subnetGeo.setParmTemplateGroup(parm_group)
    subnetGeo.setInput(0, boxNode)
    subnetGeo.moveToGoodPosition()
    return subnetLocation

## INSIDE THE SUBNET ##
def inside_subnet():
    subnetNode = hou.node('/obj/fractured_geo/cutterTool/')
    nullNode = create_nullInput(subnetNode)
    boundNode = create_bound(subnetNode, nullNode)
    isoNode = create_iso(subnetNode, boundNode)
    scatterNode = create_scatter(subnetNode, isoNode)
    randNode = create_rand(subnetNode, scatterNode)
    gridNode = create_grid(subnetNode)
    ctpNode = copy_toPoints(subnetNode, gridNode, randNode)
    hou.node('/obj/fractured_geo/cutterTool/').layoutChildren()
    atrNoiseNode = create_attNoise(subnetNode, ctpNode)
    mtNoiseNode = create_mtNoise(subnetNode, atrNoiseNode)
    groupNode = create_group(subnetNode, mtNoiseNode, boundNode)
    blastNode = create_blast(subnetNode, groupNode)
    outputNode = create_output(subnetNode, blastNode)
    
# This function creates a null in subnet. Rename null as "GEO_INPUT"
def create_nullInput(subnetNode):
    inputs = subnetNode.indirectInputs()
    nullNode = subnetNode.createNode('null', "GEO_INPUT")
    nullNode.setNextInput(inputs[0])
    return nullNode

# This function creates "bound" node... set lower padding and upper to value 30
def create_bound(subnetNode, nullNode):
    boundNode = subnetNode.createNode('bound')
    boundNode.parmTuple('minpad').set([1,1,1])
    boundNode.parmTuple('maxpad').set([1,1,1])
    boundNode.moveToGoodPosition()
    boundNode.setInput(0, nullNode)
    return boundNode
    
# This function creates iso offset node and connects input 0 to bound node. Set uniform sampling division value to 100
def create_iso(subnetNode, boundNode):
    isoNode = subnetNode.createNode('isooffset')
    isoNode.parm('samplediv').set(100)
    isoNode.moveToGoodPosition()
    isoNode.setInput(0, boundNode)
    return isoNode
    
# This function creates scatter node and connects input 0 to iso offset node. Set force total count value to 12
def create_scatter(subnetNode, isoNode):
    scatterNode = subnetNode.createNode('scatter')
    scatterNode.parm('npts').setExpression('ch("../cutterNum")')
    scatterNode.moveToGoodPosition()
    scatterNode.setInput(0, isoNode)
    return scatterNode

# Create attribute randomize node to set att name to N, distribution to Direction and dimenstions to a vaule of 3
def create_rand(subnetNode, scatterNode):
    randNode = subnetNode.createNode('attribrandomize')
    randNode.parm('name').set("N")
    randNode.parm('distribution').set('uniformorient')
    randNode.moveToGoodPosition()
    randNode.setInput(0, scatterNode)
    return randNode

# This function creates a grid node sets rows and columns to a value of 300
def create_grid(subnetNode):
    gridNode = subnetNode.createNode('grid')
    gridNode.parm('sizex').setExpression('bbox("../bound1/", D_XSIZE) * 2')
    gridNode.parm('sizey').setExpression('bbox("../bound1/", D_XSIZE)* 2')
    gridNode.parm("rows").set(300)
    gridNode.parm("cols").set(300)
    gridNode.moveToGoodPosition()
    return gridNode

# This function creates a copy to points node and takes grid1 into input 0 and attribrandomize1 into input 1
def copy_toPoints(subnetNode, gridNode, randNode):
    ctpNode = subnetNode.createNode('copytopoints')
    ctpNode.setInput(0, gridNode)
    ctpNode.setInput(1, randNode)
    return ctpNode

# This function creates "Attribute noise" node... set attrributes to "P"...center noise... element size to a value of 300 and amplitude to 200.. renames node to "noise_low_freq"
def create_attNoise(subnetNode, ctpNode):
    atrNoiseNode = subnetNode.createNode('attribnoise', "noise_low_freq")
    atrNoiseNode.parm('attribs').set('P')
    atrNoiseNode.parm('elementsize').setExpression('bbox(opinputpath(".",0), D_YMAX) + ch("../detailValue")')
    atrNoiseNode.parm('centernoise').set(1)
    atrNoiseNode.moveToGoodPosition()
    atrNoiseNode.setInput(0, ctpNode)
    return atrNoiseNode

# This function creates "Mountain" node... set height to value of 20...center noise... element size to a value of 20.. renames node to "noise_high_freq"
def create_mtNoise(subnetNode, atrNoiseNode):
    mtNoiseNode = subnetNode.createNode('mountain', "noise_high_freq")
    bbox = 'bbox(opinputpath(".",0), D_YMAX) + ch("../detailValue")'
    mtNoiseNode.parm('height').setExpression(bbox)
    mtNoiseNode.parm('centernoise').set(1)
    mtNoiseNode.parm('elementsize').setExpression(bbox)
    mtNoiseNode.moveToGoodPosition()
    mtNoiseNode.setInput(0, atrNoiseNode)
    return mtNoiseNode
# This function creates "group" node... set group name to "trim_area"..enable bounding objects
def create_group(subnetNode, mtNoiseNode, boundNode):
    groupNode = subnetNode.createNode('groupcreate', "trimArea_group")
    groupNode.parm('groupname').set("trim_area")
    groupNode.parm('grouptype').set("point")
    groupNode.parm('groupbase').set(0)
    groupNode.parm('groupbounding').set(1)
    groupNode.parm('boundtype').set("usebobject")
    groupNode.moveToGoodPosition()
    groupNode.setInput(0, mtNoiseNode)
    groupNode.setInput(1, boundNode)
    return groupNode

# Create blast node..set group to "trim_area"...enable delete non selected
def create_blast(subnetNode, groupNode):
    blastNode = subnetNode.createNode('blast')
    blastNode.parm('group').set("trim_area")
    blastNode.parm('negate').set(1)
    blastNode.moveToGoodPosition()
    blastNode.setInput(0, groupNode)
    return blastNode
# Create output node in subnet
def create_output(subnetNode, blastNode):
    outputNode = subnetNode.createNode('output')
    outputNode.moveToGoodPosition()
    outputNode.setInput(0, blastNode)
    return outputNode
## GEO LEVEL ##
# At geo1 level ("obj/geo1") create boolean shatter node. connect input 0 into box node and input 1 into subnet1
def create_boolean(geoNode,boxNode, cutterTool):
    booleanShatter = geoNode.createNode('boolean', "boolean_shattter")
    booleanShatter.parm('bsurface').set("surface")
    booleanShatter.parm('booleanop').set("shatter")
    booleanShatter.setInput(0, boxNode)
    booleanShatter.setInput(1, cutterTool)
    booleanShatter.moveToGoodPosition()
    booleanShatter.setDisplayFlag(True)
    return booleanShatter

# Create Assemble Node
def create_assemble(geoNode,booleanShatter):
    assembleNode = geoNode.createNode('assemble')
    assembleNode.setInput(0, booleanShatter)
    assembleNode.moveToGoodPosition()
    assembleNode.setDisplayFlag(True)
    return assembleNode
# Function to take user input when the tool is created for filepath
def userInput(geoNode):
    uInput = hou.ui.readInput("Insert a file path or leave empty to load test geo. Controls for this tool can be found on the node 'cutterTool'.", buttons=("OK", "Cancel"))
    pathInput = uInput[1]
    if pathInput == "":
        return create_boxGeo(geoNode)
    else:
        return create_fileGeo(geoNode, pathInput)
## Main function ##
def main():
    geoNode = create_geoNode()
    boxNode = userInput(geoNode)
    subnetNode = create_subnet(geoNode, boxNode)
    insideSubnet = inside_subnet()
    cutterTool = hou.node('/obj/fractured_geo/cutterTool/')
    #cutterParm = cutter_parm(cutterTool)
    booleanNode = create_boolean(geoNode,boxNode, cutterTool)
    create_assemble(geoNode,booleanNode)
    hou.node("/obj/fractured_geo/").layoutChildren()
main()