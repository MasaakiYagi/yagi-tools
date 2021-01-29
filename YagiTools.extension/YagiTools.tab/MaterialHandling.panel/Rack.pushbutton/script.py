# -*- coding: utf-8 -*-

# Ref
import clr
clr.AddReference("System")
clr.AddReference('System.Windows.Forms')
clr.AddReference('IronPython.Wpf')

from pyrevit import script
from pyrevit import UI
xamlfile = script.get_bundle_file('ui_rack.xaml')

from rpw import revit, db, ui, DB, UI
import wpf
from System import *
from System.Windows import *

import pickle
import os
from tempfile import gettempdir

uiapp = __revit__ 
uidoc = uiapp.ActiveUIDocument
app = uiapp.Application
doc = uidoc.Document

class RevitOperator():
    def __init__(self):
        #set default family type
        families = db.Collector(of_category="OST_GenericModel",is_type=True)
        types = []
        type_count = 0
        for fam in families:
            if fam.FamilyName == "重量ラック(単列)":
                types.append(fam)
                type_count += 1
            
        if type_count == 0:
            UI.TaskDialog.Show("ファミリエラー","重量ラックファミリがプロジェクトにロードされていないため，実行できません。")
        else:
            self.types = types
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
    def setRoom(self,room):
        self.room = room

        #get boundary segments
        boptions = DB.SpatialElementBoundaryOptions()
        boundsegs = self.room.GetBoundarySegments(boptions)
        boundcurves = []
        
        for bound in boundsegs:
            crvs = []
            for seg in bound:
                crv = seg.GetCurve()
                crvs.append(crv)
            boundcurves.append(crvs)

        self.boundcurves = boundcurves




class AppWindow(Window):
    def __init__(self):
        wpf.LoadComponent(self, xamlfile)
        self.revit_operator = RevitOperator()
        for type in self.revit_operator.types:
            typeName = DB.Element.Name.GetValue(type)
            self.type_list.Items.Add(typeName)

    def pickRoom(self, sender, args):
        self.Hide() 
        selected_room_reference = uidoc.Selection.PickObject(
                UI.Selection.ObjectType.Element,
                CustomISelectionFilter("部屋"),
                "Select Room")
        #selected_room = doc.GetElement(selected_room_reference.ElementId)
        
        #self.revit_operator.setRoom(selected_room)
        #self.selected_room_text.Text = self.revit_operator.room.LookupParameter("名前").AsString()
        self.Show()
        self.TopMost = True

    def genRack(self, sender, args):
        self.revit_operator.startTransaction("Create conveyor")

        for elem in self.selectedElements:
            st,dir,len,level = self.revit_operator.getStartDirectionLengthLevelFromLine(elem)
            self.revit_operator.generateStraightConveyorInstance(level, st, dir, len, self.i_conveyor_height/304.8)
        
        self.revit_operator.endTransaction()

class CustomISelectionFilter(UI.Selection.ISelectionFilter):
    def __init__(self, category_name):
        self.category_name = category_name

    def AllowElement(self, e):
        if e.Category.Name == self.category_name:
            return True
        else:
            return False

    def AllowReference(self, ref, point):
        return True


def main():
    #windowの表示
    app_window = AppWindow()
    app_window.ShowDialog()



if __name__ == "__main__":
    main()
