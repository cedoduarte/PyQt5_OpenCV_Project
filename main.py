from PyQt5.QtWidgets import QApplication
from PyQt5.QtSql import *
from mainwindow import MainWindow
import sys

def prepareDatabase():
	db = QSqlDatabase.addDatabase("QSQLITE")
	db.setDatabaseName("data.db")
	if db.open():
		q = QSqlQuery()
		if q.prepare("create table if not exists persona(id integer primary key autoincrement not null, nombre text not null)"):
			if q.exec():
				print("tabla persona creada")
			else:
				print(q.lastError().text())
		else:
			print(q.lastError().text())
	else:
		print(db.lastError().text())

def start():
	app = QApplication(sys.argv)
	app.setStyle("fusion")
	w = MainWindow()
	w.show()
	sys.exit(app.exec_())

if __name__ == "__main__":
	prepareDatabase()
	start()