from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSql import *
from PyQt5 import uic
from PIL import Image
import numpy
import cv2
import sys
import os

class MainWindow(QMainWindow):
	cascadePath = "haarcascade_frontalface_default.xml"

	def __init__(self, parent=None):
		QMainWindow.__init__(self, parent)
		uic.loadUi("mainwindow.ui", self)
		self.setup()
		self.makeConnections()

	def setup(self):
		self.buscarModel = self.makeBuscarModel()
		self.eliminarModel = self.makeEliminarModel()
		self.modificarModel = self.makeModificarModel()
		self.modificarTimer = self.makeModificarTimer()
		self.entrenamiento_progressbar.setRange(0, 100)
		self.entrenamiento_progressbar.setValue(0)
		self.fillNombreCombobox()

	def makeConnections(self):
		self.actionSalir.triggered.connect(self.close)
		self.agregar_listo_button.clicked.connect(self.onAgregar_listo_button_clicked)
		self.buscar_nombre_lineedit.textEdited.connect(self.onBuscar_nombre_lineedit_textEdited)
		self.eliminar_tableview.clicked.connect(self.onEliminar_tableview_clicked)
		self.modificarModel.beforeUpdate.connect(self.onModificarModel_beforeUpdate)
		self.modificarTimer.timeout.connect(self.onModificarTimer_timeout)
		self.iniciar_capturas_button.clicked.connect(self.onIniciar_capturas_button_clicked)
		self.iniciar_entrenamiento_button.clicked.connect(self.onIniciar_entrenamiento_button_clicked)
		self.iniciar_reconocimiento_button.clicked.connect(self.onIniciar_reconocimiento_button_clicked)

	def makeModificarTimer(self):
		timer = QTimer(self)
		timer.setInterval(1000)
		timer.setSingleShot(True)
		return timer

	def makeBuscarModel(self):
		model = QSqlQueryModel(self)
		model.setQuery("select * from persona")
		self.buscar_tableview.setModel(model)
		return model

	def makeEliminarModel(self):
		model = QSqlTableModel(self)
		model.setTable("persona")
		model.select()
		self.eliminar_tableview.setModel(model)
		self.eliminar_tableview.setEditTriggers(QTableView.NoEditTriggers)
		self.eliminar_tableview.setSelectionBehavior(QTableView.SelectRows)
		return model

	def makeModificarModel(self):
		model = QSqlTableModel(self)
		model.setTable("persona")
		model.select()
		self.modificar_tableview.setModel(model)
		return model

	def onIniciar_capturas_button_clicked(self):
		if self.nombre_combobox.count() == 0:
			return
		cap = cv2.VideoCapture(0)
		faceDetector = cv2.CascadeClassifier(self.cascadePath)
		faceId = self.nombre_combobox.currentData()
		count = 0
		directory = os.path.dirname("dataset/")
		if not os.path.exists(directory):
			os.makedirs(directory)
		running = True
		while running:
			_, frame = cap.read()
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			faces = faceDetector.detectMultiScale(gray, 1.3, 5)
			for (x, y, w, h) in faces:
				cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0), 2)
				count += 1
				cv2.imwrite("dataset/User." + str(faceId) + '.' + str(count) + ".jpg", gray[y:y+h, x:x+w])
				cv2.imshow("frame: use (Q) para salir", frame)
			if (cv2.waitKey(100) & 0xFF == ord("q")):
				running = False
			elif count > 100:
				running = False
		cap.release()
		cv2.destroyAllWindows()

	def onIniciar_entrenamiento_button_clicked(self):
		recognizer = cv2.face.LBPHFaceRecognizer_create()
		detector = cv2.CascadeClassifier(self.cascadePath)
		path = "dataset"
		imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
		faceSamples = []
		ids = []
		self.entrenamiento_progressbar.setRange(0, len(imagePaths))
		ix = 0
		for imagePath in imagePaths:
			imgPIL = Image.open(imagePath).convert("L")
			imgNumpy = numpy.array(imgPIL, "uint8")
			id = int(os.path.split(imagePath)[-1].split(".")[1])
			faces = detector.detectMultiScale(imgNumpy)
			for (x, y, w, h) in faces:
				faceSamples.append(imgNumpy[y:y+h, x:x+w])
				ids.append(id)
			ix += 1
			self.entrenamiento_progressbar.setValue(ix)
		recognizer.train(faceSamples, numpy.array(ids))
		path = "trainer/"
		directory = os.path.dirname(path)
		if not os.path.exists(directory):
			os.makedirs(directory)
		recognizer.save("trainer/trainer.yml")
		QMessageBox.information(self, "OK", "Entrenamiento terminado")
		self.entrenamiento_progressbar.setValue(0)

	def onIniciar_reconocimiento_button_clicked(self):
		recognizer = cv2.face.LBPHFaceRecognizer_create()
		path = "trainer/"
		directory = os.path.dirname(path)
		if not os.path.exists(directory):
			os.makedirs(directory)
		recognizer.read("trainer/trainer.yml")
		faceCascade = cv2.CascadeClassifier(self.cascadePath)
		font = cv2.FONT_HERSHEY_SIMPLEX
		cap = cv2.VideoCapture(0)
		running = True
		while running:
			_, frame = cap.read()
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			faces = faceCascade.detectMultiScale(gray, 1.2, 5)
			for (x, y, w, h) in faces:
				cv2.rectangle(frame, (x-20,y-20), (x+w+20,y+h+20), (0,255,0), 4)
				id, confidence = recognizer.predict(gray[y:y+h, x:x+w])
				name = self.getNameById(id)
				cv2.rectangle(frame, (x-22,y-90), (x+w+22,y-22), (0,255,0), -1)
				cv2.putText(frame, name, (x,y-40), font, 1, (255,255,255), 3)
			cv2.imshow("frame: cierra con (Q)", frame)
			if cv2.waitKey(10) & 0xFF == ord("q"):
				running = False
		cap.release()
		cv2.destroyAllWindows()

	def onModificarTimer_timeout(self):
		self.refreshModels()

	def onModificarModel_beforeUpdate(self, row, record):
		self.modificarTimer.start()

	def onEliminar_tableview_clicked(self, idx):
		if QMessageBox.question(self, "Eliminar", "¿Está seguro?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
			row = idx.row()
			self.eliminarModel.removeRow(row)
			self.refreshModels()

	def onBuscar_nombre_lineedit_textEdited(self, txt):
		self.buscarModel.setQuery("select * from persona where nombre like '%" + txt + "%'")

	def onAgregar_listo_button_clicked(self):
		nombre = self.agregar_nombre_lineedit.text()
		if nombre == "":
			QMessageBox.critical(self, "Error", "No hay nombre")
		else:
			q = QSqlQuery()
			if q.prepare("insert into persona(nombre) values (?)"):
				q.addBindValue(nombre)
				if q.exec():
					if QMessageBox.question(self, "OK", "Listo, ¿Desea borrar los campos?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
						self.agregar_nombre_lineedit.clear()
					self.refreshModels()
				else:
					print(q.lastError().text())
			else:
				print(q.lastError().text())

	def refreshModels(self):
		self.buscarModel.setQuery("select * from persona")
		self.eliminarModel.select()
		self.modificarModel.select()
		self.fillNombreCombobox()

	def fillNombreCombobox(self):
		self.nombre_combobox.clear()
		q = QSqlQuery()
		if q.prepare("select id, nombre from persona"):
			if q.exec():
				while q.next():
					id = q.value("id")
					nombre = q.value("nombre")
					self.nombre_combobox.addItem(nombre, id)
			else:
				print(q.lastError().text())
		else:
			print(q.lastError.text())

	def getNameById(self, id):
		q = QSqlQuery()
		if q.prepare("select nombre from persona where id like " + str(id)):
			if q.exec():
				if q.next():
					return q.value("nombre")
				else:
					print("error")
			else:
				print(q.lastError().text())
		else:
			print(q.lastError().text())