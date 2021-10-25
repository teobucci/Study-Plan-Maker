import sys
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QTextEdit, QGridLayout, QApplication)
import pandas as pd
import numpy as np
import PyQt5 
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QGroupBox, QHBoxLayout, QMainWindow, QApplication, QLineEdit, QFileDialog,  QTableWidget,QTableWidgetItem, QTableView, QStyledItemDelegate
from PyQt5 import QtCore, QtGui, QtWidgets   
import os
from PyQt5.QtWidgets import (QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QApplication)
from PyQt5.QtGui import QIcon
import re



def dataframe():
    xls = pd.ExcelFile(r'C:\Users\filip\OneDrive\Desktop\Universimize\Scripts\Max_data.xlsx')
    df = xls.parse(xls.sheet_names[0])
    df = df.astype({"Rating": int})
    return df

class Delegate(QtWidgets.QItemDelegate):
    def __init__(self, owner, choices):
        super().__init__(owner)
        self.items = choices

    def createEditor(self, parent, option, index):
        self.editor = QtWidgets.QComboBox(parent)
        self.editor.currentIndexChanged.connect(self.commit_editor)
        self.editor.addItems(self.items)
        return self.editor    

    def paint(self, painter, option, index):
        value = index.data(QtCore.Qt.DisplayRole)
        style = QtWidgets.QApplication.style()
        opt = QtWidgets.QStyleOptionComboBox()
        opt.text = str(value)
        opt.rect = option.rect
        style.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, opt, painter)
        QtWidgets.QItemDelegate.paint(self, painter, option, index)

    def commit_editor(self):      ####test
        editor = self.sender()
        self.commitData.emit(editor)


    def setEditorData(self, editor, index):
        value = index.data(QtCore.Qt.DisplayRole)
        num = self.items.index(value)
        editor.setCurrentIndex(num)

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, data, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._data.columns[col]
        return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        self._data.iloc[index.row(), index.column()] = value
        self.dataChanged.emit(index, index, (QtCore.Qt.DisplayRole, ))
        return True 

class MyWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setGeometry(400, 400 ,900, 800)
        self.setWindowTitle('Ottimizzatore piano di studi')
        self.initUI()
        self.new_df = None


    def show_data(self):
        choices = ['0', '1', '2', '3', '4', '5']
        self.model = PandasModel(dataframe())
        self.table_data.setModel(self.model)                            
        self.table_data.setItemDelegateForColumn(6, Delegate(self,choices))
        ##make combo boxes editable with a single-click:
        for row in range(self.model.rowCount()):  #self.model==table
            self.table_data.openPersistentEditor(self.model.index(row, 6))

    #def print_data(self):
    #    print(self.table_data.model()._data)
    
    def dataframe_generation_from_table(self,table):
        table = self.model
        number_of_rows = table.rowCount()
        number_of_columns = table.columnCount()

        tmp_df = pd.DataFrame( 
                    columns=['Denominazione', 'Codice', 'Sem', 'CFU', 'Gruppo', 'idgruppo', 'Rating'], # Fill columnets
                    index=range(number_of_rows) # Fill rows
                    ) 

        for i in range(number_of_rows):
            for j in range(number_of_columns):
                tmp_df.iloc[i, j] = table._data.iloc[i, j]

        self.new_df = tmp_df

    def initUI(self):

        welcom = QLabel('Seleziona un grado di interesse per gli esami che vuoi considerare')

        #self.btn_print_data = QPushButton('print data')
        #self.btn_print_data.clicked.connect(self.print_data)  ##test

        self.btn_show_table = QPushButton('Non faccio niente')
        self.btn_show_table.clicked.connect(self.dataframe_generation_from_table)
        #self.btn_show_table.clicked.connect(self.show_data)

        self.table_data = QTableView()
        #self.table_result = QTableView() 
        self.show_data()

        hbox1 = QHBoxLayout()
        hbox1.addWidget(welcom)


        ###vbox2 = QVBoxLayout()
        ###vbox2.addWidget(self.btn_show_table)
        #vbox2.addWidget(self.btn_print_data) ####test

        vbox3 = QVBoxLayout()
        vbox3.addWidget(self.table_data)
        #vbox3.addWidget(self.table_result)

        hbox2 = QHBoxLayout()
        #hbox2.addLayout(vbox2)
        hbox2.addLayout(vbox3)

        hbox3 = QHBoxLayout() ##oki
        hbox3.addWidget(self.btn_show_table)

        vbox1 = QVBoxLayout()
        vbox1.addLayout(hbox1)
        vbox1.addLayout(hbox2)
        vbox1.addLayout(hbox3)

        self.setLayout(vbox1)
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWindow()
    #sys.exit(app.exec_())
    app.exec_()
    
print (ex.new_df)
