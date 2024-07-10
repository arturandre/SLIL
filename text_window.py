# This is the main interface of SLIL code
# The core responsible for managing the summary (annotations)
# is at the summan.py [summan comes from: (sum)mary (man)ager]

from PIL import Image, ImageTk
import imageio
import PySimpleGUI as sg
import webbrowser
import os
import re

import clipboard

menu_def = [['&File',
    ['&Choose folder',
     'Choose text folder',
    'S&ave labels',
    '&Save as labels',
    '&Load labels',
    '&Quit']
    ],
    ['&Edit',
    ['&Go to',
    '&Export batch',
    '&Merge (import batch)']
    ]
]

from summan import SummaryManager

sg.theme('DarkAmber')  # Add a touch of color

#defaultFont = None
defaultFont = ("Helvetica", 12)

window = None
sgImage = None

sgImage = sg.Image(size=(640, 640), key='displayImage')

img_col = []

img_col.append([sgImage])
img_col.append([
    sg.Text('Image name: -' + '-'* 25, key="txt_img_name", font=defaultFont),
    sg.Button('Copy to clipboard', key='btCpClip', font=defaultFont)])

labels_col = []

unlabeled_code = '-10'
positive_label = '1'
negative_label = '-1'
uncertain_label = '0'

pressedNum = None
waiting_decision = False

summary_manager = SummaryManager()
labels_header = [
    sg.Text('-1   ', font=defaultFont),
    sg.Text('0   ', font=defaultFont),
    sg.Text('1', font=defaultFont),
    ]

for i, label in enumerate(summary_manager.labels):
    labels_col.append([
        sg.Radio('', f"label{i}", enable_events=True, key=f'label_n{i}', font=defaultFont),
        sg.Radio('', f"label{i}", enable_events=True, key=f'label_u{i}', font=defaultFont),
        sg.Radio('', f"label{i}", enable_events=True, key=f'label_p{i}', font=defaultFont),
        sg.Text(label, font=defaultFont),
        sg.Text('*', key=f'unlabeled_{i}', font=defaultFont),
        ])
labels_col.append([sg.Button('Save')])
labels_col.append([sg.Button('<- Previous', font=defaultFont), sg.Button('Next ->', font=defaultFont)])
labels_col.append([sg.Checkbox('Auto-save', font=defaultFont, default=True, key="cbautosave")])
labels_col.append([sg.Checkbox('Only unlabeled', font=defaultFont, default=False, key="cbunlabeled")])
labels_col.append([sg.Checkbox('Ignore exported', font=defaultFont, default=True, key="cbexported")])
labels_col.append([
    sg.Text('Image index: 000000/000000', key="txt_img_index", font=defaultFont)])

labels_col.append([sg.Text('Check on GSV:', font=defaultFont)])
labels_col.append([sg.Button('Pano', font=defaultFont), sg.Button('Coordinates', font=defaultFont)])

labels_col_header = [labels_header] + labels_col

# All the stuff inside your window.
layout = [[sg.Menu(menu_def, tearoff=True, key='menu')],
          [sg.Column(img_col), sg.Column(labels_col_header)],
          ]

# Create the Window
text_window = sg.Window('Text window',
    layout,
    return_keyboard_events=False,
    use_default_focus=False).Finalize()
def on_close():
    global text_window
    text_window.Close()
    return True
    
text_window.TKroot.protocol("WM_DELETE_WINDOW", on_close)
text_window.bind("<Key>", '')