import shutil
from pathlib import Path
import os
import pandas as pd


class SummaryManager:
    def __init__(self, custom_config={}):
        self.current_labelgui_summary_dirpath = None
        self.current_labelgui_summary_filepath = None
        self.current_labelgui_summary = None
        # custom configs
        self.summary_filename_no_ext = \
            custom_config.get('summary_filename_no_ext')\
            or SummaryManager.summary_filename_no_ext
        self.summary_filename_ext = \
            custom_config.get('summary_filename_ext')\
            or SummaryManager.summary_filename_ext

        self.labels = custom_config.get('labels')\
            or SummaryManager.labels
        self.label_dependencies = {}
        self._check_labels_dependencies()
        

        self.export_summary_basename =\
            custom_config.get('export_summary_basename')\
            or SummaryManager.export_summary_basename
        self.summary_filename = ((
            f"{self.summary_filename_no_ext}"
            f"{self.summary_filename_ext}"
        ))


        self.unsaved = False
        self.img_filenames = []
        pass

    def _check_labels_dependencies(self):
        self.label_dependencies = {}
        for i, label in enumerate(self.labels):
            if '>' in label:
                label, dependencies = label.split('>')
                # Removing the '(' and ')' characters"
                dependencies = dependencies[1:-1]
                self.labels[i] = label
                self.label_dependencies[label] = dependencies.split('+')

    def get_default_headers(self):
        all_headers = self._get_headers().split(',')
        num_setting_labels = len(self.labels)
        return all_headers[:-num_setting_labels]


    def _get_headers(self):
        """
        The headers from the summary file are defined
        with this function. This can be customized, but
        after creating a summary file further changes needs
        to be reflected in the created file externally.
        """
        # v2: img_name, lat(missing), lon(missing), heading, pitch, timestamp(missing), status, labels...
        # status -> free, reserved, exported
        ### free: can be taken to be annotated
        ### reserved: it is being annotated right now
        ### exported: it is reserved to be annotated later(possibly at an external system) and then merged back
        headers = (
            f"img_name"
            f",lat"
            f",lon"
            f",heading"
            f",pitch"
            f",timestamp"
            f",status"
        )
        for label in self.labels:
            headers += f",{label}"
        return headers

    def get_labeled_samples(self):
        """
        If an existing summary file is opened
        then this function can be used to retrieve
        the entries corresponding to annotated images.
        """
        if self.is_summary_loaded():
            return self.current_labelgui_summary[
                self.current_labelgui_summary[
                    self.labels[0]
                    ] != '-1']


    def count_labeled_samples(self):
        """
        This function returns the number of
        entries of the opened summary file that
        are annotated.
        """
        if self.is_summary_loaded():
            return len(self.get_labeled_samples())

    def get_summary_filename(self):
        """
        The summary filename can be customized
        (in the summarymanager_config.txt) and creating a
        new summary file in a folder where one already exists
        is handled by appending a "_N" string in the filename
        (check the summarymanager_config.txt for more details
        about name conflicts management).
        """
        if self.current_labelgui_summary_dirpath is not None:
            summary_filename = os.path.join(
                self.current_labelgui_summary_dirpath,
                self.summary_filename
                )
            return summary_filename
        else:
            raise Exception("No summary path informed!")

    def is_summary_loaded(self):
        """
        Checks if some summary file is currently loaded
        """
        return self.current_labelgui_summary is not None

    def save_sample_labels(self, index, labels):
        """
        Stash the changes to the labels to the
        currently in-memory summary file.

        Params:

        index <int> - Row of the entry to be stashed
        labels <Tuple<int>> - Values to be stashed in the labels
            section (last fields) of the 'index' rox.
        """
        if self.is_summary_loaded():
            row = self.current_labelgui_summary.iloc[index]
            # labels are always the last fields in the summary file
            for label in enumerate(
                    self.current_labelgui_summary.columns[-len(labels):]
                ):
                row[label[1]] = labels[label[0]]
            self.unsaved = True

    def override_summary(self):
        """
        Avoids the conflict handler algorithm (_N appending)
        and overwrites the current summary file.
        """
        if self.is_summary_loaded():
            self.\
                current_labelgui_summary.\
                    to_csv(self.current_labelgui_summary_filepath)

    def merge_summary(self, import_summary_filepath):
        """
        This function should be used to merge an exported summary file
        (after being annotated) back into the original summary file.

        Notice that it can also be used to annotate unlabelled entries
        that were not exported (i.e. status free instead of exported).

        Params:

        import_summary_filepath <str> - External (e.g exported) summary file
        """
        if self.is_summary_loaded():
            if os.path.isfile(import_summary_filepath):
                merge_df = self._load_csv(import_summary_filepath)
                indices = merge_df[merge_df[self.labels[0]] != -1].index
                for index in indices:
                    if index in self.current_labelgui_summary.index:
                        # Notice that here we update an unlabeled
                        # entry, even if this entry were not exported!
                        if (int(
                            self.current_labelgui_summary.\
                            loc[index][self.labels[0]]) == -1) \
                            and\
                            (int(merge_df.\
                                loc[index][self.labels[0]]) != -1):
                            self.current_labelgui_summary.\
                                loc[index] = merge_df.loc[index]
                self.override_summary()
                self.current_labelgui_summary = \
                    self._load_csv(self.current_labelgui_summary_filepath)

    def update_summary(self, custom_folder=None):
        """
        This function allows multiple image folders to be loaded.

        :param custom_folder=None: Some folder with images
            different from the one opened firstly
        :return:
        """
        if self.is_summary_loaded():
            old_df = self.\
                _load_csv(self.current_labelgui_summary_filepath)
            for img_index in self.current_labelgui_summary[
                self.current_labelgui_summary[
                    self.current_labelgui_summary.\
                        columns[-1]] != '-1'].index:
                old_df.loc[img_index] = \
                    self.current_labelgui_summary.loc[img_index]
            if custom_folder is not None:
                save_folder = os.path.join(
                    custom_folder,
                    self.get_summary_filename()
                    )
            else:
                save_folder = self.current_labelgui_summary_filepath
            old_df.to_csv(
                save_folder,
                sep=',')
            self.unsaved = False

    def _clone_batch_images(self, image_partition):
        """
        Copy the referenced images in a new folder.

        :param image_partition: A pandas dataframe
            with the images to be copied
        :return: None
        """
        try:
            exported_try = 1
            while True:
                new_path = os.path.join(
                    self.current_labelgui_summary_dirpath,
                    f"{self.export_summary_basename}_" + \
                    f"{exported_try}" + \
                    f"{self.summary_filename_ext}"
                )
                if not os.path.exists(new_path):
                    Path(new_path).mkdir(parents=True, exist_ok=False)
                    break
                exported_try += 1
            for i in range(len(image_partition)):
                index = image_partition[i]
                src_img_filepath = \
                    os.path.join(
                        self.current_labelgui_summary_dirpath,
                        index)
                shutil.copy(src_img_filepath, new_path)
            return True
        except:
            return False

    def export_batch(self, batch_size):
        """
        Find free unlabelled entries (those with status free)
        and create another (unlabelled) summary file
        with up until "batch_size" entries.

        The exported entries will have status "exported"
        in the currently opened summary file.

        The exported summary will be named after 

        Params:

        batch_size <int >= 0> - Maximum number of images to export
        """
        if self.is_summary_loaded():
            free_unlabeled_images = \
                self.current_labelgui_summary[
                    (self.current_labelgui_summary.status == 'free') \
                    & (self.current_labelgui_summary[
                        self.current_labelgui_summary.\
                        columns[-1]] == '-1')
                    ].index
            free_unlabeled_images = free_unlabeled_images[:batch_size]
            if self._clone_batch_images(free_unlabeled_images):
                for index in free_unlabeled_images:
                    self.current_labelgui_summary.\
                        loc[index]['status'] = 'exported'
                return True
            else:
                raise Exception("Error while trying to copy exported images.")


    def _load_csv(self, summary_filepath):
        """
        Helper function to read a csv summary file using pandas.

        Params:

        summary_filepath <str> - Path for the summary file.
        """
        return pd.read_csv(summary_filepath,
                    sep=',',
                    dtype='str',
                    index_col=0)


    def merge_summary_files(
        self,
        source_summary,
        target_summary,
        keep_first=False,
        only_labeled=True):
        """
        Insert samples from source_summary file into the
        target_summary summary file.
        Return a new DataFrame with the merged result.
        :param source_summary: First summary file
        :param target_summary: Second summary file
        :param keep_first: Labels from summary_1 will
            prevail in case of conflicts
        :param only_labeled: If True then only labeled
            samples from source_summary will be copied
        :return: DataFrame
        """
        if not os.path.exists(source_summary):
            raise Exception(f"Source summary file {source_summary} can't be found or accessed!")
        if not os.path.exists(target_summary):
            raise Exception(f"Target summary file {target_summary} can't be found or accessed!")
        dt1 = pd.read_csv(source_summary, index_col=0, sep=',')
        dt2 = pd.read_csv(target_summary, index_col=0, sep=',')
        if only_labeled:
            dt1 = dt1[dt1[self.labels[0]] != -1]
        #labeled_samples2 = dt2[labels[0] != -1].copy()
        for sample in dt1.index.values:
            samplein = sample in dt2.index
            if (samplein and keep_first) or (not samplein):
                dt2.loc[sample] = dt1.loc[sample]
        return dt2

    def get_settings_header(self):
        return self._get_headers().split(',')

    def get_summary_header(self, folder_path):
        summary_filepath = os.path.join(folder_path, self.summary_filename)
        df = self._load_csv(summary_filepath)
        file_headers_list = [df.index.name] + list(df.columns.values)
        return file_headers_list

    def compare_summary_headers(self, folder_path):
        """
        Checks if the summary file at 'folder_path' is the
        same as set in the summarymanager_config.txt file.

        It should be used to append new labels in a .smr file.
        """
        current_headers_list = self.get_settings_header()
        file_headers_list = self.get_summary_header(folder_path)
        
        other_headers = []
        present_headers = []
        for col in current_headers_list:
            if col not in file_headers_list:
                other_headers.append(col)
        for col in file_headers_list:
            if col in self.get_default_headers():
                continue
            present_headers.append(col)
        return present_headers, other_headers

    def update_summary_headers(self, folder_path):
        _, new_labels = self.compare_summary_headers(folder_path)
        summary_filepath = os.path.join(
            folder_path,
            self.summary_filename
            )
        df = self._load_csv(summary_filepath)
        if len(new_labels) > 0:
            for label in new_labels:
                df[label] = -1
            df.to_csv(summary_filepath)
        return df
        
    

    def load_images_folder(self, folder_path):
        """
        Loads a summary or creates one based on the
        existing images on the 'folder_path'.

        Params:
        
        folder_path <str> - Folder with images and possible a
            summary file for those images.
        """
        self.current_labelgui_summary_dirpath = folder_path

        for f in os.listdir(folder_path):
            if f.endswith('.png'):
                self.img_filenames.append(f)
        self.current_labelgui_summary_filepath = \
            os.path.join(folder_path, self.get_summary_filename())
        if not os.path.isfile(self.current_labelgui_summary_filepath):
            # @TODO: Show popup asking if the summary file
            # (labelgui.smr) should be created
            with open(self.current_labelgui_summary_filepath, 'w+')\
                as summary_file:
                summary_file.write(self._get_headers())
                summary_file.write('\n')
        df = self._load_csv(self.current_labelgui_summary_filepath)

        # Check for new labels:
        #current_headers_list = self.get_settings_header()
        #file_headers_list = [df.index.name] + list(df.columns.values)
        #file_headers_list = self.get_summary_header(folder_path)
        #updated_labels = False
        #for col in current_headers_list:
        #    if col not in file_headers_list:
        #        df[col] = -1
        #        updated_labels = True
        #if updated_labels:
        #    df.to_csv(self.current_labelgui_summary_filepath)
                
        with open(self.current_labelgui_summary_filepath, 'a+')\
            as summary_file:
            # update file if needed
            for img_filename in self.img_filenames:
                if img_filename in df.index:
                    continue
                else:
                    # img_name, coords(missing), heading, pitch, timestamp(missing), labels...
                    heading_ini_index = \
                        img_filename.find('heading') + \
                            len('heading') + 1
                    heading = \
                        img_filename[heading_ini_index:img_filename.\
                            find('_', heading_ini_index)]
                    pitch_ini_index = img_filename.\
                        find('pitch') + len('pitch') + 1
                    pitch = \
                        img_filename[pitch_ini_index:img_filename.\
                            find('.png', pitch_ini_index)]

                    # -1 (N/A), 0 - Not present, 1 - Present
                    labels_str = '-1'
                    for _ in self.labels[1:]:
                        labels_str += f',-1'
                    # v2: img_name, lat(missing), lon(missing), heading, pitch, timestamp(missing), status, labels...
                    summary_line = (
                        f'{img_filename}'
                        f',missing'
                        f',missing'
                        f',{str(heading)}'
                        f',{str(pitch)}'
                        f',missing'
                        f',free'
                        f',{labels_str}'
                        f'\n'
                    )
                    summary_file.write(summary_line)
            del df
            self.current_labelgui_summary = \
                self._load_csv(self.current_labelgui_summary_filepath)

        # END: for img_filename in img_filenames:
with open('summarymanager_config.txt', 'r') as f:
    for line in f.readlines():
        if (line.startswith('#')) or (line.strip() == ""):
            continue
        try:
            atrib, val = line.split('=')
        except ValueError as e:
            print(f"read line: {line}")
            raise Exception(e)
        atrib = atrib.strip()
        val = val.strip()
        if val.startswith("'") and val.endswith("'"):
            val = val[1:-1]
        if atrib == 'summary_filename_no_ext':
            SummaryManager.\
                summary_filename_no_ext = val
        elif atrib == 'summary_filename_ext':
            SummaryManager.summary_filename_ext = val
        elif atrib == 'labels':
            SummaryManager.labels = val.split(',')
        elif atrib == 'export_summary_basename':
            SummaryManager.export_summary_basename = val
