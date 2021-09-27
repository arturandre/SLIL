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

from menu import *
from altimagefolder import altimagefolder # Singleton

file_menu = FileMenu()
edit_menu = EditMenu()
altimgs_menu = AltImageFolderMenu(altimagefolder)

# File menu handlers #########################

# 'Choose &summary file'
def bt_ld_smr(menu_button, *args, **kwargs):
    summary_manager = kwargs['summary_manager']
    text = sg.popup_get_file("Select the summary file to load",
            title="Select summary file",
            default_extension=".smr",
            file_types=(('Summary file', '.smr'), ('ALL Files', '*.*'),),
            )
    summary_manager.load_summary_file(text)
    
file_menu["bt_ld_smr"].set_handler(bt_ld_smr)

# 'Choose &images folder'
def bt_ld_img(menu_button, *args, **kwargs):
    summary_manager = kwargs['summary_manager']
    picture_folder = sg.popup_get_folder('Please select a pictures folder')
    if picture_folder is not None:
        if not os.path.exists(picture_folder):
            sg.popup('The folder', picture_folder, 'couldn\'t be found or is inaccessible!')
        else:
            summary_manager.load_images_folder(picture_folder)

            if summary_manager.is_summan_ready():
                current_sample_index = 0
                while not load_sample(current_sample_index):
                    if summary_manager.count_samples() > current_sample_index+1:
                        current_sample_index += 1
                    else:
                        sg.popup("The current folder doesn't have any of the images in the loaded summary file!")
                        break

file_menu["bt_ld_img"].set_handler(bt_ld_img)

# 'S&ave labels'
def bt_sv_lbl(menu_button):
    pass
file_menu["bt_sv_lbl"].set_handler(bt_sv_lbl)

# '&Save as labels'
def bt_sv_lbl_as(menu_button):
    pass
file_menu["bt_sv_lbl_as"].set_handler(bt_sv_lbl_as)

# '&Load labels'
def bt_ld_lbl(menu_button):
    pass
file_menu["bt_ld_lbl"].set_handler(bt_ld_lbl)

# '&Quit'
def bt_quit(menu_button):
    pass
file_menu["bt_quit"].set_handler(bt_quit)

# END File menu handlers

# Edit menu handlers ############
# END Edit menu handlers

# Alternative images folder menu handlers ################

def bt_add_alt_im_fd(menu_button, *args, **kwargs):
    update_menu = kwargs["update_menu"]
    text = sg.popup_get_file("Select the summary file to load",
        title="Select summary file",
        default_extension=".smr",
        file_types=(('Summary file', '.smr'), ('ALL Files', '*.*'),),
        )
    if text is None: # Cancel
        return
    if not os.path.exists(text):
        sg.popup("The selected folder can't be found or is not accessible!")
        return
    altimagefolder.insert_folder(text)
    update_menu()
    

altimgs_menu["bt_add_alt_im_fd"].set_handler(bt_add_alt_im_fd)

def bt_rem_alt_im_fd(menu_button, *args, **kwargs):
    pass
altimgs_menu["bt_rem_alt_im_fd"].set_handler(bt_rem_alt_im_fd)

# END Alternative images folder menu handlers ############

file_menu.check_handlers()
edit_menu.check_handlers()
altimgs_menu.check_handlers()

from summan import SummaryManager

sg.theme('DarkAmber')  # Add a touch of color

window = None
sgImage = None

sgImage = sg.Image(size=(640, 640), key='displayImage')

img_col = []

img_col.append([sgImage])
img_col.append([
    sg.Text('Image name: -' + '-'* 140, key="txt_img_name"),
    sg.Button('Copy to clipboard', key='btCpClip')])

labels_col = []

unlabeled_code = '-10'
positive_label = '1'
negative_label = '-1'
uncertain_label = '0'

pressedNum = None
waiting_decision = False

summary_manager = SummaryManager()
labels_header = [
    sg.Text('-1   '),
    sg.Text('0   '),
    sg.Text('1'),
    ]

