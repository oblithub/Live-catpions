import customtkinter as ctk
import tkinter # For constants like tkinter.BOTTOM
import config_manager # For accessing config settings
import logging # Added for logging

class CaptionWindow(ctk.CTkFrame):
    """
    A CustomTkinter Frame that serves as the GUI window for displaying live captions.
    It includes a label for the captions, a Start/Stop button, and a placeholder for the heatmap.
    """
    def __init__(self, master, app_ref, config): # Pass config for heatmap placeholder height
        super().__init__(master)
        self.app = app_ref 
        self.config = config

        self.caption_label = ctk.CTkLabel(self, text="Initializing...", font=("Arial", 20), wraplength=780)
        self.caption_label.pack(side=tkinter.TOP, pady=(10,0), padx=20, expand=True, fill="both")

        heatmap_max_h = config_manager.getint_setting(self.config, 'GUI', 'heatmap_bar_max_height', fallback=50)
        # Placeholder frame for the heatmap, GUIManager will populate this.
        self.heatmap_placeholder_frame = ctk.CTkFrame(self, height=heatmap_max_h + 10, fg_color="transparent")
        self.heatmap_placeholder_frame.pack(side=tkinter.TOP, fill=tkinter.X, pady=5, padx=5) # Pack after label

        self.start_stop_button = ctk.CTkButton(self, text="Loading...", command=self.toggle_captioning)
        self.start_stop_button.pack(side=tkinter.BOTTOM, pady=5) # Pack button last
        
        self.pack(expand=True, fill="both") 

    def toggle_captioning(self):
        if self.app.is_captioning:
            self.app.stop_captioning()
        else:
            self.app.start_captioning()

    def update_caption(self, text):
        if text is not None:
            self.caption_label.configure(text=text)
    
    def show_message(self, text, duration=None):
        self.caption_label.configure(text=text)
        if duration:
            revert_text = "Listening..." if self.app.is_captioning else "Captioning stopped."
            if text.startswith("Failed to initialize") or \
               text.startswith("Microphone selection cancelled") or \
               text.startswith("No microphones found") or \
               text.startswith("Invalid input") or \
               text.startswith("Failed to load STT model") or \
               text.startswith("Error: Hotkey listener failed"): 
                 revert_text = "Click Start to retry."
            self.master.after(duration, lambda: self.update_caption(revert_text))

    def get_heatmap_placeholder_frame(self):
        """Returns the frame designated for heatmap bars."""
        return self.heatmap_placeholder_frame


