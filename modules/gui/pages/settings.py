import customtkinter as ctk
from config.config import write_settings


class SettingsPage(ctk.CTkFrame):
    """
    A page for configuring application settings, including agent models.
    """

    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="black")
        self.controller = controller

        self.context_vars = {}
        self.model_vars = {}  # To hold variables for the dropdowns

        title_label = ctk.CTkLabel(
            self, text="Settings", font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 20))

        # --- Header Labels ---
        ctk.CTkLabel(self, text="Agent", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=10
        )
        ctk.CTkLabel(self, text="Context Window", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=1, padx=10
        )
        ctk.CTkLabel(self, text="Model", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=2, padx=10
        )

        # --- Recursion depth setting (moved for better layout) ---
        ctk.CTkLabel(self, text="Recursion Depth:").grid(
            row=2, column=0, sticky="w", padx=10, pady=8
        )
        self.recursion_depth_var = ctk.StringVar(value=self.controller.recursion_depth)
        ctk.CTkEntry(self, textvariable=self.recursion_depth_var, width=120).grid(
            row=2, column=1, padx=10, pady=8
        )

        # --- Context window and model settings for each agent ---
        agents = ["analyst", "critic", "explorer", "synthesizer", "web_searcher"]
        for idx, agent in enumerate(agents, start=3):
            # Agent Name Label
            ctk.CTkLabel(self, text=f"{agent.capitalize()}").grid(
                row=idx, column=0, sticky="w", padx=10, pady=8
            )

            # Context Window Entry
            initial_context = self.controller.research_config["model"][agent][
                "context_window"
            ]
            context_var = ctk.StringVar(value=initial_context)
            self.context_vars[agent] = context_var
            ctk.CTkEntry(self, textvariable=context_var, width=120).grid(
                row=idx, column=1, padx=10, pady=8
            )

            # Model Dropdown
            initial_model = self.controller.research_config["model"][agent][
                "model_name"
            ]
            model_var = ctk.StringVar(value=initial_model)
            self.model_vars[agent] = model_var
            model_menu = ctk.CTkOptionMenu(
                self, variable=model_var, values=self.controller.available_models
            )
            model_menu.grid(row=idx, column=2, padx=10, pady=8)

        # --- Save button ---
        save_btn = ctk.CTkButton(
            self, text="Save and Return", command=self.save_settings
        )
        save_btn.grid(row=len(agents) + 3, column=0, columnspan=3, pady=(20, 10))

        # Center the grid layout in the frame
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

    def save_settings(self):
        """Saves the current settings and returns to the StartPage."""
        try:
            self.controller.recursion_depth = int(self.recursion_depth_var.get())
        except ValueError:
            print("Invalid input for recursion depth. Must be an integer.")
        new_settings = {"recursion_depth": self.recursion_depth_var.get(), "model": {}}
        for agent, var in self.context_vars.items():
            try:
                self.controller.research_config["model"][agent]["context_window"] = int(
                    var.get()
                )
                new_settings["model"][agent] = {
                    "context_window": int(var.get()),
                    "model_name": "",
                }
            except ValueError:
                print(f"Invalid input for {agent} context window. Must be an integer.")

        for agent, var in self.model_vars.items():
            self.controller.research_config["model"][agent]["model_name"] = var.get()
            new_settings["model"][agent]["model_name"] = var.get()

        print("\n--- Settings Saved ---")
        print(f"Recursion Depth: {self.controller.recursion_depth}")
        for agent, config in self.controller.research_config["model"].items():
            print(
                f"{agent.capitalize()} -> Context: {config['context_window']}, Model: {config['model_name']}"
            )
        print("----------------------\n")
        write_settings(new_settings)

        self.controller.show_frame("StartPage")
