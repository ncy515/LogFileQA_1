import time
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os.path, time
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import os
from PicketFence1 import PicketFence
import numpy as np
import glob
from pymongo import MongoClient
import gridfs
import datetime
import shutil

class MLC_QA:
    def __init__(self, file_dir, LA_Name):
        self.file_dir = file_dir
        self.LA_Name = LA_Name
        self.init_dir = os.getcwd()
        os.chdir(file_dir)

    def QA_Results(self, tolerance: float=0.5, action_tolerance: float=None, hdmlc: bool=False, num_pickets: int=None):
        f_names = glob.glob('*.dcm')
        position = ['Gantry_0.dcm', 'Gantry_90.dcm', 'Gantry_180.dcm', 'Gantry_270.dcm']

        for i, f_name in enumerate(f_names):
            if f_name.startswith("Gantry"):
                pass
            else:
                os.rename(f_name, position[i])

        results = []
        err_leaves = []
        f_names = glob.glob('*.dcm')

        for f in f_names:
            pf = PicketFence(f)
            pf.analyze(tolerance=0.5, num_pickets=5)
            results.append('Gantry Angle:')
            results.append(pf.image.gantry_angle)
            results.append(pf.results())

        for f in f_names:
            pf = PicketFence(f)
            pf.analyze(tolerance=tolerance, hdmlc = hdmlc, num_pickets=num_pickets)
            try:
                err_leaves.append(pf.error_leafs())

            except:
                err_leaves.append(['N/A', 'N/A', 'N/A'])

        for r in results:
            print(r)

        print('The 3 leaves of maximum error at 4 tested Gantry angles')
        print(err_leaves)

    def QA_Report(self, tolerance: float=0.5, action_tolerance: float=None, hdmlc: bool=False, num_pickets: int=5):
        f_names = glob.glob('*.dcm')
        position = ['Gantry_0.dcm', 'Gantry_90.dcm', 'Gantry_180.dcm', 'Gantry_270.dcm']
        for i, f_name in enumerate(f_names):
            if f_name.startswith("Gantry"):
                pass
            else:
                os.rename(f_name, position[i])

        # for i, f_name in enumerate(f_names):
        #     name = position[i]
        #     shutil.move(f_name, name)

        f_names = glob.glob('*.dcm')

        client = MongoClient('localhost', 27017)
        db = client.QA
        fs = gridfs.GridFS(db)

        results = []
        mlc_list = []
        i = 0
        fig = ['fig1.png', 'fig2.png', 'fig3.png', 'fig4.png']
        gantry_angle = []

        for f in f_names:
            pf = PicketFence(f)
            pf.analyze(tolerance=tolerance, hdmlc = hdmlc, num_pickets=num_pickets)
            pf.save_analyzed_image(fig[i])
            gantry_angle.append(pf.image.gantry_angle)
            results.append(pf.results())
            # mlc_list.append(pf.error_leafs())
            i += 1

        reportname = str(datetime.datetime.fromtimestamp(os.stat(f_names[0]).st_ctime))
        reportname = 'PF_' + reportname[0:10] + '.pdf'


        doc = SimpleDocTemplate(reportname, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        Story = []

        current_directory = os.getcwd()
        logo = self.init_dir + '\\images\\qmh_logo.png'
        formatted_time = time.ctime(os.path.getmtime(f_names[0]))

        im = Image(logo, 1.2 * inch, 1 * inch)
        Story.append(im)

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))

        ptext = '<font size=10>Department of Clinical Oncology, Medical Physics Unit</font>'
        Story.append(Paragraph(ptext, styles["Center"]))
        Story.append(Spacer(1, 12))
        ptext = '<font size=10>QA Date: %s</font>' % formatted_time
        Story.append(Paragraph(ptext, styles["Normal"]))
        ptext = '<font size=10>Linear Accelerator: %s</font>' % self.LA_Name
        Story.append(Paragraph(ptext, styles["Normal"]))


        for i in range(4):
            ptext = '<font size=10>Gantry Angle: %s</font>' % gantry_angle[i]
            Story.append(Paragraph(ptext, styles["Normal"]))
            Story.append(Spacer(1, 12))

            result = results[i].splitlines()
            for r in result:
                ptext = '<font size=10>%s</font>' % r
                Story.append(Paragraph(ptext, styles["Normal"]))

            Story.append(Spacer(1, 12))

            im = Image(fig[i], 7 * inch, 7 * inch)
            Story.append(im)
            Story.append(PageBreak())

        ptext = '<font size=10>Leaves of maximum error for all Gantry Angles</font>'
        Story.append(Paragraph(ptext, styles["Center"]))
        Story.append(Spacer(1, 12))
        mg_leaf = [[0,0,0], [0,0,0], [0,0,0], [0,0,0]]

        k = 0
        for f in f_names:
            pf = PicketFence(f)
            pf.analyze(tolerance=tolerance, hdmlc = hdmlc, num_pickets=num_pickets)
            try:
                mlc_list.append([x+1 for x in pf.error_leafs()])
                mg_leaf[k] = [x+1 for x in pf.error_leafs()]
            except:
                mlc_list.append([0, 0, 0])
                # mg_leaf[k] = [0,0,0]
            k += 1

        mg_leaf = [j for sub in mg_leaf for j in sub]
        mg_leaf = [int(j) for j in mg_leaf]

        mlc_list1 = np.array(mlc_list)
        data = np.c_[gantry_angle, mlc_list1]
        name = ['', '1st', '2nd', '3rd']
        data = np.r_[[name], data]
        data = np.array(data).tolist()

        print(mg_leaf)

        t = Table(data)
        t.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                               # ('VALIGN', (0,0), (-1,-1), 'CENTER'),
                               ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                               ('BOX', (0, 0), (-1, -1), 0.25, colors.black)]))
        Story.append(t)

        doc.build(Story)

        # list0 = mlc_list[0]
        # list1 = mlc_list[1]
        # list2 = mlc_list[2]
        # list3 = mlc_list[3]

        fileID = fs.put(open(reportname, 'rb'))

        db.picketfence_QA.insert_one({'LINAC': self.LA_Name,
                               'QA Date': str(formatted_time),
                               'Tested Gantry Angles': gantry_angle,
                               'Leaves with top 3 biggest errors at G0': mg_leaf[0:3],
                               'Leaves with top 3 biggest errors at G90': mg_leaf[3:6],
                               'Leaves with top 3 biggest errors at G180': mg_leaf[6:9],
                               'Leaves with top 3 biggest errors at G270': mg_leaf[9:12]
                               # 'report file id': fileID})
                                      })

        return reportname