class GUIManager:
    def __init__(self, app_ref, config): 
        self.app_ref = app_ref
        self.config = config 
        self.root = ctk.CTk()
        
        window_geometry = config_manager.get_setting(self.config, 'GUI', 'window_geometry', fallback='800x130+100+100')
        always_on_top = config_manager.getboolean_setting(self.config, 'GUI', 'always_on_top', fallback=True)

        self.root.title("Live Captions")
        self.root.geometry(window_geometry)
        if always_on_top:
            self.root.attributes("-topmost", True)
        
        ctk.set_appearance_mode("System") 
        ctk.set_default_color_theme("blue")

        self.caption_display = CaptionWindow(master=self.root, app_ref=self.app_ref, config=self.config)
        self.caption_display.pack(expand=True, fill="both") # Pack the CaptionWindow frame itself

        self.summary_bubble = None 
        self.keyword_popup = None 
        self.command_visualizer_popup = None 
        
        # Heatmap UI elements
        self.mic_activity_bars = []
        self._create_mic_activity_display() # Create the heatmap bars

        self.root.lift() 

    def _create_mic_activity_display(self):
        """Creates the visual elements for the mic activity heatmap."""
        num_bars = config_manager.getint_setting(self.config, 'Features', 'heatmap_data_points', fallback=20)
        bar_width = config_manager.getint_setting(self.config, 'GUI', 'heatmap_bar_width', fallback=5)
        # Max height used for scaling, actual placeholder ensures space.
        # heatmap_max_height = config_manager.getint_setting(self.config, 'GUI', 'heatmap_bar_max_height', fallback=50)
        
        color_low = config_manager.get_setting(self.config, 'GUI', 'heatmap_color_low', fallback='blue')
        color_medium = config_manager.get_setting(self.config, 'GUI', 'heatmap_color_medium', fallback='green')
        color_high = config_manager.get_setting(self.config, 'GUI', 'heatmap_color_high', fallback='red')
        self.heatmap_colors = [color_low, color_medium, color_high]

        heatmap_container_parent = self.caption_display.get_heatmap_placeholder_frame()
        # Clear any previous content in placeholder (e.g., if re-creating)
        for widget in heatmap_container_parent.winfo_children():
            widget.destroy()

        for i in range(num_bars):
            # Initial height is 1, color is low. Will be updated by update_mic_activity_display.
            bar = ctk.CTkFrame(heatmap_container_parent, width=bar_width, height=1, fg_color=self.heatmap_colors[0], corner_radius=2)
            # Pack bars to fill the placeholder horizontally
            bar.pack(side=tkinter.LEFT, padx=1, expand=True, fill=tkinter.Y, anchor='s') # Anchor south for height change
            self.mic_activity_bars.append(bar)
        logging.info(f"Created {num_bars} microphone activity bars.")


    def update_mic_activity_display(self, rms_values):
        """Updates the height and color of mic activity bars based on RMS values."""
        num_bars_to_update = min(len(rms_values), len(self.mic_activity_bars))
        heatmap_max_height = config_manager.getint_setting(self.config, 'GUI', 'heatmap_bar_max_height', fallback=50)

        for i in range(num_bars_to_update):
            bar = self.mic_activity_bars[i]
            normalized_rms = rms_values[i] # These are already normalized 0-1 from App

            bar_height = int(normalized_rms * heatmap_max_height)
            bar_height = max(1, bar_height) # Ensure minimum height of 1px to be visible
            
            # Determine color based on RMS value
            if normalized_rms < 0.33:
                color = self.heatmap_colors[0]
            elif normalized_rms < 0.66:
                color = self.heatmap_colors[1]
            else:
                color = self.heatmap_colors[2]
            
            # Update bar configuration if changed
            # This check avoids unnecessary re-configuration if height and color are the same
            if bar.cget('height') != bar_height or bar.cget('fg_color') != color:
                bar.configure(height=bar_height, fg_color=color)

    def get_root(self):
        return self.root

    def get_caption_window(self): # Renamed from get_caption_display for consistency
        return self.caption_display

    def show_mic_selection_dialog(self, prompt_text, title):
        dialog = ctk.CTkInputDialog(text=prompt_text, title=title)
        return dialog.get_input()

    def show_summary_bubble(self, summary_text, duration_ms):
        logging.info(f"Displaying summary bubble with text: '{summary_text[:50]}...' for {duration_ms}ms")
        if self.summary_bubble and self.summary_bubble.winfo_exists():
            logging.debug("Previous summary bubble existed, destroying it.")
            self.summary_bubble.destroy()

        try:
            self.summary_bubble = ctk.CTkToplevel(self.root)
            self.summary_bubble.title("Summary") 

            main_win_x = self.root.winfo_x()
            main_win_y = self.root.winfo_y()
            main_win_width = self.root.winfo_width() 
            
            bubble_width = config_manager.getint_setting(self.config, 'GUI', 'summary_bubble_width', fallback=600)
            bubble_height = config_manager.getint_setting(self.config, 'GUI', 'summary_bubble_height', fallback=80)
            bubble_y_offset = config_manager.getint_setting(self.config, 'GUI', 'summary_bubble_y_offset', fallback=-90) 

            bubble_x = main_win_x + (main_win_width - bubble_width) // 2
            bubble_y = main_win_y + bubble_y_offset 
            
            if bubble_y < 0: bubble_y = 10

            self.summary_bubble.geometry(f"{bubble_width}x{bubble_height}+{bubble_x}+{bubble_y}")
            self.summary_bubble.attributes("-topmost", True)
            
            use_frameless_bubble = config_manager.getboolean_setting(self.config, 'GUI', 'summary_bubble_frameless', fallback=False)
            if use_frameless_bubble:
                 self.summary_bubble.overrideredirect(True)

            label = ctk.CTkLabel(self.summary_bubble, text=summary_text, wraplength=bubble_width-20, font=("Arial", 14))
            label.pack(expand=True, fill="both", padx=10, pady=10)

            def safe_destroy_bubble():
                if self.summary_bubble and self.summary_bubble.winfo_exists():
                    logging.debug("Auto-destroying summary bubble.")
                    self.summary_bubble.destroy()
                    self.summary_bubble = None 
            
            self.summary_bubble.after(duration_ms, safe_destroy_bubble)
            logging.debug("Summary bubble displayed and scheduled for destruction.")

        except Exception as e:
            logging.error(f"Error creating summary bubble: {e}", exc_info=True)
            if self.summary_bubble and self.summary_bubble.winfo_exists():
                self.summary_bubble.destroy() 
            self.summary_bubble = None

    def show_keyword_popup(self, message, duration_ms):
        logging.info(f"Displaying keyword popup with message: '{message}' for {duration_ms}ms")
        if self.keyword_popup and self.keyword_popup.winfo_exists():
            logging.debug("Previous keyword popup existed, destroying it.")
            self.keyword_popup.destroy()

        try:
            self.keyword_popup = ctk.CTkToplevel(self.root)

            main_win_x = self.root.winfo_x()
            main_win_y = self.root.winfo_y()
            main_win_width = self.root.winfo_width()

            popup_width = config_manager.getint_setting(self.config, 'GUI', 'keyword_popup_width', fallback=250)
            popup_height = config_manager.getint_setting(self.config, 'GUI', 'keyword_popup_height', fallback=50)
            
            default_x_offset = main_win_width - popup_width - 20 
            popup_x_offset = config_manager.getint_setting(self.config, 'GUI', 'keyword_popup_x_offset_from_main', fallback=default_x_offset)
            popup_y_offset = config_manager.getint_setting(self.config, 'GUI', 'keyword_popup_y_offset_from_main', fallback=20) 

            popup_x = main_win_x + popup_x_offset
            popup_y = main_win_y + popup_y_offset
            
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            if popup_x + popup_width > screen_width: popup_x = screen_width - popup_width - 5
            if popup_y + popup_height > screen_height: popup_y = screen_height - popup_height - 5
            if popup_x < 0: popup_x = 5
            if popup_y < 0: popup_y = 5

            self.keyword_popup.geometry(f"{popup_width}x{popup_height}+{popup_x}+{popup_y}")
            self.keyword_popup.attributes("-topmost", True)
            
            popup_frameless = config_manager.getboolean_setting(self.config, 'GUI', 'keyword_popup_frameless', fallback=True)
            if popup_frameless:
                 self.keyword_popup.overrideredirect(True)

            label = ctk.CTkLabel(self.keyword_popup, text=message, wraplength=popup_width-20, font=("Arial", 12))
            label.pack(expand=True, fill="both", padx=10, pady=10)

            def safe_destroy_keyword_popup():
                if self.keyword_popup and self.keyword_popup.winfo_exists():
                    logging.debug("Auto-destroying keyword popup.")
                    self.keyword_popup.destroy()
                    self.keyword_popup = None 
            
            self.keyword_popup.after(duration_ms, safe_destroy_keyword_popup)
            logging.debug("Keyword popup displayed and scheduled for destruction.")

        except Exception as e:
            logging.error(f"Error creating keyword popup: {e}", exc_info=True)
            if self.keyword_popup and self.keyword_popup.winfo_exists():
                self.keyword_popup.destroy()
            self.keyword_popup = None

    def show_command_visualizer(self, message, duration_ms):
        logging.info(f"Displaying command visualizer with message: '{message}' for {duration_ms}ms")
        if self.command_visualizer_popup and self.command_visualizer_popup.winfo_exists():
            logging.debug("Previous command visualizer popup existed, destroying it.")
            self.command_visualizer_popup.destroy()

        try:
            self.command_visualizer_popup = ctk.CTkToplevel(self.root)

            popup_width = config_manager.getint_setting(self.config, 'GUI', 'command_popup_width', fallback=400)
            popup_height = config_manager.getint_setting(self.config, 'GUI', 'command_popup_height', fallback=100)

            main_win_x = self.root.winfo_x()
            main_win_y = self.root.winfo_y()
            main_win_width = self.root.winfo_width()
            main_win_height = self.root.winfo_height() 

            popup_x = main_win_x + (main_win_width // 2) - (popup_width // 2)
            popup_y = main_win_y - popup_height - 20 

            if popup_y < 0: 
                popup_y = main_win_y + (main_win_height // 2) - (popup_height // 2)
                if popup_y < 0: popup_y = 10 

            self.command_visualizer_popup.geometry(f"{popup_width}x{popup_height}+{popup_x}+{popup_y}")
            self.command_visualizer_popup.attributes("-topmost", True)
            
            popup_frameless = config_manager.getboolean_setting(self.config, 'GUI', 'command_popup_frameless', fallback=True)
            if popup_frameless:
                 self.command_visualizer_popup.overrideredirect(True)

            label = ctk.CTkLabel(self.command_visualizer_popup, text=message, font=("Arial", 24, "bold"), wraplength=popup_width-20)
            label.pack(expand=True, fill="both", padx=10, pady=10)

            def safe_destroy_command_popup():
                if self.command_visualizer_popup and self.command_visualizer_popup.winfo_exists():
                    logging.debug("Auto-destroying command visualizer popup.")
                    self.command_visualizer_popup.destroy()
                    self.command_visualizer_popup = None
            
            self.command_visualizer_popup.after(duration_ms, safe_destroy_command_popup)
            logging.debug("Command visualizer popup displayed and scheduled for destruction.")

        except Exception as e:
            logging.error(f"Error creating command visualizer popup: {e}", exc_info=True)
            if self.command_visualizer_popup and self.command_visualizer_popup.winfo_exists():
                self.command_visualizer_popup.destroy()
            self.command_visualizer_popup = None


    def run_mainloop(self):
        """Starts the CustomTkinter main event loop."""
        self.root.mainloop()
