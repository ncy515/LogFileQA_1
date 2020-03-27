import os
import glob
from flask import Flask, flash, request, redirect, url_for, render_template, send_file
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
from LogFileQA import LogFileQA
from WLT import WLT
from MLC_QA import MLC_QA

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


###################################################
# Patient Specific QA

@app.route('/upload_file', methods=['GET', 'POST'])
def upload_file():

    app.config['MONGO_URI'] = "mongodb://localhost:27017/QA"
    mongo = PyMongo(app)
    client = MongoClient('localhost', 27017)
    db = client.QA

    UPLOAD_FOLDER = 'D:\\Dicom Files\\Dynalog'
    if request.method == 'POST':
        DIR_name = request.form.get('DIR_name')
        print(DIR_name)
        # path_name = os.path.join(UPLOAD_FOLDER, DIR_name)
        path_name = DIR_name
        print(path_name)
        # mlog = MachineLogs(path_name)
        DtoA = float(request.form.get('DtoA'))
        print(DtoA)
        dosetoA = float(request.form.get('dosetoA'))
        print(dosetoA)
        Res = float(request.form.get('Res'))
        print(Res)

        qa = LogFileQA(path_name, DtoA=DtoA, dosetoA=dosetoA, Res=Res)
        resultfilename = qa.IMRT_QA()

        return send_file(resultfilename)
        # return mongo.send_file(str1)

    return '''

    <!doctype html>
    <title>Dynalog File IMRT/VMAT QA</title>
    <form method=post enctype=multipart/form-data>
        <h3>Enter Directory Name of Dynalog and DICOM-RT File: </h3>
        <input placeholder="Enter Directory Name" name="DIR_name" type="text" required size="35"> <br>
        <hr>
        <h3>Enter Gamma Analysis Criteria: </h3>
        <input placeholder="Distance to Agreement/mm" name="DtoA" type="number" step = 0.001 required size="35"> <br>
        <input placeholder="Dose to Agreement/%" name="dosetoA" type="number" step = 0.001 required size="35"> <br>
        <input placeholder="Resolution/mm" name="Res" type="number" step = 0.001 required size="35"> <br>
        <hr>
        <br>
        <input type="submit" value="Perform Patient Specific QA" width="35" height="10">
    </form>
    '''

###################################################
# Picket Fence QA

###################################################
# Picket Fence QA

def allowed_file(filename):
    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'dcm'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/picketfence', methods=['GET', 'POST'])
def picketfence():
    if request.method == 'POST':
        DIR_name = str(request.form.get('DIR_name'))
        UPLOAD_FOLDER = DIR_name
        LINAC_name = str(request.form.get('LINAC_name'))

        print(UPLOAD_FOLDER)
        print(LINAC_name)
        qa = MLC_QA(UPLOAD_FOLDER, LINAC_name)
        reportname = qa.QA_Report()
        reportname = os.path.join(UPLOAD_FOLDER, reportname)

        return send_file(reportname)

    # qa = MLC_QA(UPLOAD_FOLDER, LINAC_name)
    # reportname = qa.QA_Report()
    # reportname = os.path.join(UPLOAD_FOLDER, reportname)
    #
    # return send_file(reportname)

    return '''

       <!doctype html>
       <title>Picket Fence Test</title>
       <form method=post enctype=multipart/form-data>
           <h3>Enter LINAC Name: </h3>
           <input placeholder="Enter LINAC Name" name="LINAC_name" type="text" required size="35"> <br>
           <h3>Enter Picket Fence Image Directory Name: </h3>
           <input placeholder="Enter Directory Name" name="DIR_name" type="text" required size="35"> <br>
           <hr>
           <br>
           <input type="submit" value="Perform Picket Fence Test" width="35" height="10">
       </form>
     
     '''


###################################################
#Winston Lutz Test

@app.route('/wltest', methods=['GET', 'POST'])
def wltest():
    # app.config['MONGO_URI'] = "mongodb://localhost:27017/QA"
    # UPLOAD_FOLDER = 'D:\\Dicom Files\\WLImages'
    # mongo = PyMongo(app)
    # client = MongoClient('localhost', 27017)
    # db = client.WinstonLutzTest

    if request.method == 'POST':
        DIR_name = request.form.get('DIR_name')
        LINAC_name = request.form.get('LINAC_name')
        path_name = DIR_name
        print(path_name)
        print(LINAC_name)

        wlt = WLT(path_name, LINAC_name)
        reportname = wlt.QA_Report()
        reportname = os.path.join(DIR_name, reportname)
        print(reportname)

        return send_file(reportname)

    return '''

    <!doctype html>
    <title>LINAC Winston Lutz Test</title>
    <form method=post enctype=multipart/form-data>
        <h3>Enter LINAC Name: </h3>
        <input placeholder="Enter LINAC Name" name="LINAC_name" type="text" required size="35"> <br>
        <h3>Enter Winston Lutz Image Directory Name: </h3>
        <input placeholder="Enter Directory Name" name="DIR_name" type="text" required size="35"> <br>
        <hr>
        <br>
        <input type="submit" value="Perform Winston Lutz Test" width="35" height="10">
    </form>
    
    '''


if __name__ == "__main__":
    app.run(debug=True)