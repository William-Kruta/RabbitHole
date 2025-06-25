import os
import threading
from tkinter import filedialog
import customtkinter as ctk
from PIL import Image, ImageSequence
import queue
import random
from modules.research.research import DeepResearch
from modules.research.llm import LLM
from config.config import read_settings


GIF_PATH = os.path.join("assets", "loading_2.gif")


GIFS = [
    {"path": os.path.join("assets", "loading_2.gif"), "dim": (200, 113)},
    {"path": os.path.join("assets", "hole_jump_1.gif"), "dim": (200, 113)},
    {"path": os.path.join("assets", "hole_jump_2.gif"), "dim": (200, 113)},
    {"path": os.path.join("assets", "hole_jump_3.gif"), "dim": (200, 113)},
    {"path": os.path.join("assets", "hole_jump_4.gif"), "dim": (200, 113)},
]


dimensions = {"gif": (200, 113)}


class ResearchPage(ctk.CTkFrame):
    """
    A page to display the status of a research task, with an animated GIF.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="black")
        settings = read_settings()
        self.controller = controller
        # --- Setup Queue for thread-safe GUI updates ---
        self.update_queue = queue.Queue()
        # Instantiate the research class, passing it our update method as a callback
        self.deep_research = DeepResearch(status_callback=self.queue_status_update)
        self.chat_model_name = settings["model"]["chat"]["model_name"]
        self.chat_context_window = settings["model"]["chat"]["context_window"]
        self.chat_agent = LLM(
            self.chat_model_name,
            system_prompt="You are a chat agent. Help the user with questions no matter the topic.",
        )

        # Configure a 2-column grid. Column 0 for text, Column 1 for GIF.
        self.grid_columnconfigure(0, weight=1)  # Status box gets more space
        self.grid_columnconfigure(1, weight=1)  # GIF gets less space

        # Title Label
        self.title_label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=20)

        # Status Box
        self.status_box = ctk.CTkTextbox(
            self, width=50, height=300, font=ctk.CTkFont(size=14)
        )
        self.status_box.grid(row=2, column=0, padx=(20, 10), pady=10, sticky="nsew")
        self.status_box.configure(state="disabled")
        # Chat Interface
        self.chat_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.chat_frame.grid(row=2, column=1, padx=(10, 20), pady=10, sticky="nsew")
        self.chat_frame.grid_rowconfigure(0, weight=1)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        # Chat history
        self.chat_history = ctk.CTkScrollableFrame(self.chat_frame, fg_color="gray17")
        self.chat_history.grid(row=0, column=0, sticky="nsew")

        # User Input
        # User input area
        input_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        input_frame.grid_columnconfigure(0, weight=1)

        self.user_entry = ctk.CTkEntry(
            input_frame, placeholder_text="Ask a follow-up question..."
        )
        self.user_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.user_entry.bind("<Return>", self._send_user_message)
        send_button = ctk.CTkButton(
            input_frame, text="Send", width=70, command=self._send_user_message
        )
        send_button.grid(row=0, column=1)
        # GIF Label
        self.gif_label = ctk.CTkLabel(self, text="")
        self.gif_label.grid(row=4, column=0, padx=(10, 20), pady=10, sticky="nsew")

        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal")
        self.progress_bar.grid(
            row=3, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew"
        )
        self.progress_bar.set(0)

        # Back Button
        self.back_button = ctk.CTkButton(
            self, text="New Research", command=self._stop_and_go_back
        )
        self.back_button.grid(row=1, column=0, columnspan=2, padx=20, pady=20)
        self.download_button = ctk.CTkButton(
            self, text="Download Report", command=self._save_report
        )
        self.download_button.grid(row=1, column=1, columnspan=2, padx=20, pady=20)
        # self.download_button.grid_remove()
        # --- GIF Animation Attributes ---
        self.gif_frames = []
        self.animation_job = None
        self._load_gif()
        self._process_queue()

    def _load_gif(self):
        """Loads GIF frames into a list."""
        choice = GIFS[0]
        # random.choice(GIFS)
        print(f"CHOICE: {choice}")
        try:
            # Assumes a 'loading.gif' file in the same directory
            gif_image = Image.open(choice["path"])
            for frame in ImageSequence.Iterator(gif_image):
                ctk_frame = ctk.CTkImage(
                    light_image=frame.copy().resize(choice["dim"]),
                    size=dimensions["gif"],
                )
                self.gif_frames.append(ctk_frame)
        except FileNotFoundError:
            self.gif_label.configure(text="GIF not found")
            print("loading.gif not found. Please add it to the script's directory.")

    def _animate_gif(self, frame_index):
        """Updates the GIF label with the next frame."""
        if self.gif_frames:
            frame = self.gif_frames[frame_index]
            self.gif_label.configure(image=frame)
            next_frame_index = (frame_index + 1) % len(self.gif_frames)
            self.animation_job = self.after(
                100, self._animate_gif, next_frame_index
            )  # 100ms delay

    def _stop_animation(self):
        """Stops the GIF animation loop."""
        if self.animation_job:
            self.after_cancel(self.animation_job)
            self.animation_job = None
            self.gif_label.configure(image=None)  # Clear the image

    def _save_report(self):
        """Opens a file dialog to save the final report."""
        print(f"REPORT CLICKED")
        print(f"DEEP: {self.deep_research.get_report()}")
        if self.deep_research.report == "":
            pass
        else:
            topic = self.title_label.cget("text").replace("Researching: ", "")
            #   Sanitize the topic to create a valid filename
            sanitized_topic = "".join(
                c for c in topic if c.isalnum() or c in (" ", "_")
            ).rstrip()
            report_text = self.deep_research.report
            filepath = filedialog.asksaveasfilename(
                initialfile=f"{sanitized_topic}.md",  # Pre-fill the filename
                defaultextension=".md",
                filetypes=[
                    ("Markdown Files", "*.md"),
                    ("Text Files", "*.txt"),
                    ("All Files", "*.*"),
                ],
                title="Save Research Report",
            )
            if filepath:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(report_text)
                print(f"Report saved to {filepath}")

    def _stop_and_go_back(self):
        """Stops animation and returns to the start page."""
        self._stop_animation()
        self.controller.show_frame("StartPage")

    def queue_status_update(self, message_tuple):
        """This method is called by the DeepResearch thread to add an update to the queue."""
        self.update_queue.put(message_tuple)

    def _process_queue(self):
        """Checks the queue for messages and updates the GUI. Runs on the main thread."""
        try:
            while not self.update_queue.empty():
                message, current_step, max_steps = self.update_queue.get_nowait()
                self.status_box.configure(state="normal")
                self.status_box.insert("end", f"{message}\n")
                self.status_box.see("end")  # Auto-scroll to the bottom
                self.status_box.configure(state="disabled")
                if max_steps > 0:
                    progress_value = float(current_step) / float(max_steps)
                    self.progress_bar.set(progress_value)
                    # When research is complete
                    if progress_value >= 1.0:
                        self._stop_animation()
                        # self.gif_label.grid_remove()  # Hide GIF
                        # self.back_button.grid_remove()  # Hide "New Research" button
                        # self.download_button.grid()  # Show "Download" button

        finally:
            # Schedule itself to run again
            self.after(100, self._process_queue)

    def _add_chat_bubble(self, message, sender):
        """Adds a new message bubble to the chat history."""
        if sender == "user":
            bubble = ctk.CTkLabel(
                self.chat_history,
                text=message,
                fg_color="#007AFF",
                text_color="white",
                corner_radius=15,
                wraplength=250,
                justify="left",
                anchor="w",
            )
            bubble.pack(anchor="e", padx=10, pady=5)
        else:  # assistant
            bubble = ctk.CTkLabel(
                self.chat_history,
                text=message,
                fg_color="#E5E5EA",
                text_color="black",
                corner_radius=15,
                wraplength=250,
                justify="left",
                anchor="w",
            )
            bubble.pack(anchor="w", padx=10, pady=5)

        # Auto-scroll to the bottom
        self.after(100, self.chat_history._parent_canvas.yview_moveto, 1.0)

    def _send_user_message(self, event=None):
        """Handles sending a message from the user entry."""
        user_message = self.user_entry.get()
        if not user_message.strip():
            return

        self._add_chat_bubble(user_message, "user")
        self.user_entry.delete(0, "end")

        chat_response = self.chat_agent.get_response(
            user_message, self.chat_context_window
        )
        self._add_chat_bubble(chat_response, "assistant")

        # self.after(500, self._add_chat_bubble, chat_response, "assistant")

    def start_new_research(self, query):
        """Resets the page and starts the research process in a new thread."""
        settings = read_settings()
        print(f"SETTINGS: {settings}")
        self.title_label.configure(text=f"Researching: {query}")
        self.status_box.configure(state="normal")
        self.status_box.delete("1.0", "end")
        self.status_box.configure(state="disabled")
        self._stop_animation()
        self._animate_gif(0)

        # --- Create and start the research thread ---
        thread = threading.Thread(
            target=self.deep_research.start_research,
            args=(query, int(settings["recursion_depth"])),
            daemon=True,
        )
        thread.start()
