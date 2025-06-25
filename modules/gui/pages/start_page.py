import os
import customtkinter as ctk
from PIL import Image

LOGO = os.path.join("assets", "rabbit_thumbnail_2.png")

dimensions = {"logo": (500, 500)}


class StartPage(ctk.CTkFrame):
    """
    The landing page of the application, with a research-style layout.
    Inherits from customtkinter.CTkFrame.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="black")
        self.controller = controller
        self.configure(fg_color="black")

        # --- Widgets for the StartPage (recreating the new layout) ---

        try:
            # Create a CTkImage object
            logo_image = ctk.CTkImage(
                light_image=Image.open(LOGO),
                dark_image=Image.open(LOGO),
                size=dimensions["logo"],
            )  # Adjust size as needed

            # Create the label with the image
            self.image_label = ctk.CTkLabel(self, image=logo_image, text="")
        except FileNotFoundError:
            # Fallback to text if the image is not found
            self.image_label = ctk.CTkLabel(
                self, text="[Your Logo/Image Here]", font=ctk.CTkFont(size=18)
            )

        self.image_label.place(relx=0.5, rely=0.2, anchor="center")

        # Frame holding search bar and send button
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.place(relx=0.5, rely=0.6, anchor="center")

        # Search entry
        self.search_var = ctk.StringVar()
        entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            width=400,
            font=ctk.CTkFont(size=18),
            placeholder_text="Enter your research topic...",
        )
        entry.grid(row=0, column=0, padx=(0, 10), ipady=5)
        entry.bind("<Return>", lambda event: self.start_research())

        # Send button
        send_button = ctk.CTkButton(
            search_frame,
            text=">",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.start_research,
            width=40,
            height=35,
        )
        send_button.grid(row=0, column=1)

        # Placeholder for loading feedback
        self.loading_label = ctk.CTkLabel(self, text="")
        self.loading_label.place(relx=0.5, rely=0.85, anchor="center")

        # Settings button in the bottom right corner
        settings_button = ctk.CTkButton(
            self,
            text="⚙",
            font=ctk.CTkFont(size=20),
            command=self.open_settings,
            width=30,
            fg_color="transparent",
            text_color=("gray70", "gray30"),
            hover_color=("gray90", "gray10"),
        )
        settings_button.place(relx=0.98, rely=0.98, anchor="se")

    def start_research(self):
        """Placeholder function for starting research."""
        query = self.search_var.get()
        if not query.strip():
            self.loading_label.configure(text="Please enter a research topic.")
            return

        # Get the research page frame from the controller
        research_page = self.controller.frames["ResearchPage"]

        # Call a method on the research page to initialize it with the new query
        research_page.start_new_research(query)

        # Switch to the research page
        self.controller.show_frame("ResearchPage")

    def open_settings(self):
        """Placeholder function for opening settings."""
        self.controller.show_frame("SettingsPage")