for i, label in enumerate(summary_manager.labels):
    labels_col.append([
        sg.Radio('', f"label{i}", enable_events=True, key=f'label_n{i}'),
        sg.Radio('', f"label{i}", enable_events=True, key=f'label_u{i}'),
        sg.Radio('', f"label{i}", enable_events=True, key=f'label_p{i}'),
        sg.Text(label),
        sg.Text('*', key=f'unlabeled_{i}'),
        ])
labels_col.append([sg.Button('Save')])
labels_col.append([sg.Button('<- Previous'), sg.Button('Next ->')])
labels_col.append([sg.Checkbox('Auto-save', default=False, key="cbautosave")])
labels_col.append([sg.Checkbox('Only unlabeled', default=False, key="cbunlabeled")])
labels_col.append([sg.Checkbox('Ignore exported', default=True, key="cbexported")])
labels_col.append([
    sg.Text('Image index: 000000/000000', key="txt_img_index")])

labels_col.append([sg.Text('Check on GSV:')])
labels_col.append([sg.Button('Pano'), sg.Button('Coordinates')])

labels_col_header = [labels_header] + labels_col

def initialize_menu():
    global file_menu
    global edit_menu
    global altimgs_menu
    menu_def = [file_menu.to_simpleGui_list(),
    edit_menu.to_simpleGui_list(),
    altimgs_menu.to_simpleGui_list()]
    general_menu = sg.Menu(menu_def, tearoff=True, key='menu')
    return general_menu

general_menu = initialize_menu()

def update_menu():
    global general_menu
    global file_menu
    global edit_menu
    global altimgs_menu
    menu_def = [file_menu.to_simpleGui_list(),
    edit_menu.to_simpleGui_list(),
    altimgs_menu.to_simpleGui_list()]
    general_menu.Update(menu_def)


# All the stuff inside your window.
layout = [[general_menu],
          [sg.Column(img_col), sg.Column(labels_col_header)],
          ]

# Create the Window
window = sg.Window('Street Level Imagery Labeler - SLIL',
    layout,
    return_keyboard_events=False,
    use_default_focus=False).Finalize()
def on_close():
    if sg.popup_ok_cancel("Do you really want to exit?", title="Confirm exit") == "OK":
        if summary_manager.unsaved:
            close_save = sg.\
                popup_yes_no('There are changes not saved, wish to save them before exiting?')
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
    if summary_manager.is_summan_ready():
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
    if summary_manager.is_summan_ready():
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
    if summary_manager.is_summan_ready():
        last_index = current_sample_index
        ignore_unlabeled = window['cbunlabeled'].get()
        ignore_exported = window['cbexported'].get()
        while True:
            current_sample_index += 1
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
            #    get_next_unlabeled(backwards=False, ignore_unlabeled=ignore_unlabeled, ignore_exported=ignore_exported)
            #else:
            #    load_sample(current_sample_index)


def set_sample_labels(index):
    if summary_manager.is_summan_ready():
        current_labels = summary_manager.current_labelgui_summary.iloc[index][-len(summary_manager.labels):]
        for current_label in enumerate(current_labels):
            # Radio buttons
            line_idx = current_label[0]
            label_line = labels_col[line_idx]
            label = int(current_label[1]) #-10, -1, 0, 1
            if label != -10:
                decision_idx = label +1 # 0, 1, 2
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
    if summary_manager.is_summan_ready():
        img_name = summary_manager.current_labelgui_summary.index[index]
        img_folder = summary_manager.imgs_folder
        imgFilename = os.path.join(img_folder, img_name)
        if not os.path.isfile(imgFilename):
            return False
        #_panoid_-zFcDmsqVM0Sfw0yQSzlcg_heading_135_pitch_-4
        current_sample_index = index
        heading_idx = img_name.index("_heading_")
        pitch_idx = img_name.index("_pitch_")
        current_pano = img_name[len("_panoid_"):heading_idx]
        current_heading = img_name\
            [(heading_idx + len("_heading_")):pitch_idx]
        current_pitch = img_name\
            [(pitch_idx+len("_pitch_")):img_name.index(".png")]
        
        image = Image.open(imgFilename)
        photo = ImageTk.PhotoImage(image)
        sgImage.update(data=photo)
        set_sample_labels(index)
        window['txt_img_index'].\
            update((
                "Image index: "
                f"{index+1}/"
                f"{len(summary_manager.current_labelgui_summary)}"
            ))

        current_img_name = img_name
        window['txt_img_name'].\
            update((
                "Image name: "
                f"{current_img_name}"
            ))
        print(img_name)
        
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
        else:  #unlabeled
            sel_labels.append(-10)
    summary_manager.\
        save_sample_labels(current_sample_index, sel_labels)

