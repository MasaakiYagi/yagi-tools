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

#symbols = db.Collector(of_category="OST_Furniture", is_type=True)

uiapp = __revit__ # noqa F821
uidoc = uiapp.ActiveUIDocument
app = uiapp.Application
doc = uidoc.Document

straightConveyorName = "直線ローラーコンベヤ"
curveConveyorName = "曲線ローラーコンベヤ"

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
        UI.TaskDialog.Show("temp","{}".format(temp_count))

    def startTransaction(self,tname):
        #Generate transaction and start it
        self.transaction = db.Transaction(tname)
        self.transaction.Start()

    def endTransaction(self):
        #End transaction
        self.transaction.Commit()

    def generateStraightConveyorInstance(self, lev, start_point, end_point, height=700):
        #create a new straight conveyor
        direction = end_point-start_point
        newInst = doc.Create.NewFamilyInstance(start_point, self.straightConveyorFamilySymbol, lev, DB.Structure.StructuralType.NonStructural)
        
        #set height and length of conveyor



class AppWindow(Window):
    def __init__(self):
        wpf.LoadComponent(self, xamlfile)
        self.revit_operator = RevitOperator()

    @property
    def i_conveyor_width(self):
        return self.conveyor_width.Text

    def genConv(self, sender, args):
        lev =doc.GetElement("49173")
        self.revit_operator.startTransaction("Create conveyor")
        self.revit_operator.generateStraightConveyorInstance(lev,DB.XYZ(0,0,0), DB.XYZ(5,0,0))
        self.revit_operator.endTransaction()


def main():
    #windowの表示
    app_window = AppWindow()
    app_window.ShowDialog()


if __name__ == "__main__":
    main()