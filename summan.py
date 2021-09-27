import shutil
from pathlib import Path
import os
import pandas as pd


class SummaryManager:
    unlabeled_code = '-10'
    positive_label = '1'
    negative_label = '-1'
    uncertain_label = '0'


    def _reset_images_folder(self):
        """
        Resets the list holding the list of image names of
        the current session. Notice that if the summary file
        is loaded it will be kept.
        
        """
        self.img_filenames = []
        self.imgs_folder = None

    def _reset_labelgui_summary(self):
        """
        Resets the currently loaded summary file, and folder.
        Notice that if there are any image folder loaded it will
        be kept as it is.
        """
        self.current_labelgui_summary_dirpath = None
        self.current_labelgui_summary_filepath = None
        self.current_labelgui_summary = None
        self.unsaved = False


    def _reset_session(self):
        self._reset_images_folder()
        self._reset_labelgui_summary()

    def __init__(self, custom_config={}):
        # customizable configs
        self.summary_filename_no_ext = \
            custom_config.get('summary_filename_no_ext')\
            or SummaryManager.summary_filename_no_ext
        self.summary_filename_ext = \
            custom_config.get('summary_filename_ext')\
            or SummaryManager.summary_filename_ext

        self.labels = custom_config.get('labels')\
            or SummaryManager.labels
        self.label_dependents = {}
        self._check_labels_dependencies()
        

        self.export_summary_basename =\
            custom_config.get('export_summary_basename')\
            or SummaryManager.export_summary_basename
        self.summary_filename = ((
            f"{self.summary_filename_no_ext}"
            f"{self.summary_filename_ext}"
        ))

        self._reset_session()
        pass

    def _check_labels_dependencies(self):
        self.label_dependents = {}
        for i, label in enumerate(self.labels):
            if '>' in label:
                label, dependencies = label.split('>')
                # Removing the '(' and ')' characters"
                dependencies = dependencies[1:-1]
                self.labels[i] = label
                self.label_dependents[label] = dependencies.split('+')

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
        if self._is_summary_loaded():
            return self.current_labelgui_summary[
                self.current_labelgui_summary[
                    self.labels[0]
                    ] != SummaryManager.unlabeled_code]


    def count_labeled_samples(self):
        """
        This function returns the number of
        entries of the opened summary file that
        are annotated.
        """
        if self._is_summary_loaded():
            return len(self.get_labeled_samples())
    
    def count_samples(self):
        """
        Returns how many images are referenced at the loaded
        summary file.
        """
        if self._is_summary_loaded():
            return len(self.current_labelgui_summary)

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

    def _is_summary_loaded(self):
        """
        Checks if some summary file is currently loaded
        """
        return self.current_labelgui_summary is not None

    def _is_images_folder_loaded(self):
        """
        Checks if a folder with images and the images themselves are loaded.
        """
        return self.imgs_folder is not None
    
    def is_summan_ready(self):
        """
        Checks if a summary file and images are loaded to be presented.
        """
        return self._is_summary_loaded() and self._is_images_folder_loaded()

    def save_sample_labels(self, index, labels):
        """
        Stash the changes to the labels to the
        currently in-memory summary file.

        Params:

        index <int> - Row of the entry to be stashed
        labels <Tuple<int>> - Values to be stashed in the labels
            section (last fields) of the 'index' rox.
        """
        if self._is_summary_loaded():
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
        if self._is_summary_loaded():
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
        if self._is_summary_loaded():
            if os.path.isfile(import_summary_filepath):
                merge_df = self._load_csv(import_summary_filepath)
                indices = merge_df[merge_df[self.labels[0]] != \
                    int(SummaryManager.unlabeled_code)].index
                for index in indices:
                    if index in self.current_labelgui_summary.index:
                        # Notice that here we update an unlabeled
                        # entry, even if this entry were not exported!
                        if (int(
                            self.current_labelgui_summary.\
                            loc[index][self.labels[0]]) == \
                                int(SummaryManager.unlabeled_code)) \
                            and\
                            (int(merge_df.\
                                loc[index][self.labels[0]]) != \
                                    int(SummaryManager.unlabeled_code)):
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
        if self._is_summary_loaded():
            old_df = self.\
                _load_csv(self.current_labelgui_summary_filepath)
            for img_index in self.current_labelgui_summary[
                self.current_labelgui_summary[
                    self.current_labelgui_summary.\
                        columns[-1]] != SummaryManager.unlabeled_code].index:
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
        if self._is_summary_loaded():
            free_unlabeled_images = \
                self.current_labelgui_summary[
                    (self.current_labelgui_summary.status == 'free') \
                    & (self.current_labelgui_summary[
                        self.current_labelgui_summary.\
                        columns[-1]] == SummaryManager.unlabeled_code)
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
            dt1 = dt1[dt1[self.labels[0]] != \
                int(SummaryManager.unlabeled_code)]
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
                df[label] = int(SummaryManager.unlabeled_code)
            df.to_csv(summary_filepath)
        return df
        
    def load_summary_file(self, filepath):
        """
        Loads just the summary file. Notice that after loading
        the summary file an images folder must be loaded as well.
        """

        self._reset_session()

        if os.path.isfile(filepath):
            self.current_labelgui_summary_filepath = filepath
            self.current_labelgui_summary_dirpath = os.path.split(filepath)[0]
            self.current_labelgui_summary = self._load_csv(filepath)
        else:
            raise Exception("Summary file could not be open or accessed")


    def load_images_folder(self, folder_path):
        """
        Sets the images list of the session as the images
        referenced in the loaded summary file and present in
        the 'folder_path' argument.

        If no summary is loaded then this function tries to
        load one from the 'folder_path' with the name configured
        in the configuration file **summarymanager_config.txt**.

        If there is no summary file with the name defined in the 
        configuration file, then an exception is raised.
        
        Params:
        
        folder_path <str> - Folder with images and possible a
            summary file for those images.
        """

        self._reset_images_folder()


        if self.current_labelgui_summary_filepath is None:

            # If there is no summary file loaded then one is loaded from the
            # 'folder_path' if possible.
            #
            # Get the name of summan file as defined in the configuration file
            # and checks if there is an summary file at 'folder_path'
            summary_filepath = os.path.join(folder_path, self.get_summary_filename())
            if os.path.isfile(summary_filepath):
                self.current_labelgui_summary_filepath = summary_filepath
                self.current_labelgui_summary_dirpath = folder_path
                self.current_labelgui_summary = self._load_csv(summary_filepath)
            else:
                # Asks if the user wants to create a summary file at 'folder_path' using the
                # '.png' images available in the folder and the classes defined in the configuration file.
                raise Exception(
                    f'Summary file not loaded and not found in the images folder. '
                    f'Try to load a summary file first, or create one (File->Create summary in folder).'
                    )
        else:
            for f in os.listdir(folder_path):
                if f.endswith('.png'):
                    self.img_filenames.append(f)
            self.imgs_folder = folder_path
            pass



    def load_image_create_summary(self, folder_path):
        """
        Creates a summary file, named according to the configuration file,
        at 'folder_path', referencing '.png' images in the folder.

        If a summary file with the same name already exists in the folder then
        an exception will be raised.
        one will be created at 'folder_path'
        and the created summary file will reference the images inside
        the folder at 'folder_path'.
        """

        self._reset_session()

        summary_filepath = os.path.join(folder_path, self.get_summary_filename())
        if os.path.isfile(summary_filepath):
            raise Exception(
                f"Summary file found at the images folder. "
                f"Load the image folder using (File -> Load images folder)."
                )

        for f in os.listdir(folder_path):
            if f.endswith('.png'):
                self.img_filenames.append(f)
        with open(self.current_labelgui_summary_filepath, 'w+')\
            as summary_file:
            summary_file.write(self._get_headers())
            summary_file.write('\n')
        df = self._load_csv(self.current_labelgui_summary_filepath)
        
                
        with open(summary_filepath, 'a+')\
            as summary_file:
            # update file if needed
            for img_filename in self.img_filenames:
                heading_ini_index = img_filename.find('heading') + len('heading') + 1
                heading = img_filename[heading_ini_index:img_filename.find('_', heading_ini_index)]
                pitch_ini_index = img_filename.find('pitch') + len('pitch') + 1
                pitch = img_filename[pitch_ini_index:img_filename.find('.png', pitch_ini_index)]

                # -10 -> unlabeled_code,-1 -> Not present, 0 -> Uncertain, 1 -> Present
                labels_str = SummaryManager.unlabeled_code
                for _ in self.labels[1:]:
                    labels_str += f',{SummaryManager.unlabeled_code}'
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
        self.current_labelgui_summary = self._load_csv(summary_filepath)
        self.current_labelgui_summary_filepath = summary_filepath
        self.current_labelgui_summary_dirpath = folder_path



dirname = os.path.dirname(__file__)
summary_filename = os.path.join(dirname, 'summarymanager_config.txt')
with open(summary_filename, 'r') as f:
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
