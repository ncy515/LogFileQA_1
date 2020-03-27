import os
import glob
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from pylinac import PicketFence
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


from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/logfileQA', methods=['GET', 'POST'])
def logfileQA():
    return render_template('logfileQA')


if __name__ == "__main__":
    app.run(debug=True)
