
from PyQt5 import QtWidgets, QtGui, QtCore
from OpenGL.GL import *
from OpenGL.GL import shaders
import struct
import math
import sys


VERTEX_SHADER = """
#version 420

in vec3 position;

void main() {
	gl_Position = vec4(position, 1);
}
"""

FRAGMENT_SHADER = """
#version 420

#define PI 3.1415926538

uniform float baseHeight;
uniform float waveHeight1;
uniform float waveHeight2;
uniform float waveWidth1;
uniform float waveWidth2;
uniform float waveOffset1;
uniform float waveOffset2;
uniform float borderWidth;
uniform float borderGradient;
uniform vec3 backgroundColor;
uniform vec3 waveColor;
uniform vec3 borderColor;
out vec3 color;

vec3 merge(vec3 a, vec3 b, float v) {
	vec3 diff = b - a;
	return a + diff * v;
}

void main() {
	float x = gl_FragCoord.x;
	float y = gl_FragCoord.y;
	
	float height = baseHeight;
	height += (1 + sin(x * waveWidth1 + waveOffset1)) * waveHeight1;
	height += (1 + sin(x * waveWidth2 + waveOffset2)) * waveHeight2;
	if (y < height) {
		if (y > height - borderWidth) {
			color = borderColor;
		}
		else if (y > height - borderWidth - borderGradient) {
			float value = (y - (height - borderWidth - borderGradient)) / borderGradient;
			color = merge(waveColor, borderColor, value);
		}
		else {
			color = waveColor;
		}
	}
	else {
		color = backgroundColor;
	}
}
"""


class WaveConfig:
	def __init__(self):
		self.reset()
		
	def reset(self):
		self.baseHeight = 150
		
		self.waveHeight1 = 60
		self.waveHeight2 = 4
		self.waveWidth1 = 2.5
		self.waveWidth2 = 16
		self.waveSpeed1 = 2.6
		self.waveSpeed2 = 32
		
		self.borderWidth = 5
		self.borderGradient = 20
		
		self.backgroundColor = (0, 0, 0)
		self.waveColor = (1, 0, 0)
		self.borderColor = (1, .8, 0)


class RenderWidget(QtWidgets.QOpenGLWidget):
	def __init__(self, config):
		super().__init__()
		
		self.config = config
		
		self.waveOffset1 = 0
		self.waveOffset2 = 0
		
		self.timer = QtCore.QTimer(self)
		self.timer.setInterval(30)
		self.timer.timeout.connect(self.updateWaves)
		self.timer.start()
		
	def updateWaves(self):
		self.waveOffset1 += self.config.waveSpeed1
		self.waveOffset2 += self.config.waveSpeed2
		self.update()
	
	def initializeGL(self):
		data = struct.pack("18f",
			-1, -1, 0, -1, 1, 0, 1, -1, 0,
			1, 1, 0, 1, -1, 0, -1, 1, 0
		)
		self.buffer_id = glGenBuffers(1)
		glBindBuffer(GL_ARRAY_BUFFER, self.buffer_id)
		glBufferData(GL_ARRAY_BUFFER, len(data), data, GL_STATIC_DRAW)
		
		self.shader = shaders.compileProgram(
			shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER),
			shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
		)
		
		self.positionLoc = glGetAttribLocation(self.shader, "position")
		
		self.baseHeightLoc = glGetUniformLocation(self.shader, "baseHeight")
		
		self.waveHeightLoc1 = glGetUniformLocation(self.shader, "waveHeight1")
		self.waveHeightLoc2 = glGetUniformLocation(self.shader, "waveHeight2")
		self.waveWidthLoc1 = glGetUniformLocation(self.shader, "waveWidth1")
		self.waveWidthLoc2 = glGetUniformLocation(self.shader, "waveWidth2")
		self.waveOffsetLoc1 = glGetUniformLocation(self.shader, "waveOffset1")
		self.waveOffsetLoc2 = glGetUniformLocation(self.shader, "waveOffset2")
		
		self.borderWidthLoc = glGetUniformLocation(self.shader, "borderWidth")
		self.borderGradientLoc = glGetUniformLocation(self.shader, "borderGradient")
		
		self.backgroundColorLoc = glGetUniformLocation(self.shader, "backgroundColor")
		self.waveColorLoc = glGetUniformLocation(self.shader, "waveColor")
		self.borderColorLoc = glGetUniformLocation(self.shader, "borderColor")
	
	def paintGL(self):
		glBindBuffer(GL_ARRAY_BUFFER, self.buffer_id)
		with self.shader:
			glEnableVertexAttribArray(self.positionLoc)
			glVertexAttribPointer(self.positionLoc, 3, GL_FLOAT, False, 12, None)
			
			glUniform1f(self.baseHeightLoc, self.config.baseHeight)
			glUniform1f(self.waveHeightLoc1, self.config.waveHeight1)
			glUniform1f(self.waveHeightLoc2, self.config.waveHeight2)
			glUniform1f(self.waveWidthLoc1, self.config.waveWidth1 * math.pi / 360)
			glUniform1f(self.waveWidthLoc2, self.config.waveWidth2 * math.pi / 360)
			glUniform1f(self.borderWidthLoc, self.config.borderWidth)
			glUniform1f(self.borderGradientLoc, self.config.borderGradient)
			
			glUniform1f(self.waveOffsetLoc1, self.waveOffset1 * math.pi / 360)
			glUniform1f(self.waveOffsetLoc2, self.waveOffset2 * math.pi / 360)
			
			glUniform3f(self.backgroundColorLoc, *self.config.backgroundColor)
			glUniform3f(self.waveColorLoc, *self.config.waveColor)
			glUniform3f(self.borderColorLoc, *self.config.borderColor)
			
			glDrawArrays(GL_TRIANGLES, 0, 6)
			
			glDisableVertexAttribArray(self.positionLoc)
			
			
