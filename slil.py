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
from summan_captions import get_image_captions

text_window = None
current_questions = []
current_answers_gt = []
current_answers_pred = []
current_question_idx = -1
num_questions = -1

def change_question_index(question_idx):
    global text_window, current_questions, current_answers_gt
    global current_answers_pred, current_question_idx, num_questions
    current_question_idx = question_idx

    if text_window is None:
        sg.popup("Change change the question without selecting a text folder!")
    else:
        text_window['-QUESTION-'].update(current_questions[current_question_idx])
        text_window['-ANSWERS_GT-'].update(current_answers_gt[current_question_idx])
        text_window['-ANSWERS_PRED-'].update(current_answers_pred[current_question_idx])

    
def open_new_window(image_name, gt_answers_path, pred_answers_path):
    global text_window, current_questions, current_answers_gt
    global current_answers_pred, current_question_idx, num_questions
    gt_answers_path = gt_answers_path.replace('/', os.sep)
    pred_answers_path = pred_answers_path.replace('/', os.sep)

    questions, answers_gt, answers_pred =\
        get_image_captions(image_name, gt_answers_path, pred_answers_path)
    current_questions = questions
    current_answers_gt = answers_gt
    current_answers_pred = answers_pred
    num_questions = len(questions)
    current_question_idx = 0
    if len(current_answers_gt) == 0:
        current_answers_gt = [""]*num_questions
    if len(current_answers_pred) == 0:
        current_answers_pred = [""]*num_questions
    
    #question = "" if question is None else question
    #answers_gt = "" if answers_gt is None else answers_gt
    #answers_pred = "" if answers_pred is None else answers_pred

    #if question is None or answers_gt is None or answers_pred is None:
    #    sg.popup("No data found for the selected image.")
    #    return

    if text_window is None:
        layout = [
            [sg.Multiline(current_questions[current_question_idx],
                          size=(80, 5), disabled=True, key='-QUESTION-')],
            [sg.Multiline(current_answers_gt[current_question_idx],
                          size=(40, 15), disabled=True, key='-ANSWERS_GT-'),
             sg.Multiline(current_answers_pred[current_question_idx],
                          size=(40, 15), disabled=True, key='-ANSWERS_PRED-')],
            [sg.Button('Close')]
        ]

        text_window = sg.Window("Comparison Window", layout, finalize=True, modal=False)
    else:
        text_window['-QUESTION-'].update(current_questions[current_question_idx])
        text_window['-ANSWERS_GT-'].update(current_answers_gt[current_question_idx])
        text_window['-ANSWERS_PRED-'].update(current_answers_pred[current_question_idx])

    # while True:
    #     event, values = window.read()
    #     if event in (sg.WIN_CLOSED, 'Close'):
    #         break

    # window.close()


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
#positive_label = '1'
#negative_label = '-1'
#uncertain_label = '0'

pressedNum = None
waiting_decision = False

summary_manager = SummaryManager()
labels_header = [
    sg.Text('U    ', font=defaultFont),
    sg.Text('N   ', font=defaultFont),
    sg.Text('A', font=defaultFont),
    sg.Text('X', font=defaultFont),
    ]

