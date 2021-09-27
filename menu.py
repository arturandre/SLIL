"""
&File     - F
S&ave     - F-A
&images   - F-I
&Load     - F-L
su&mmary  - F-M
&Quit     - F-Q
&Save     - F-S

&Edit     - E
&Go       - E-G
&Export   - E-E
&Merge    - E-M

&Alt.     - A
&folder   - A-F
&Rem.     - A-R
"""

from altimagefolder import AltImageFolder


class Menu:
    def __init__(self, title):
        self.title = title
        self.menu_buttons = []
        self.temp_menu_buttons = []

    def __contains__(self, key):
        if type(key) is not str:
            raise TypeError("The key parameter of Menu[key] must be str. It returns a MenuButton with the same idx if it exists.")
        

        key = key.split("::")[-1]

        for button in self.menu_buttons + self.temp_menu_buttons:
            if button == "-": continue # Separator
            if button.idx == key:
                return True
        return False



    def __getitem__(self, key):
        """
        Get a MenuButton from the property self.menu_buttons with
        'idx' equals 'key' if it exists. Key must be str.
        """
        if type(key) is not str:
            raise TypeError("The key parameter of Menu[key] must be str. It returns a MenuButton with the same idx if it exists.")

        key = key.split("::")[-1]

        for button in self.menu_buttons + self.temp_menu_buttons:
            if button == "-": continue # Separator
            if button.idx == key:
                return button
        raise KeyError(f"No MenuButton with idx = {key} was found!")

    def add_menu_button(self, title, idx, handler=None):
        new_button = MenuButton(title=title, idx=idx, handler=handler)
        self.menu_buttons.append(new_button)
        return new_button
    
    def add_separator(self):
        self.menu_buttons.append('-')
    
    def add_temp_menu_button(self, title, idx, handler=None):
        new_button = MenuButton(title=title, idx=idx, handler=handler)
        self.temp_menu_buttons.append(new_button)
        return new_button

    def reset_temp_menu_buttons(self):
        self.temp_menu_buttons = []
        

    def to_simpleGui_list(self):
        # Optional menu keys are defined with Text::Optional_Key
        menu_buttons = []
        for button in (self.menu_buttons + self.temp_menu_buttons):
            if button == '-':
                menu_buttons.append('---') # Separator
            else:
                menu_buttons.append(button.title + '::' + button.idx)
        menu_tab = [self.title, menu_buttons]
        return menu_tab
    
    def check_handlers(self):
        for button in self.menu_buttons:
            if button == "-": continue # Separator
            if button.handler is None:
                print(f"The menu button '{button.title}' has no handler!")
        pass

class MenuButton:
    def __init__(self, title, idx, handler=None):
        self.title   = title
        if type(idx) is not str:
            raise TypeError("MenuButton 'idx' must be a string")
        self.idx     = idx
        self.handler = handler
    
    def set_handler(self, handler=None):
        self.handler = handler

    def click(self, *args, **kwargs):
        if self.handler is not None:
            self.handler(self, *args, **kwargs)

class FileMenu(Menu):
    def __init__(self):
        super().__init__(title="&File")

        self.add_menu_button('Choose su&mmary file', 'bt_ld_smr')
        self.add_menu_button('Choose &images folder', 'bt_ld_img')
        self.add_menu_button('S&ave labels', 'bt_sv_lbl')
        self.add_menu_button('&Save as labels', 'bt_sv_lbl_as')
        self.add_menu_button('&Load labels', 'bt_ld_lbl')
        self.add_menu_button('&Quit', 'bt_quit')

class EditMenu(Menu):
    def __init__(self):
        super().__init__(title="&Edit")
        self.add_menu_button('&Go to', 'bt_goto')
        self.add_menu_button('&Export batch', 'bt_exp_batch')
        self.add_menu_button('&Merge (import batch)', 'bt_imp_batch')

class AltImageFolderMenu(Menu):
    def __init__(self, altimagefolder):
        """
        The 'altimagefolder' is a Model (MVC) to keep the current
        loaded alternative images folders.
        """
        super().__init__(title="&Alt. Image Folder")
        self.add_menu_button('Add image &folder', 'bt_add_alt_im_fd')
        self.add_menu_button('&Rem. image folder', 'bt_rem_alt_im_fd')
        self.add_separator()
        altimagefolder.register_insert_callback(self._update_loaded_folders)

    def _update_loaded_folders(self, altimagefolder):
        self.reset_temp_menu_buttons()
        for i, loaded_folder in enumerate(altimagefolder.loaded_folders):
            self.add_temp_menu_button(loaded_folder[-15:], f"temp_{i}")