def check_label_checkbox(label_index, label_decision, mouse_click=False):
    if label_decision not in ['n', 'u', 'p']:
        raise Exception('Unrecognized decision: {label_decision}, expected: [n, u, p].')
    sel_radio_line = labels_col[label_index]
    label_decision_idx = ['n', 'u', 'p'].index(label_decision) #0, 1, 2
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
    event, values = window.read()
    
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

    if event in file_menu:
        print(f"event FileMenu {event}")
        file_menu[event].click(summary_manager=summary_manager)
    elif event in edit_menu:
        print(f"event EditMenu {event}")
    elif event in altimgs_menu:
        print(f"event AltImageMenu {event}")
        altimgs_menu[event].click(update_menu=update_menu)
        
    
    if event == 'Export batch':  # Export -> Export batch button
        text = sg.popup_get_text("How many images should be exported?",
                                 title='Export images',
                                 default_text='1000')
        if summary_manager.export_batch(int(text)):
            summary_manager.override_summary()
        continue
    elif event == 'Merge (import batch)':  # Export -> Merge (import batch) button
        text = sg.popup_get_file("Select the summary file to merge",
                                 title="Select summary file",
                                 default_extension=".smr",
                                 file_types=(('Summary file', '.smr'), ('ALL Files', '*.*'),),
                                 )
        summary_manager.merge_summary(text)
        pass
    elif event == "ch_smr_fd":  # File -> Choose folder button
        picture_folder = sg.popup_get_folder('Please select a pictures folder')
        if picture_folder is not None:
            #sg.popup('Results', 'The value returned from PopupGetFolder', picture_folder)
            if not os.path.exists(picture_folder):
                sg.popup('The folder', picture_folder, 'couldn\'t be found or is inaccessible!')
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
                            ))
                        if update_summary == "Yes":
                            summary_manager.update_summary_headers(picture_folder)
                        else:
                            sg.popup('Incompatible headers!',
                            ((
                                f'Please change the labels in summarymanager_config.txt file '
                                f'to {present_labels} and restart the application.'
                            )))
                            break
                
                summary_manager.load_images_folder(picture_folder)

                if summary_manager.is_summan_ready():
                    current_sample_index = 0
                    while not load_sample(current_sample_index):
                        if len(summary_manager.count_samples()) > current_sample_index:
                            current_sample_index += 1
                        else:
                            sg.popup("The current folder doesn't have any of the images in the loaded summary file!")
                            break

    elif summary_manager.is_summan_ready():
        if window["cbautosave"].get():
            save_in_memory()
        if event == 'Save labels':
            save_in_memory()
            summary_manager.update_summary()
            continue
        elif event == 'Go to':  # Go to (top menu button)
            text = sg.popup_get_text(f"Go to which image index from {0} up to {current_sample_index}",
                                    title='Go to image',
                                    default_text='0')
            if text is not None:
                sample_index = int(text)
                load_sample(sample_index)
        elif event == 'Save as labels':
            text = sg.popup_get_folder('Please select a folder')
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
                    
                elif waiting_decision and (window.user_bind_event.char in ['a', 's', 'd']):
                    decision = ['a', 's', 'd'].index(window.user_bind_event.char)
                    decision = ['n', 'u', 'p'][decision]
                    if (pressedNum >= 0) and (pressedNum < len(summary_manager.labels)):
                        check_label_checkbox(pressedNum, decision)
                if not window.user_bind_event.char.isdigit():  # Number keys
                    waiting_decision = False
            elif window.user_bind_event.keysym == 'Left': # Enter keys:
                decrease_sample_index()
            elif window.user_bind_event.keysym == 'Right': # Enter keys:
                increase_sample_index()
        