for i, label in enumerate(summary_manager.labels):
    labels_col.append([
        sg.Radio('', f"label{i}", enable_events=True, key=f'label_n{i}', font=defaultFont),
        sg.Radio('', f"label{i}", enable_events=True, key=f'label_u{i}', font=defaultFont),
        sg.Radio('', f"label{i}", enable_events=True, key=f'label_p{i}', font=defaultFont),
        sg.Radio('', f"label{i}", enable_events=True, key=f'label_x{i}', font=defaultFont),
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
window = sg.Window('Street Level Imagery Labeler - SLIL',
    layout,
    return_keyboard_events=False,
    use_default_focus=False).Finalize()


def on_close():
    if sg.popup_ok_cancel("Do you really want to exit?", title="Confirm exit", font=defaultFont) == "OK":
        if summary_manager.unsaved:
            close_save = sg.\
                popup_yes_no('There are changes not saved, wish to save them before exiting?', font=defaultFont)
            if close_save == "Yes":
                save_in_memory()
                summary_manager.update_summary()
            if close_save is not None:
                window.Close()
                exit()
        else:
            window.Close()
            exit()
        # The program shouldn't reach this point!
        return True
    else:
        return False
window.TKroot.protocol("WM_DELETE_WINDOW", on_close)

window.bind("<Key>", '')

# Refs:
# - event handlers: https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/event-handlers.html
# -- event types: https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/event-types.html
# -- key names: https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/key-names.html
def handleKeyboardEvents(event):
    if event.type == 2:  # KeyPress
        print(event.keysym)
        

current_sample_index = -1
current_pano = None
current_heading = None
current_pitch = None
current_img_name = None

def get_next_unlabeled(backwards=False, ignore_unlabeled=False, ignore_exported=False):
    global current_sample_index
    step = 1 if not backwards else -1
    if summary_manager.is_summary_loaded():
        last_col = summary_manager.current_labelgui_summary.columns[-1]
        # if not backwards:
        next_unlabeled_ones = summary_manager.current_labelgui_summary.iloc[
                              current_sample_index::step][
            summary_manager.current_labelgui_summary.iloc[current_sample_index::step][last_col] == unlabeled_code]
        # else:
        #    next_unlabeled_ones = summary_manager.current_labelgui_summary.iloc[
        #                          :current_sample_index:step][
        #        summary_manager.current_labelgui_summary.iloc[:current_sample_index:step][last_col] == unlabeled_code]
        if len(next_unlabeled_ones) == 0:
            # if not backwards:
            next_unlabeled_ones = summary_manager.current_labelgui_summary.iloc[
                                  :current_sample_index:step][
                summary_manager.current_labelgui_summary.iloc[:current_sample_index:step][last_col] == unlabeled_code]
            # else:
            #    next_unlabeled_ones = summary_manager.current_labelgui_summary.iloc[
            #                          current_sample_index::step][
            #        summary_manager.current_labelgui_summary.iloc[current_sample_index::step][last_col] == unlabeled_code]
        if len(next_unlabeled_ones) > 0:
            current_sample_index = summary_manager.current_labelgui_summary.index.get_loc(next_unlabeled_ones.index[0])
            load_sample(current_sample_index)


def decrease_sample_index():
    global current_sample_index
    if summary_manager.is_summary_loaded():
        last_index = current_sample_index
        ignore_unlabeled = window['cbunlabeled'].get()
        ignore_exported = window['cbexported'].get()
        while True:
            current_sample_index -= 1
            current_sample_index %= len(summary_manager.current_labelgui_summary)
            if last_index == current_sample_index:
                sg.popup_error("No next image found!")
                break
            next_sample = summary_manager.current_labelgui_summary.iloc[current_sample_index]
            if ignore_unlabeled:
                if not next_sample[summary_manager.labels[0]] in (int(unlabeled_code), unlabeled_code):
                    continue
            if ignore_exported:
                if next_sample['status'] == 'exported':
                    continue
            break
        load_sample(current_sample_index)

        #if ignore_unlabeled or ignore_exported:
        #    get_next_unlabeled(backwards=True, ignore_unlabeled=ignore_unlabeled, ignore_exported=ignore_exported)
        #else:
        #    load_sample(current_sample_index)

def increase_sample_index():
    global current_sample_index
    if summary_manager.is_summary_loaded():
        last_index = current_sample_index
        ignore_unlabeled = window['cbunlabeled'].get()
        ignore_exported = window['cbexported'].get()
        while True:
            current_sample_index += 1
            current_sample_index %= len(summary_manager.current_labelgui_summary)
            if last_index == current_sample_index:
                sg.popup_error("No next image found!", font=defaultFont)
                break
            next_sample = summary_manager.current_labelgui_summary.iloc[current_sample_index]
            if ignore_unlabeled:
                if not next_sample[summary_manager.labels[0]] in (int(unlabeled_code), unlabeled_code):
                    continue
            if ignore_exported:
                if next_sample['status'] == 'exported':
                    continue
            break
        load_sample(current_sample_index)
            #if ignore_unlabeled or ignore_exported:
            #    get_next_unlabeled(backwards=False, ignore_unlabeled=ignore_unlabeled, ignore_exported=ignore_exported)
            #else:
            #    load_sample(current_sample_index)


def set_sample_labels(index):
    if summary_manager.is_summary_loaded():
        current_labels = summary_manager.current_labelgui_summary.iloc[index][-len(summary_manager.labels):]
        for current_label in enumerate(current_labels):
            # Radio buttons
            line_idx = current_label[0]
            label_line = labels_col[line_idx]
            label = int(current_label[1]) #-10, -1, 0, 1, 2
            if label != -10:
                decision_idx = label +1 # 0, 1, 2, 3
                label_line[decision_idx].update(True)
            else:
                # Hack to reset radio buttons
                # https://github.com/PySimpleGUI/PySimpleGUI/issues/1350#issuecomment-487114267
                label_line[0].TKIntVar.set(0)
                #for i in range(3):
                #    label_line[i].update(False)
            # Text (*)
            labels_col[line_idx][-1]\
                .update('*' if current_label[1] in [int(unlabeled_code), unlabeled_code] else '')

def load_sample(index):
    global current_sample_index
    global current_pano
    global current_heading
    global current_pitch
    global current_img_name
    if summary_manager.is_summary_loaded():
        img_name = summary_manager.current_labelgui_summary.index[index]
        imgFilename = os.path.join(
            os.path.dirname(summary_manager.current_labelgui_summary_filepath),
            img_name)
        #_panoid_-zFcDmsqVM0Sfw0yQSzlcg_heading_135_pitch_-4
        current_sample_index = index
        
        try:
            heading_idx = img_name.index("_heading_")
        except ValueError:
            heading_idx = 0

        try:
            pitch_idx = img_name.index("_pitch_")
        except ValueError:
            pitch_idx = 0

        try:
            current_pano = img_name[len("_panoid_"):heading_idx]
        except ValueError:
            current_pano = "0"

        try:
            current_heading = img_name[(heading_idx + len("_heading_")):pitch_idx]
        except ValueError:
            current_heading = 0

        try:
            current_pitch = img_name[(pitch_idx + len("_pitch_")):img_name.index(".png")]
        except ValueError:
            current_pitch = 0
        
        image = Image.open(imgFilename)
        image = image.resize((512, 512))
        photo = ImageTk.PhotoImage(image)
        sgImage.update(data=photo)
        set_sample_labels(index)
        window['txt_img_index'].\
            update((
                "Image index: "
                f"{index}/"
                f"{len(summary_manager.current_labelgui_summary) - 1}"
            ))

        current_img_name = img_name
        window['txt_img_name'].\
            update((
                "Image name: "
                f"{current_img_name[:14]}..."
            ))
        print(img_name)
    if summary_manager.text_folder is not None:
        open_new_window(current_img_name, summary_manager.text_folder, summary_manager.text_folder)
        
    pass

def save_in_memory():
    sel_labels = []
    for rb_line in labels_col[:len(summary_manager.labels)]:
        if rb_line[0].get(): #-1
            sel_labels.append(-1)
        elif rb_line[1].get(): #0
            sel_labels.append(0)
        elif rb_line[2].get(): #1
            sel_labels.append(1)
        elif rb_line[3].get(): #2
            sel_labels.append(2)
        else:  #unlabeled
            sel_labels.append(-10)
    summary_manager.\
        save_sample_labels(current_sample_index, sel_labels)

def check_label_checkbox(label_index, label_decision, mouse_click=False):
    if label_decision not in ['n', 'u', 'p', 'x']:
        raise Exception('Unrecognized decision: {label_decision}, expected: [n, u, p, x].')
    sel_radio_line = labels_col[label_index]
    label_decision_idx = ['n', 'u', 'p', 'x'].index(label_decision) #-1, 0, 1, 2
    label_decision = label_decision_idx -1 # -1, 0, 1
    sel_radio = sel_radio_line[label_decision_idx]
    sel_radio.update(True)

    #checked = bool(sel_checkbox.get())
    #if mouse_click: checked = not checked
    #sel_checkbox.update(not checked)
    # Checking dependencies
    #sel_label = sel_checkbox.Text
    selected_label = sel_radio_line[-2].DisplayText
    # Turns true depencies from a dependent label
    if label_decision == 1:
        if selected_label in summary_manager.label_dependents.keys():
            dependencies = summary_manager.label_dependents[selected_label]
            for i in range(len(summary_manager.labels)):
                i_radioline = labels_col[i]

                # radio button corresponding to the option '1'
                aux_radio = i_radioline[2] 
                if i_radioline[-2].DisplayText in dependencies:
                    aux_radio.update(True)
    # Turns false dependents from a dependency label
    elif label_decision == -1:
        for key in summary_manager.label_dependents.keys():
            selected_label_dependencies = summary_manager.label_dependents[key]
            if selected_label in selected_label_dependencies:
                i_radioline = summary_manager.labels.index(key)

                # radio button corresponding to the option '-1'
                aux_radio = labels_col[i_radioline][0]
                aux_radio.update(True)

# Event Loop to process "events" and get the "values" of the inputs
while True:
    # Needed to detect when the "X" close button is pressed
    try:
        event, values = window.read(timeout=100)
    except SystemExit:
        pass # Just exiting
    
    event_str = str(event)
    print((
        f'event: {event}, type(event): {type(event)}, '
        f'event_str: {event_str}, type(event_str): {type(event_str)}')
        )
    print('values ', values)

    if (event is not None) and (len(event) == 0):
        print(f'user_bind_event: {window.user_bind_event}')
        print(f'char: {window.user_bind_event.char}, {type(window.user_bind_event.char)}')
        print(f'keysym: {window.user_bind_event.keysym}, {type(window.user_bind_event.keysym)}')
    
    if (event is None) or event == "Quit":  # if user closes window
        if on_close():
            break
    elif event == 'Export batch':  # Export -> Export batch button
        text = sg.popup_get_text("How many images should be exported?",
                                 title='Export images',
                                 default_text='1000', font=defaultFont)
        if summary_manager.export_batch(int(text)):
            summary_manager.override_summary()
        continue
    elif event == 'Merge (import batch)':  # Export -> Merge (import batch) button
        text = sg.popup_get_file("Select the summary file to merge",
                                 title="Select summary file",
                                 default_extension=".smr",
                                 file_types=(('Summary file', '.smr'), ('ALL Files', '*.*'),),
                                 font=defaultFont
                                 )
        summary_manager.merge_summary(text)
        pass
    elif event == 'Choose folder':  # File -> Choose folder button
        picture_folder = sg.popup_get_folder('Please select a pictures folder', font=defaultFont)
        if picture_folder is not None:
            #sg.popup('Results', 'The value returned from PopupGetFolder', picture_folder, font=defaultFont)
            if not os.path.exists(picture_folder):
                sg.popup('The folder', picture_folder, 'couldn\'t be found or is inaccessible!', font=defaultFont)
            else:
                if os.path.isfile(
                    os.path.join(
                        picture_folder,
                        summary_manager.summary_filename)
                    ):
                    present_labels, new_labels = \
                        summary_manager.compare_summary_headers(picture_folder)
                    if len(new_labels) > 0:
                        update_summary = sg.popup_yes_no((
                            f'New labels not present in summary: '
                            f'{new_labels}\n'
                            f'Labels present in summary: '
                            f'{present_labels}\n'
                            f'Want to insert them in the summary file?'
                            ), font=defaultFont)
                        if update_summary == "Yes":
                            summary_manager.update_summary_headers(picture_folder)
                        else:
                            sg.popup('Incompatible headers!',
                            (
                                f'Please change the labels in summarymanager_config.txt file '
                                f'to {present_labels} and restart the application.'
                            ), font=defaultFont)
                            break
                
                summary_manager.load_images_folder(picture_folder)

                if summary_manager.is_summary_loaded():
                    current_sample_index = 0
                    load_sample(current_sample_index)
                    
    elif event == 'Choose text folder':  # File -> Choose text folder button
        #TODO: Make sure it can only be selected after a picture folder is selected
        texts_folder = sg.popup_get_folder('Please select a text folder', font=defaultFont)
        if texts_folder is not None:
            if not os.path.exists(texts_folder):
                sg.popup('The folder', texts_folder, 'couldn\'t be found or is inaccessible!', font=defaultFont)
            else:
                summary_manager.text_folder = texts_folder

    elif summary_manager.is_summary_loaded():
        if window["cbautosave"].get():
            save_in_memory()
        if event == 'Save labels':
            save_in_memory()
            summary_manager.update_summary()
            continue
        elif event == 'Go to':  # Go to (top menu button)
            text = sg.popup_get_text(f"Go to which image index from {0} up to {current_sample_index}",
                                    title='Go to image',
                                    default_text='0', font=defaultFont)
            if text is not None:
                sample_index = int(text)
                load_sample(sample_index)
        elif event == 'Save as labels':
            text = sg.popup_get_folder('Please select a folder', font=defaultFont)
            if text is not None:
                save_in_memory()
                summary_manager.update_summary(text)
            continue
        elif event == 'btCpClip':
            clipboard.copy(current_img_name)
            print(f'Copied {current_img_name} to clipboard.')

            current_img_name
        elif event == 'Save':
            save_in_memory()
            summary_manager.update_summary()
            continue
        elif event == '<- Previous':
            decrease_sample_index()
        elif event == 'Next ->':
            increase_sample_index()
        elif event == 'Pano':  # Go to (top menu button)
            googleaddress = ((
                f"https://www.google.com/maps/@"
                f"-23.7411249,-46.705598"
                f",3a,75y,"
                f"{current_heading}h,"
                f"{int(current_pitch)+90}t"
                f"/data=!3m7!1e1!3m5!1s"
                f"{current_pano}"
                f"!2e0!6s%2F%2Fgeo0.ggpht.com%2Fcbk%3Fpanoid%3D"
                f"{current_pano}"
                f"%26output%3Dthumbnail%26cb_client%3Dmaps_sv.tactile.gps%26"
                f"thumb%3D2%26w%3D203%26h%3D100%26"
                f"yaw%3D169.97714%26pitch%3D0%26"
                f"thumbfov%3D100!7i16384!8i8192"
            ))
            webbrowser.open_new_tab(googleaddress)
        elif event == 'Coordinates':  # Go to (top menu button)
            #/data=!3m7!1e1!3m5!1s!2e0!5s20140101T000000!7i13312!8i6656
            lat, lon = summary_manager.\
                current_labelgui_summary.iloc[current_sample_index][['lat', 'lon']]
            googleaddress = ((
                f"https://www.google.com/maps/@"
                f"{lat},{lon}"
                f",3a,75y,"
                f"{current_heading}h,"
                f"{int(current_pitch)+90}t"
                f"/data=!3m7!1e1!3m5!1s!2e0!5s20140101T000000!7i13312!8i6656"
            ))
            webbrowser.open_new_tab(googleaddress)
        elif re.match(r'^label_[nup]\d+$', event):
            groups = re.match(r'^label_([nup])(\d+)$', event).groups()
            decision = groups[0]
            label = groups[1]
            label = int(label)
            check_label_checkbox(label, decision, mouse_click=True)
        elif len(event) == 0: # keyboard events
            if len(window.user_bind_event.char) == 1:  # numbers/letters/enter keys
                if window.user_bind_event.char == '\r':  # Enter keys
                    save_in_memory()
                    continue
                elif window.user_bind_event.char.isdigit():  # Number keys
                    waiting_decision = True
                    pressedNum = int(window.user_bind_event.char) - 1
                    
                elif waiting_decision and (window.user_bind_event.char in ['a', 's', 'd', 'f']):
                    decision = ['a', 's', 'd', 'f'].index(window.user_bind_event.char)
                    decision = ['n', 'u', 'p', 'x'][decision]
                    if (pressedNum >= 0) and (pressedNum < len(summary_manager.labels)):
                        check_label_checkbox(pressedNum, decision)
                if not window.user_bind_event.char.isdigit():  # Number keys
                    waiting_decision = False
            elif window.user_bind_event.keysym == 'Left': # Enter keys:
                decrease_sample_index()
            elif window.user_bind_event.keysym == 'Right': # Enter keys:
                increase_sample_index()
            elif window.user_bind_event.keysym == 'Up': # Enter keys:
                if num_questions > 0:
                    question_idx = (current_question_idx+1)%num_questions
                    change_question_index(question_idx)
            elif window.user_bind_event.keysym == 'Down': # Enter keys:
                if num_questions > 0:
                    question_idx = (current_question_idx-1)%num_questions
                    change_question_index(question_idx)
    if text_window is not None:
        try:
            event_text, values_text = text_window.read(timeout=100)
        except SystemExit:
            pass # Just exiting
        if event_text in (sg.WIN_CLOSED, 'Close'):
            text_window.close()
            text_window = None


    
        



