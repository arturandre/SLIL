# This is the main interface of SLIL code
# The core responsible for managing the summary (annotations)
# is at the summan.py [summan comes from: (sum)mary (man)ager]

from PIL import Image, ImageTk
import imageio
import PySimpleGUI as sg
import os

menu_def = [['&File', ['&Choose folder', 'S&ave labels', '&Save as labels', '&Load labels', '&Quit']],
            ['&Export', ['&Export batch', '&Merge (import batch)']]
            ]

from summan import SummaryManager

sg.theme('DarkAmber')  # Add a touch of color

window = None
sgImage = None

sgImage = sg.Image(size=(640, 640))

img_col = [[sgImage]]
labels_col = []

summary_manager = SummaryManager()

for label in SummaryManager.labels:
    labels_col.append([sg.Checkbox(label)])
labels_col.append([sg.Button('Save')])
labels_col.append([sg.Button('<- Previous'), sg.Button('Next ->')])
labels_col.append([sg.Checkbox('Auto-save', default=True, key="cbautosave")])
labels_col.append([sg.Checkbox('Only unlabeled', default=False, key="cbunlabeled")])
labels_col.append([sg.Checkbox('Ignore exported', default=True, key="cbexported")])
labels_col.append([sg.Text('Image index: 000000/000000', key="txt_img_index")])

# All the stuff inside your window.
layout = [[sg.Menu(menu_def, tearoff=True)],
          [sg.Column(img_col), sg.Column(labels_col)],
          ]

# Create the Window
window = sg.Window('Tree Wires labeler', layout, return_keyboard_events=True, use_default_focus=False).Finalize()

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
                if not next_sample[SummaryManager.labels[0]] in (-1, '-1'):
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
                if not next_sample[SummaryManager.labels[0]] in (-1, '-1'):
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
            labels_col[current_label[0]][0].update(current_label[1] in [1, '1'])


def load_sample(index):
    if summary_manager.is_summary_loaded():
        imgFilename = os.path.join(
            os.path.dirname(summary_manager.current_labelgui_summary_filepath),
            summary_manager.current_labelgui_summary.index[index])
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
    pass

# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == None:  # if user closes window
        if summary_manager.unsaved:
            close_save = sg.popup_yes_no('There are changes not saved, wish to save them before exiting?')
            if close_save == "Yes":
                sel_labels = [cb[0].get() for cb in labels_col[:len(SummaryManager.labels)]]
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
        text = sg.popup_get_folder('Please select a pictures folder')
        if text is not None:
            sg.popup('Results', 'The value returned from PopupGetFolder', text)
            summary_manager.load_images_folder(text)
            if summary_manager.is_summary_loaded():
                current_sample_index = 0
                load_sample(current_sample_index)
    elif summary_manager.is_summary_loaded():
        if event == 'Save labels':
            summary_manager.update_summary()
            continue
        elif event == 'Save as labels':
            text = sg.popup_get_folder('Please select a folder')
            if text is not None:
                summary_manager.update_summary(text)
            continue
        elif event in ('\r', 'Return:36', 'Save'):
            print('Enter')
            sel_labels = \
                [cb[0].get() for cb in labels_col[:len(SummaryManager.labels)]]
            summary_manager.\
                save_sample_labels(current_sample_index, sel_labels)
            continue
        if window["cbautosave"].get():
            sel_labels = \
                [cb[0].get() for cb in labels_col[:len(summary_manager.labels)]]
            summary_manager.\
                save_sample_labels(current_sample_index, sel_labels)
        if event.isdigit():  # hotkey for labels
            print("digit: ", event)
            event = int(event)
            if event < len(SummaryManager.labels):
                sel_checkbox = labels_col[event][0]
                checked = bool(sel_checkbox.get())
                sel_checkbox.update(not checked)
                continue
        elif event in ('Left:37', '<- Previous'):
            decrease_sample_index()
        elif event in ('Right:39', 'Next ->'):
            increase_sample_index()

    else:
        print('event ', event)
    print('event ', event)
    # print('You entered ', values[0])



window.close()
