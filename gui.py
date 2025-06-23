import os
import tkinter as tk
import threading
from modules.research.research import DeepResearch
from PIL import Image, ImageTk
from config.config import read_settings, write_settings, read_research_config

# Default research configuration; update models and context_windows as needed
# default_config = {
#     "analyst": {"model": "your-analyst-model", "context_window": 4096},
#     "critic": {"model": "your-critic-model", "context_window": 4096},
#     "explorer": {"model": "your-explorer-model", "context_window": 4096},
#     "synthesizer": {"model": "your-synthesizer-model", "context_window": 4096},
#     "web_searcher": {"model": "your-web-searcher-model", "context_window": 4096},
# }


# Default recursion depth for research
DEFAULT_RECURSION_DEPTH = 2
ICON_PATH = os.path.join("assets", "rabbit.ico")
IMAGE_PATH = os.path.join("assets", "rabbit_thumbnail_2.png")

# Loading
LOADING_GIF_PATH = os.path.join("assets", "loading_2.gif")
GIF_FRAME_DELAY = 100
PLACEHOLDER_SIZE = (128, 128)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rabbit Hole")
        self.configure(bg="black")
        self.geometry("800x400")
        self.resizable(False, False)
        self.iconbitmap("assets\\rabbit.ico")
        img = tk.PhotoImage(file="assets\\rabbit_final_transparent.png")
        self.iconphoto(False, img)

        # Placeholder label for an image above the search bar
        self.image_label = tk.Label(self, bg="black")
        # Centered near the top
        self.image_label.place(relx=0.5, rely=0.2, anchor="center")

        # Research parameters
        self.recursion_depth = DEFAULT_RECURSION_DEPTH
        self.research_config = read_settings()
        self.context_vars = {}

        # Frame holding search bar and settings button
        frame = tk.Frame(self, bg="black")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        # Search entry
        self.search_var = tk.StringVar()
        entry = tk.Entry(
            frame, textvariable=self.search_var, width=50, font=("Arial", 14)
        )
        entry.grid(row=0, column=0, padx=(0, 10))
        entry.bind("<Return>", lambda event: self.start_research())

        # Send button (replaces settings)
        send_button = tk.Button(
            frame,
            text=">",
            font=("Arial", 14),
            command=self.start_research,
            bg="black",
            fg="white",
            bd=0,
        )
        send_button.grid(row=0, column=1)
        # Video player for feedback beneath search bar
        self.loading_label = tk.Label(self, bg="black")
        self.loading_label.place(
            relx=0.5, rely=0.9, anchor="center", width=150, height=150
        )
        self.loading_frames = []
        self._animating = False
        # Settings button moved to bottom right
        settings_button = tk.Button(
            self,
            text="⚙",
            font=("Arial", 14),
            command=self.open_settings,
            bg="black",
            fg="white",
            bd=0,
        )
        # place at bottom-right corner
        settings_button.place(relx=0.98, rely=0.98, anchor="se")

    def open_settings(self):
        """Open a settings window to adjust recursion depth and context windows."""
        win = tk.Toplevel(self)
        win.title("Settings")
        win.configure(bg="black")
        win.resizable(False, False)

        # Recursion depth setting
        tk.Label(win, text="Recursion Depth:", bg="black", fg="white").grid(
            row=0, column=0, sticky="w", padx=10, pady=5
        )
        self.recursion_depth_var = tk.IntVar(value=self.recursion_depth)
        tk.Spinbox(
            win, from_=1, to=10, textvariable=self.recursion_depth_var, width=5
        ).grid(row=0, column=1, padx=10, pady=5)

        # Context window settings for each agent
        agents = ["analyst", "critic", "explorer", "synthesizer", "web_searcher"]
        for idx, agent in enumerate(agents, start=1):
            tk.Label(
                win,
                text=f"{agent.capitalize()} Context Window:",
                bg="black",
                fg="white",
            ).grid(row=idx, column=0, sticky="w", padx=10, pady=5)
            var = tk.IntVar(
                value=self.research_config["model"][agent]["context_window"]
            )
            self.context_vars[agent] = var
            tk.Spinbox(
                win, from_=100, to=100_000, increment=100, textvariable=var, width=7
            ).grid(row=idx, column=1, padx=10, pady=5)

        # Save button
        save_btn = tk.Button(
            win,
            text="Save",
            command=lambda: self.save_settings(win),
            bg="black",
            fg="white",
        )
        save_btn.grid(row=len(agents) + 1, column=0, columnspan=2, pady=10)

    def save_settings(self, win):
        """Save settings from the settings window and close it."""
        new_settings = {}
        self.recursion_depth = self.recursion_depth_var.get()
        print(f"RESEARCH :{self.research_config}")
        new_settings["recursion_depth"] = self.recursion_depth_var.get()
        new_settings["model"] = {}
        for agent, var in self.context_vars.items():
            print(f"RESEARCH: {self.research_config['model'][agent]}")
            self.research_config["model"][agent]["context_window"] = var.get()
            new_settings["model"][agent] = {"context_window": var.get()}

        write_settings(new_settings)
        win.destroy()

    def start_research(self):
        """Start the research process in a separate thread to keep the UI responsive."""
        topic = self.search_var.get().strip()
        if not topic:
            return
        self.play_loading()
        threading.Thread(target=self.run_research, args=(topic,), daemon=True).start()

    def run_research(self, topic):
        """Instantiate DeepResearch and run research with the current settings."""
        dr = DeepResearch(read_research_config(), show_progress=True)
        dr.run_research(topic, recursion_depth=self.recursion_depth)
        self.after(0, self.stop_loading)

    def set_image(self, widget: tk.Label, image_path: str, width=None, height=None):

        img = Image.open(image_path)
        if width and height:
            img = img.resize((width, height), Image.LANCZOS)
            widget.place_configure(width=width, height=height)
        else:
            # use placeholder size
            width, height = PLACEHOLDER_SIZE
            img = img.resize((width, height), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(img)
        widget.config(image=tk_img)
        widget.image = tk_img

    def play_loading(self):
        print(f"Playing Animation")
        """Start the loading animation beneath the search bar."""
        if self.loading_frames:
            self._animating = True
            self._animate(0)

    def stop_loading(self):
        """Stop and clear the loading animation."""
        self._animating = False
        self.loading_label.config(image="")

    def _animate(self, idx=0):
        """Internal: cycle through GIF frames."""
        if not self._animating or not self.loading_frames:
            return
        frame = self.loading_frames[idx]
        self.loading_label.config(image=frame)
        next_idx = (idx + 1) % len(self.loading_frames)
        self.after(GIF_FRAME_DELAY, lambda: self._animate(next_idx))

    def _load_gif_frames(self):
        """Load GIF frames into memory."""
        try:
            gif = Image.open(LOADING_GIF_PATH)
            frame_index = 0
            while True:
                gif.seek(frame_index)
                frame = ImageTk.PhotoImage(
                    gif.copy().convert("RGBA").resize((150, 150), Image.LANCZOS)
                )
                self.loading_frames.append(frame)
                frame_index += 1
        except EOFError:
            pass  # end of frames
        except Exception:
            self.loading_frames = []


if __name__ == "__main__":
    app = App()
    app.set_image(
        app.image_label, "assets\\rabbit_thumbnail_2.png", width=200, height=200
    )
    app.mainloop()
