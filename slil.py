# This is the main interface of SLIL code
# The core responsible for managing the summary (annotations)
# is at the summan.py [summan comes from: (sum)mary (man)ager]

from PIL import Image, ImageTk
import imageio
import PySimpleGUI as sg
import os
import re

menu_def = [['&File', ['&Choose folder', 'S&ave labels', '&Save as labels', '&Load labels', '&Quit']],
            ['&Export', ['&Export batch', '&Merge (import batch)']]
            ]

from summan import SummaryManager

sg.theme('DarkAmber')  # Add a touch of color

window = None
sgImage = None

sgImage = sg.Image(size=(640, 640), key='displayImage')

img_col = []

img_col.append([sgImage])
img_col.append([sg.Text('Image name: -' + '-'*140, key="txt_img_name")])

labels_col = []

summary_manager = SummaryManager()

for i, label in enumerate(summary_manager.labels):
    labels_col.append([
        sg.Checkbox(label, enable_events=True, key=f'label_{i}'),
        sg.Text('*', key=f'unlabeled_{i}')
        ])
labels_col.append([sg.Button('Save')])
labels_col.append([sg.Button('<- Previous'), sg.Button('Next ->')])
labels_col.append([sg.Checkbox('Auto-save', default=False, key="cbautosave")])
labels_col.append([sg.Checkbox('Only unlabeled', default=False, key="cbunlabeled")])
labels_col.append([sg.Checkbox('Ignore exported', default=True, key="cbexported")])
labels_col.append([sg.Text('Image index: 000000/000000', key="txt_img_index")])

# All the stuff inside your window.
layout = [[sg.Menu(menu_def, tearoff=True, key='menu')],
          [sg.Column(img_col), sg.Column(labels_col)],
          ]

# Create the Window
window = sg.Window('Street Level Imagery Labeler - SLIL',
    layout,
    return_keyboard_events=False,
    use_default_focus=False).Finalize()

window.bind("<Key>", '')

# Refs:
# - event handlers: https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/event-handlers.html
# -- event types: https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/event-types.html
# -- key names: https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/key-names.html
def handleKeyboardEvents(event):
    if event.type == 2:  # KeyPress
        print(event.keysym)
        

current_sample_index = -1

def get_next_unlabeled(backwards=False, ignore_unlabeled=False, ignore_exported=False):
    global current_sample_index
    step = 1 if not backwards else -1
    if summary_manager.is_summary_loaded():
        last_col = summary_manager.current_labelgui_summary.columns[-1]
        # if not backwards:
        next_unlabeled_ones = summary_manager.current_labelgui_summary.iloc[
                              current_sample_index::step][
            summary_manager.current_labelgui_summary.iloc[current_sample_index::step][last_col] == '-1']
        # else:
        #    next_unlabeled_ones = summary_manager.current_labelgui_summary.iloc[
        #                          :current_sample_index:step][
        #        summary_manager.current_labelgui_summary.iloc[:current_sample_index:step][last_col] == '-1']
        if len(next_unlabeled_ones) == 0:
            # if not backwards:
            next_unlabeled_ones = summary_manager.current_labelgui_summary.iloc[
                                  :current_sample_index:step][
                summary_manager.current_labelgui_summary.iloc[:current_sample_index:step][last_col] == '-1']
            # else:
            #    next_unlabeled_ones = summary_manager.current_labelgui_summary.iloc[
            #                          current_sample_index::step][
            #        summary_manager.current_labelgui_summary.iloc[current_sample_index::step][last_col] == '-1']
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
                if not next_sample[summary_manager.labels[0]] in (-1, '-1'):
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
                sg.popup_error("No next image found!")
                break
            next_sample = summary_manager.current_labelgui_summary.iloc[current_sample_index]
            if ignore_unlabeled:
                if not next_sample[summary_manager.labels[0]] in (-1, '-1'):
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
            # Checkbox
            labels_col[current_label[0]][0].update(current_label[1] in [1, '1'])
            # Text (*)
            labels_col[current_label[0]][1]\
                .update('*' if current_label[1] in [-1, '-1'] else '')


