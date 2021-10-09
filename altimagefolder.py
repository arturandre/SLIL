class AltImageFolder:
    def __init__(self):
        #self.loaded_folders = []
        self.loaded_folders = {}
        self._on_insert_callbacks = []
        self._on_current_folder_changed = []
        self._on_remove_callbacks = []
        self._current_loaded_folder = -1

    def reset_current_loaded_folder(self):
        self._current_loaded_folder = -1


    def set_current_loaded_folder(self, folder_idx):
        #if (folder_idx < 0) or (folder_idx >= len(self.loaded_folders)):
        if (folder_idx < 0) or (folder_idx >= len(self.loaded_folders.keys())):
            raise IndexError("Selected folder index out of bounds.")

        self._current_loaded_folder = folder_idx
        return self.get_current_alt_folder()

    def get_current_alt_folder(self):
        if self._current_loaded_folder == -1:
            return None
        else:

            return list(self.loaded_folders.keys())[self._current_loaded_folder]

    def get_next_alt_folder(self):
        self._current_loaded_folder += 1

        if self._current_loaded_folder == len(self.loaded_folders):
            self._current_loaded_folder = -1
        
        return self.get_current_alt_folder()

    def get_loaded_folders(self):
        return self.loaded_folders

    def insert_folder(self, folder, summary):
        # if folder in self.loaded_folders:
        #     return False
        # else:
        #     self.loaded_folders.append(folder)
        #     self.on_folder_insert()
        #     return True
        if (folder in self.loaded_folders) and (self.loaded_folders[folder] == summary):
                return False
        else:
            self.loaded_folders[folder] = summary
            self.on_folder_insert()
            return True
    
    def remove_folder(self, folder_idx):
        if (folder_idx < 0) or (folder_idx > len(self.loaded_folders)):
            return False
        else:
            #self.loaded_folders.remove(folder)
            del self.loaded_folders[list(self.loaded_folders.keys())[folder_idx]]
            self.on_folder_remove()
            return True

    def on_folder_insert(self):
        if len(self._on_insert_callbacks) > 0:
            for callback in self._on_insert_callbacks:
                callback(self)

    def on_current_folder_changed(self):
        if len(self._on_current_folder_changed) > 0:
            for callback in self._on_current_folder_changed:
                callback(self)
    
    def on_folder_remove(self):
        if len(self._on_remove_callbacks) > 0:
            for callback in self._on_remove_callbacks:
                callback(self)
    
    def register_insert_callback(self, callback):
        if callback in self._on_insert_callbacks:
            return False
        else:
            self._on_insert_callbacks.append(callback)
            return True

    def unregister_insert_callback(self, callback):
        if callback not in self._on_insert_callbacks:
            return False
        else:
            self._on_insert_callbacks.remove(callback)
            return True

    def register_folder_changed_callback(self, callback):
        if callback in self._on_current_folder_changed:
            return False
        else:
            self._on_current_folder_changed.append(callback)
            return True

    def unregister_folder_changed_callback(self, callback):
        if callback not in self._on_current_folder_changed:
            return False
        else:
            self._on_current_folder_changed.remove(callback)
            return True

    def register_remove_callback(self, callback):
        if callback in self._on_remove_callbacks:
            return False
        else:
            self._on_remove_callbacks.append(callback)
            return True

    def unregister_remove_callback(self, callback):
        if callback not in self._on_remove_callbacks:
            return False
        else:
            self._on_remove_callbacks.remove(callback)
            return True

# Singleton
altimagefolder = AltImageFolder()