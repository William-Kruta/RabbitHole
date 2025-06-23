import os
import customtkinter as ctk
from modules.gui.pages.start_page import StartPage
from modules.gui.pages.settings import SettingsPage
from modules.gui.pages.research_page import ResearchPage

from config.config import read_settings
from modules.utils.utils import get_ollama_models

ICON_PATH = os.path.join("assets", "rabbit.ico")


class App(ctk.CTk):
    """
    The main application class, now inheriting from customtkinter.CTk.
    This class controls the window and page switching.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- Configure the main window ---
        self.iconbitmap(ICON_PATH)
        self.title("Rabbit Hole")
        self.geometry("600x550")

        self.settings = read_settings()

        # --- Set the appearance and theme ---
        # Options: "System" (default), "Dark", "Light"
        # Set to "Dark" to match the style of the provided example
        ctk.set_appearance_mode("Dark")
        # Options: "blue" (default), "green", "dark-blue"
        ctk.set_default_color_theme("blue")

        self.recursion_depth = self.settings["recursion_depth"]
        self.research_config = self.settings
        self.available_models = get_ollama_models()

        # --- The container frame ---
        # This frame holds all the pages (other frames).
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        # Loop through a tuple of page classes to initialize them
        for F in (StartPage, SettingsPage, ResearchPage):
            page_name = F.__name__
            # Create an instance of the page
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            # Place the frame in the grid. It will be stacked with other frames.
            frame.grid(row=0, column=0, sticky="nsew")

        # Show the initial page
        self.show_frame("StartPage")

    def show_frame(self, page_name):
        """
        Raises the specified frame to the top of the stacking order, making it visible.
        """
        frame = self.frames[page_name]
        frame.tkraise()
