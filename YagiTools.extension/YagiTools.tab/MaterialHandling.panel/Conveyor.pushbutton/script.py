# coding: UTF-8

# Ref
import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('IronPython.Wpf')

# find the path of ui.xaml
from pyrevit import script
from pyrevit import UI
xamlfile = script.get_bundle_file('ui.xaml')

from rpw import revit, db, ui, DB, UI
import wpf
from System import *
from System.Windows import *

import math

#symbols = db.Collector(of_category="OST_Furniture", is_type=True)

uiapp = __revit__ # noqa F821
uidoc = uiapp.ActiveUIDocument
app = uiapp.Application
doc = uidoc.Document

straightConveyorName = "直線ローラーコンベヤ"
curveConveyorName = "曲線ローラーコンベヤ"

def getRotateAngle(direction):
    stdVec = DB.XYZ(0,-1,0)
    cross = stdVec.CrossProduct(direction)
    relAngle = stdVec.AngleTo(direction)
    if cross[2] > 0:
        return relAngle
    else:
        return 2*math.pi-relAngle


class RevitOperator():
    def __init__(self):
        #set default family type
        #families = DB.FilteredElementCollector(doc).WhereElementIsElementType().ToElements()
        families = db.Collector(of_category="OST_MechanicalEquipment",is_type=True)
        temp_count = 0
        for fam in families:
            if fam.FamilyName == straightConveyorName:
                self.straightConveyorFamilySymbol = fam
                temp_count+=1
                
            elif fam.FamilyName == curveConveyorName:
                self.curveConveyorFamilySymbol = fam
                temp_count+=1
        if temp_count == 0:
            UI.TaskDialog.Show("ファミリエラー","コンベヤファミリがプロジェクトにロードされていないため，実行できません。")
    
    #
    # Transaction control #
    #
    def startTransaction(self,tname):
        #Generate transaction and start it
        self.transaction = db.Transaction(tname)
        self.transaction.Start()

    def endTransaction(self):
        #End transaction
        self.transaction.Commit()

    #
    # Process #
    #
    def getStartDirectionLengthLevelFromLine(self,modelLine):
        # find start point XYZ
        location = modelLine.Location
        line = location.Curve
        start = line.Origin
        start = DB.XYZ(start.X,start.Y,0)

        #find direction XYZ
        direction = line.Direction

        # find length double
        length = line.Length

        # find level
        sketchPlane = modelLine.SketchPlane
        levs = db.Collector(of_category="OST_Levels",is_not_type=True)
        level = 0
        for lev in levs:
            if lev.Name == sketchPlane.Name:
                level = lev


        return start,direction,length,level
    #
    # Control Revit #
    #
    def generateStraightConveyorInstance(self, level, start_point, direction, length, height=700):
        #create a new straight conveyor
        newInst = doc.Create.NewFamilyInstance(start_point, self.straightConveyorFamilySymbol, level, DB.Structure.StructuralType.NonStructural)
        
        #set height and length of conveyor
        pl = newInst.LookupParameter("搬送長さ")
        pl.Set(length)
        ph = newInst.LookupParameter("搬送高さ")
        ph.Set(height)

        # rotate conveyor 
        p1 = DB.XYZ(start_point.X, start_point.Y, start_point.Z)
        p2 = DB.XYZ(start_point.X, start_point.Y, start_point.Z+1)
        axis = DB.Line.CreateBound(p1,p2)
        ang = getRotateAngle(direction)
        DB.ElementTransformUtils.RotateElement(doc, newInst.Id, axis, ang)


class AppWindow(Window):
    def __init__(self, selectedElements):
        wpf.LoadComponent(self, xamlfile)
        self.selectedElements = selectedElements
        self.revit_operator = RevitOperator()
        text = ""
        for elem in self.selectedElements:
            text += elem.Id.ToString()
            text += " / "
        self.selected_model_group.Text = text

    @property
    def i_conveyor_width(self):
        return self.conveyor_width.Text

    @property
    def i_conveyor_height(self):
        t_height = self.conveyor_height.Text
        return float(t_height)

    def genConv(self, sender, args):
        self.revit_operator.startTransaction("Create conveyor")

        for elem in self.selectedElements:
            st,dir,len,level = self.revit_operator.getStartDirectionLengthLevelFromLine(elem)
            self.revit_operator.generateStraightConveyorInstance(level, st, dir, len, self.i_conveyor_height/304.8)
        
        self.revit_operator.endTransaction()

class CustomISelectionFilter(UI.Selection.ISelectionFilter):
    def __init__(self, nom_class):
        self.nom_class = nom_class

    def AllowElement(self, e):
        if isinstance(e, self.nom_class):
            return True
        else:
            return False

def main():
    #モデル線分グループの選択
    selectedElementRefs = uidoc.Selection.PickObjects(
        UI.Selection.ObjectType.Element,
        CustomISelectionFilter(DB.ModelLine),
        "Pick ModelLines")
    
    selectedElements = map(lambda x:doc.GetElement(x.ElementId),selectedElementRefs)

    #windowの表示
    app_window = AppWindow(selectedElements)
    app_window.ShowDialog()

    


if __name__ == "__main__":
    main()


## memo ##
#　バグ

#ウィンドウを隠してPickさせるやつ↓
"""
def shell_pickobject():
    __window__.Hide() 
    elementReference = uidoc.Selection.PickObject(UI.Selection.ObjectType.Element,spaceFilter,"Select a space(room)") 
    __window__.Show()
    __window__.TopMost = True
    return elementReference
"""

#　やること
#タイプの既存判定
#タイプの新規作成
#曲線対応