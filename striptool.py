import sys, time
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import numpy as np
import threading
from threading import Thread, Event, Timer
from PyQt4.QtCore import QObject, pyqtSignal, pyqtSlot
import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)

class RepeatedTimer:

    """Repeat `function` every `interval` seconds."""

    def __init__(self, interval, function, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.start = time.time()
        self.event = Event()
        self.thread = threading.Thread(target=self._target)
        self.thread.daemon = True
        self.thread.start()

    def _target(self):
        while not self.event.wait(self._time):
            self.function(*self.args, **self.kwargs)

    @property
    def _time(self):
        if (self.interval) - ((time.time() - self.start) % self.interval) < 0.0001:
            return self.interval
        else:
            return (self.interval) - ((time.time() - self.start) % self.interval)

    def stop(self):
        self.event.set()
        self.thread.join()

class createSignalTimer(QObject):
    ''' Represents a signal; when started it
        emits a signal that indicates that it was updated. '''
    updated = pyqtSignal('PyQt_PyObject')

    def __init__(self, function, *args):
        # Initialize the signal as a QObject
        QObject.__init__(self)
        self.function = function
        self.args = args

    def startTimer(self, interval=1):
        self.timer = RepeatedTimer(interval, self.update)

    def update(self):
        ''' call signal generating Function '''
        val = self.function(*self.args)
        self.updated.emit(val)

class createRecord(QObject):
    ''' Emits an updated signal when the record is updated'''
    updated = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        # Initialize the PunchingBag as a QObject
        QObject.__init__(self)
        self.record = []

    def timeFilter(self, list, time):
        for x in reversed(list):
            if x[0] > (time - self.signalLength):
                yield x
            else:
                break

    def filterRecord(self, time):
         return list(reversed(list(self.timeFilter(self.record, time.time()))))

    def appendToRecord(self, value):
        self.record.append(value)
        self.updated.emit(self.record)

    def getRecord(self):
        return self.record

    @pyqtSlot('PyQt_PyObject')
    def update(self, value):
        self.appendToRecord(value)

class createSignalRecord(QObject):

    newData = pyqtSignal('PyQt_PyObject')

    def __init__(self, timer, function, *args):
        # Initialize the PunchingBag as a QObject
        QObject.__init__(self)
        self.signal = createSignalTimer(function, *args)
        self.record = createRecord()
        self.signal.updated.connect(self.record.update)
        self.signal.startTimer(timer)
        self.record.updated.connect(self.printSignal)

    def setInterval(self, newinterval):
        self.signal.timer.interval = newinterval

    def getRecord(self):
        return self.record.getRecord()

    @pyqtSlot('PyQt_PyObject')
    def printSignal(self, value):
        self.newData.emit(value)

class linearPlot(QWidget):
    def __init__(self):
        QWidget.__init__(self)

    def createLinearPlot(self):
        self.linearPlotWidget = pg.GraphicsLayoutWidget()
        self.linearPlot = self.linearPlotWidget.addPlot(row=0, column=0)
        self.linearPlot.showGrid(x=True, y=True)
        # self.curve = self.linearPlot.plot()
        # print self.curve
        return self.linearPlotWidget

    def addCurve(self):
        return self.curve(self.linearPlot)

    class curve(QObject):
        def __init__(self, linearPlot):
            QObject.__init__(self)
            self.curve = linearPlot.plot()

        def setData(self, x, y):
            currenttime = time.time()
            self.curve.setData({'x': x-currenttime, 'y': y})

        def setData(self, data, pen='r'):
            currenttime = time.time()
            x,y = np.transpose(data)
            self.curve.setData({'x': x-currenttime, 'y': y}, pen=pen)

        def updatePlot(self, record, pen='r'):
            self.setData(record.getRecord(), pen)

    def show(self):
        self.linearPlotWidget.show()

class plotTabs(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.tabs = QtGui.QTabWidget()
        # self.tabs.currentChanged.connect(self.updatePlot)
        # self.tabs.currentChanged.connect(self.updateTabs)

    def createPlotTabs(self, linear=True, histogram=True, FFT=True):
        if linear:
            self.tabs.addTab(linearPlot().createLinearPlot(),"Linear Plot")
        if histogram:
            self.tabs.addTab(self.histogramPlotTab(),"Histogram Plot")
        if FFT:
            self.tabs.addTab(self.FFTPlotTab(),"Spectrum Plot")
        return self.tabs

    def histogramPlotTab(self):
        self.tabHistogramPlot = pg.GraphicsLayoutWidget()
        self.HistogramPlot = self.tabHistogramPlot.addPlot(row=0, column=0)
        self.HistogramPlot.showGrid(x=True, y=True)
        return self.tabHistogramPlot

    def FFTPlotTab(self):
        self.tabFFTPlot = pg.GraphicsLayoutWidget()
        self.FFTPlot = self.tabFFTPlot.addPlot(row=0, column=0)
        self.FFTPlot.updateSpectrumMode(True)
        self.FFTPlot.showGrid(x=True, y=True)
        return self.tabFFTPlot

def createRandomSignal():
    signalValue = np.random.normal()
    return [time.time(), signalValue]

def main():
    pg.setConfigOptions(antialias=True)
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    signalrecord1 = createSignalRecord(0.01, createRandomSignal)
    signalrecord2 = createSignalRecord(0.01, createRandomSignal)
    signalrecord1.setInterval(0.1)
    app = QApplication(sys.argv)
    lay = QtGui.QGridLayout()
    plotWidget = linearPlot()
    plot1 = plotWidget.createLinearPlot()
    curve1 = plotWidget.addCurve()
    curve2 = plotWidget.addCurve()
    lay.addWidget(plotWidget,0, 1)
    plotThread = QTimer()
    plotThread.timeout.connect(lambda: curve1.updatePlot(signalrecord1, pen='r'))
    plotThread.timeout.connect(lambda: curve2.updatePlot(signalrecord2, pen='g'))
    plotThread.start(1000)
    plotWidget.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
   main()