def load_sample(index):
    if summary_manager.is_summary_loaded():
        imgName = summary_manager.current_labelgui_summary.index[index]
        imgFilename = os.path.join(
            os.path.dirname(summary_manager.current_labelgui_summary_filepath),
            imgName)
        
        image = Image.open(imgFilename)
        photo = ImageTk.PhotoImage(image)
        sgImage.update(data=photo)
        set_sample_labels(index)
        window['txt_img_index'].\
            update((
                "Image index: "
                f"{index}/"
                f"{len(summary_manager.current_labelgui_summary) - 1}"
            ))
        window['txt_img_name'].\
            update((
                "Image name: "
                f"{imgName}"
            ))
        print(imgName)
        
    pass

def save_in_memory():
    sel_labels = \
        [cb[0].get() for cb in labels_col[:len(summary_manager.labels)]]
    summary_manager.\
        save_sample_labels(current_sample_index, sel_labels)

def check_label_checkbox(label_index, mouse_click=False):
    sel_checkbox = labels_col[label_index][0]
    checked = bool(sel_checkbox.get())
    if mouse_click: checked = not checked
    sel_checkbox.update(not checked)
    # Checking dependencies
    sel_label = sel_checkbox.Text
    if not checked: # Just checked the CheckBox right now
        if sel_label in summary_manager.label_dependencies.keys():
            deps = summary_manager.label_dependencies[sel_label]
            for i in range(len(summary_manager.labels)):
                aux_checkbox = labels_col[i][0]
                if aux_checkbox.Text in deps:
                    aux_checkbox.update(True)

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
    
    if event is None:  # if user closes window
        if summary_manager.unsaved:
            close_save = sg.popup_yes_no('There are changes not saved, wish to save them before exiting?')
            if close_save == "Yes":
                sel_labels = [cb[0].get() for cb in labels_col[:len(summary_manager.labels)]]
                summary_manager.save_sample_labels(current_sample_index, sel_labels)
                summary_manager.update_summary()
        break
    elif event == 'Export batch':  # Export -> Export batch button
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
    elif event == 'Choose folder':  # File -> Choose folder button
        picture_folder = sg.popup_get_folder('Please select a pictures folder')
        if picture_folder is not None:
            sg.popup('Results', 'The value returned from PopupGetFolder', picture_folder)
            if not os.path.exists(picture_folder):
                sg.popup('The folder', picture_folder, 'couldn\'t be found or is inaccessible!')
            else:
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
                            f'Please change the labels in summarymanaget_config.txt file '
                            f'to {present_labels} and restart the application.'
                        )))
                        break
                
                summary_manager.load_images_folder(picture_folder)

                if summary_manager.is_summary_loaded():
                    current_sample_index = 0
                    load_sample(current_sample_index)
                    
    elif summary_manager.is_summary_loaded():
        if window["cbautosave"].get():
            save_in_memory()
        if event == 'Save labels':
            save_in_memory()
            summary_manager.update_summary()
            continue
        elif event == 'Save as labels':
            text = sg.popup_get_folder('Please select a folder')
            if text is not None:
                save_in_memory()
                summary_manager.update_summary(text)
            continue
        elif event == 'Save':
            save_in_memory()
            summary_manager.update_summary()
            continue
        elif event == '<- Previous':
            decrease_sample_index()
        elif event == 'Next ->':
            increase_sample_index()
        elif re.match(r'^label_\d+$', event):
            checkbox_label = re.match(r'^label_(\d+)$', event).groups()[0]
            checkbox_label = int(checkbox_label)
            check_label_checkbox(checkbox_label, mouse_click=True)
        elif len(event) == 0: # keyboard events
            if len(window.user_bind_event.char) == 1:  # numbers/letters/enter keys
                if window.user_bind_event.char == '\r':  # Enter keys
                    save_in_memory()
                    continue
                elif window.user_bind_event.char.isdigit(): # Number keys
                    pressedNum = int(window.user_bind_event.char)
                    if pressedNum < len(summary_manager.labels):
                        check_label_checkbox(pressedNum)
            elif window.user_bind_event.keysym == 'Left': # Enter keys:
                decrease_sample_index()
            elif window.user_bind_event.keysym == 'Right': # Enter keys:
                increase_sample_index()
        


window.close()
