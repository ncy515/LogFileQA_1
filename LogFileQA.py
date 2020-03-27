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

class LogFileQA:
    def __init__(self, path_name, DtoA: float = 0.05, dosetoA: float = 0.05, Res: float = 0.5):
        self.path_name = path_name
        self.DtoA = DtoA
        self.dosetoA = dosetoA
        self.Res = Res

    def IMRT_QA(self):
        global aa
        global gg
        global dd
        global ee
        global n1
        global n2
        global n3
        global mlog
        # global DtoA, dosetoA, Res
        global p_pcnt, fail_list, fail_str, p_str
        global qa_date
        global str1

        # app.config['MONGO_URI'] = "mongodb://localhost:27017/QA"
        # mongo = PyMongo(app)
        client = MongoClient('localhost', 27017)
        db = client.QA
        fs = gridfs.GridFS(db)

        os.chdir(self.path_name)

        if len(glob.glob('*.bin')) > 0:
            mlog = []
            fname = glob.glob('*.bin')
            for i, name in enumerate(fname):
                mlog.append(TrajectoryLog(name))
            n1 = len(mlog)
            qa_date = fname[0][-18:-10]

        else:
            fname = glob.glob('*.dlg')
            qa_date = fname[0][1:9]
            mlog = MachineLogs(self.path_name)
            n1 = mlog.num_dlogs

        (n2, n3) = mlog[0].fluence.actual.calc_map().shape

        aa = ee = dd = np.zeros((n1, n2, n3))
        # add difference map

        (gn2, gn3) = mlog[0].fluence.gamma.calc_map(distTA=self.DtoA, doseTA=self.dosetoA, resolution=self.Res).shape
        gg = np.zeros((n1, gn2, gn3))

        p_pcnt = []

        for i in range(n1):
            aa[i] = mlog[i].fluence.actual.calc_map().astype(np.float)

        for i in range(n1):
            ee[i] = mlog[i].fluence.expected.calc_map().astype(np.float)

        for i in range(n1):
            gg[i] = mlog[i].fluence.gamma.calc_map(distTA=self.DtoA, doseTA=self.dosetoA, resolution=self.Res).astype(np.float)

        for i in range(n1):
            p_pcnt.append(round(mlog[i].fluence.gamma.pass_prcnt, 1))

        dd = aa - ee

        p_str = ''
        for i in p_pcnt:
            p_str += str(i) + '%, '

        p_str = p_str[0:-2]

        # p_str = p_str[:-1]

        print(p_pcnt)

        fail_list = []

        for i in range(n1):
            if p_pcnt[i] < 98.5:
                fail_list.append(i)

        fail_str = ''
        for i in fail_list:
            fail_str += str(i + 1) + ','

        fail_str = fail_str[:-1]

        plan_file = glob.glob('*.dcm')
        dcm = pydicom.read_file(plan_file[0])

        # Generate report in pdf format
        str1 = qa_date + '.pdf'
        resultfilename = self.path_name + '\\' + str1
        doc = SimpleDocTemplate(resultfilename, pagesize=A4)

        logo = Image("C:\\Users\\ngcho\\Pictures_A\\qmhlogo.png")
        logo.drawHeight = 0.7 * inch
        logo.drawWidth = 0.85 * inch

        # container for the 'Flowable' objects
        elements = []

        MUs = []
        ControlPts = []

        for beam in dcm.FractionGroupSequence[0].ReferencedBeamSequence:
            MUs.append(round(beam.BeamMeterset))

        for beam in dcm.BeamSequence:
            ControlPts.append(beam.NumberOfControlPoints)

        data = [[logo, 'Department of Clinical Oncology'],
                ['', ''],
                ['IMRT QA Report', ''],
                ['Patient Name:', str(dcm.PatientName)],
                ['Patient ID:', str(dcm.PatientID)],
                ['Plan Label:', str(dcm.RTPlanLabel)],
                ['LINAC:', str(dcm.BeamSequence[0].TreatmentMachineName)],
                ['QA Date:', qa_date[0:4] + '/' + qa_date[4:6] + '/' + qa_date[6:8]],
                ['Total # Beams:', str(len(dcm.BeamSequence))],
                ['Gamma Criteria:', str(self.DtoA) + 'mm / ' + str(self.dosetoA) + '%'],
                ['List of Failed Beams:', fail_str],
                ['Overall Pass?', str(np.mean(p_pcnt) > 98.5)],
                ['Passing Rate of Each Beam:']]

        t = Table(data, hAlign='LEFT')
        t.setStyle(TableStyle([('FONTSIZE', (1, 0), (1, 0), 18),
                               ('FONTSIZE', (0, 1), (-1, -1), 14)]))
        elements.append(t)
        print(p_pcnt)

        data1 = [[str(p_pcnt).strip('[').strip(']')],
                 ['Physicist Signature:']]
        t1 = Table(data1, hAlign='LEFT')
        t1.setStyle(TableStyle([('FONTSIZE', (0, 0), (0, 0), 12),
                                ('FONTSIZE', (0, 1), (-1, -1), 14)]))
        elements.append(t1)

        # plot failed beams
        for i in fail_list:
            pict_name = 'pict_' + str(i) + '.png'
            f = plt.figure()
            ax1 = f.add_subplot(1, 4, 1)
            ax1.set_title('Actual')
            ax1.imshow(aa[i], aspect='auto')
            ax2 = f.add_subplot(1, 4, 2)
            ax2.set_title('Expected')
            ax2.imshow(ee[i], aspect='auto')
            ax3 = f.add_subplot(1, 4, 3)
            ax3.set_title('Gamma Index')
            ax3.imshow(gg[i], aspect='auto')
            ax4 = f.add_subplot(1, 4, 4)
            ax4.set_title('Difference')
            ax4.imshow(dd[i], aspect='auto')
            f.savefig(pict_name)
            plt.close(f)

        for i in fail_list:
            pict_name = 'pict_' + str(i) + '.png'
            pict1 = Image(pict_name)
            pict1.drawHeight = 6 * inch
            pict1.drawWidth = 6.5 * inch
            str2 = 'Failed Beam: ' + str(i + 1)
            data2 = [[str2],
                     [pict1]]
            t2 = Table(data2, hAlign='LEFT')
            t2.setStyle(TableStyle([('FONTSIZE', (0, 0), (0, 0), 14)]))
            elements.append(PageBreak())
            elements.append(t2)
            # os.remove(pict_name)

        # write the document to disk
        doc.build(elements)

        # figname = glob.glob('*.png')
        # for name in figname:
        #     os.remove(name)
        #
        # for i in fail_list:
        #     pict_name = 'pict_' + str(i) + '.png'
        #     os.remove(pict_name)

        gamma_cri_str = str(self.DtoA) + 'mm / ' + str(self.dosetoA) + '%'
        pass_fail = str(np.mean(p_pcnt) > 98.5)
        # db.save_file(str1, open(resultfilename, 'rb'))

        fileID = fs.put(open(resultfilename, 'rb'))
        # p_pcnt = p_pcnt.tolist
        db.IMRT_QA.insert_one({'LINAC': str(dcm.BeamSequence[0].TreatmentMachineName),
                                     'Patient Name': str(dcm.PatientName),
                                     'Patient ID': str(dcm.PatientID),
                                     'Plan Label': str(dcm.RTPlanLabel),
                                     'QA Date': qa_date,
                                     'Total # Beams': str(len(dcm.BeamSequence)),
                                     'Gamma Criteria': gamma_cri_str,
                                     'List of Failed Beams': fail_str,
                                     'Overall Pass/Fail': pass_fail,
                                     'Passing Rate of Each Beam': p_pcnt,
                                     'MUs of each beam': MUs,
                                     'Number of Control Points for each beam': ControlPts,
                                     'Dose Rate': str(dcm.BeamSequence[0].ControlPointSequence[0].DoseRateSet),
                                     'reportpdf': resultfilename,
                                     'report file id': fileID})
        # db.IMRT_QA.insert_one()

        plt.close('all')
        # figname = glob.glob('*.png')
        # for name in figname:
        #     os.remove(name)

        # for i in fail_list:
        #     pict_name = 'pict_' + str(i) + '.png'
        #     os.remove(pict_name)

        return (resultfilename)


