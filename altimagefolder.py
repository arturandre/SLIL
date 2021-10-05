class AltImageFolder:
    def __init__(self):
        self.loaded_folders = []
        self._on_insert_callbacks = []
        self._on_remove_callbacks = []
        self._current_loaded_folder = -1

    def reset_current_loaded_folder(self):
        self._current_loaded_folder = -1


    def set_current_loaded_folder(self, folder_idx):
        if (folder_idx < 0) or (folder_idx >= len(self.loaded_folders)):
            raise IndexError("Selected folder index out of bounds.")

        self._current_loaded_folder = folder_idx
        return self.loaded_folders[self._current_loaded_folder]

    def get_current_alt_folder(self):
        if self._current_loaded_folder == -1:
            return None
        else:
            return self.loaded_folders[self._current_loaded_folder]

    def get_next_alt_folder(self):
        self._current_loaded_folder += 1

        if self._current_loaded_folder == len(self.loaded_folders):
            self._current_loaded_folder = -1
            return None
        else:
            return self.loaded_folders[self._current_loaded_folder]

    def get_loaded_folders(self):
        return self.loaded_folders

    def insert_folder(self, folder):
        if folder in self.loaded_folders:
            return False
        else:
            self.loaded_folders.append(folder)
            self.on_folder_insert()
            return True
    
    def remove_folder(self, folder_idx):
        if (folder_idx < 0) or (folder_idx > len(self.loaded_folders)):
            return False
        else:
            #self.loaded_folders.remove(folder)
            del self.loaded_folders[folder_idx]
            self.on_folder_remove()
            return True

    def on_folder_insert(self):
        if len(self._on_insert_callbacks) > 0:
            for callback in self._on_insert_callbacks:
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