class ColorPickerButton(QtWidgets.QPushButton):

	valueChanged = QtCore.pyqtSignal(tuple)

	def __init__(self):
		super().__init__()
		self.clicked.connect(self.handleClicked)
		
	def setColor(self, r, g, b):
		self.color = QtGui.QColor(r * 255, g * 255, b * 255)
		self.setStyleSheet("background-color: %s" %self.color.name())
		
	def handleClicked(self):
		color = QtWidgets.QColorDialog.getColor(self.color)
		if color.isValid():
			r, g, b = color.redF(), color.greenF(), color.blueF()
			self.setColor(r, g, b)
			self.valueChanged.emit((r, g, b))
		
		
class SettingsWidget(QtWidgets.QWidget):
	
	valueChanged = QtCore.pyqtSignal()
	
	settings = [
		("Base height", "baseHeight", -100, 300, 1, 1),
		("Wave height 1", "waveHeight1", -200, 200, 1, 1),
		("Wave height 2", "waveHeight2", -200, 200, 1, 1),
		("Wave width 1", "waveWidth1", -30, 30, 2, 0.1),
		("Wave width 2", "waveWidth2", -30, 30, 2, 0.1),
		("Wave speed 1", "waveSpeed1", -100, 100, 1, 1),
		("Wave speed 2", "waveSpeed2", -100, 100, 1, 1),
		("Border width", "borderWidth", 0, 30, 1, 1),
		("Border gradient", "borderGradient", 0, 30, 1, 1)
	]
	
	colors = [
		("Background color", "backgroundColor"),
		("Wave color", "waveColor"),
		("Border color", "borderColor")
	]
	
	def __init__(self, config):
		super().__init__()
		
		self.config = config
		
		self.layout = QtWidgets.QFormLayout(self)
		
		for setting in self.settings:
			widget = QtWidgets.QDoubleSpinBox()
			widget.setRange(setting[2], setting[3])
			widget.setDecimals(setting[4])
			widget.setSingleStep(setting[5])
			widget.setValue(getattr(config, setting[1]))
			widget.valueChanged.connect(
				lambda v, s=setting: self.changeValue(s[1], v)
			)
			self.layout.addRow(setting[0] + ":", widget)
		
		for setting in self.colors:
			widget = ColorPickerButton()
			widget.setColor(*getattr(config, setting[1]))
			widget.valueChanged.connect(
				lambda color, s=setting: self.changeColor(s[1], color)
			)
			self.layout.addRow(setting[0] + ":", widget)
		
	def changeValue(self, name, value):
		setattr(self.config, name, value)
		self.valueChanged.emit()
		
	def changeColor(self, name, color):
		setattr(self.config, name, color)
		self.valueChanged.emit()


class MainWindow(QtWidgets.QMainWindow):
	def __init__(self):
		super().__init__()
		self.config = WaveConfig()
		
		self.widget = RenderWidget(self.config)
		self.setCentralWidget(self.widget)
		
		self.settings = SettingsWidget(self.config)
		self.settings.valueChanged.connect(self.widget.update)
		
		self.dock = QtWidgets.QDockWidget("Settings")
		self.dock.setWidget(self.settings)
		self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dock)
		
		self.setWindowTitle("NSMBU Wave Simulator")
		self.resize(800, 600)
		
		
if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	window = MainWindow()
	window.show()
	app.exec()
