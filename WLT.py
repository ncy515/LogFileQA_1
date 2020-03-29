import os
import glob
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from pylinac import PicketFence, WinstonLutz
from pylinac import MachineLogs, TrajectoryLog
from flask_pymongo import PyMongo
from datetime import datetime
from matplotlib import pyplot as plt
import shutil
import gridfs
from pymongo import MongoClient
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, PageBreak
from reportlab.lib.units import mm, inch
import numpy as np
import pydicom

class WLT:
    def __init__(self, direct_name, LINAC):
        self.direct_name = direct_name
        self.LINAC = LINAC

    def QA_Report(self):
        # app.config['MONGO_URI'] = "mongodb://localhost:27017/WinstonLutzTest"
        # mongo = PyMongo(app)

        client = MongoClient('localhost', 27017)
        db = client.QA
        fs = gridfs.GridFS(db)

        init_dir = os.getcwd()

        os.chdir(self.direct_name)
        fnames = glob.glob('*.dcm')

        position = ['Gantry270Couch0.dcm', 'Gantry0Couch0.dcm', 'Gantry90Couch0.dcm', 'Gantry180Couch0.dcm',
                    'Gantry0Couch90.dcm', 'Gantry0Couch45.dcm', 'Gantry0Couch315.dcm', 'Gantry0Couch270.dcm']

        for i, fname in enumerate(fnames):
            name = position[i]
            shutil.move(fname, name)

        wl = WinstonLutz(self.direct_name, use_filenames=True)
        # wl.plot_summary()
        wl.save_summary('summary.png')
        plt.close()

        r = wl.results()
        rr = r.split('\n')
        wltreportname = 'WLT'+ datetime.now().strftime('%d%m%Y') + '.pdf'

        # c = canvas.Canvas('WLT'+ datetime.now().strftime('%d%m%Y') + '.pdf')
        c = canvas.Canvas(wltreportname)

        c.setLineWidth(0.3)
        c.drawImage(init_dir+"\\images\\qmh_logo.png", 50, 750, 90, 80)
        c.drawString(150, 780, 'Department of Clinical Oncology Medical Physics Unit')
        c.drawString(50, 700, 'Date: ' + datetime.now().strftime('%d-%m-%Y'))
        c.drawString(50, 685, 'LINAC: ' + self.LINAC)
        y = 670
        for line in rr:
            c.drawString(50, y, line)
            y -= 15
        c.drawImage('summary.png', 30, 20, 7 * inch, 5 * inch)
        c.save()

        fileID = fs.put(open(wltreportname, 'rb'))

        db.WLTest.insert_one({'LINAC': self.LINAC,
                              'QA Date': datetime.now().strftime('%d-%m-%Y'),
                              'Gantry Isocenter Size': str(('%.4f' % wl.gantry_iso_size)),
                              'Couch Isocenter Size': str(('%.4f' % wl.couch_iso_size)),
                              'PV Isocenter Size': str(('%.4f' % wl.collimator_iso_size)),
                              'reportpdf': wltreportname})

        return wltreportname

    def Iso_Dev(self):
        wl = WinstonLutz(self.direct_name, use_filenames=True)
        g_iso = wl.gantry_iso_size
        coll_iso = wl.collimator_iso_size
        couch_iso = wl.couch_iso_size
        epid_rms = wl.cax2epid_distance()

        return(g_iso, coll_iso, couch_iso, epid_rms)
