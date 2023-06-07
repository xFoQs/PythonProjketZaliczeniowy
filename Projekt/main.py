import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import csv
import numpy as np
import statistics
from collections import Counter


class App:
    def __init__(self, master):
        self.master = master
        self.master.title("CSV Viewer")

        self.load_button = ttk.Menubutton(self.master, text="Load CSV", direction='below')
        self.load_button.menu = tk.Menu(self.load_button, tearoff=0)
        self.load_button["menu"] = self.load_button.menu
        self.load_button.menu.add_command(label="Open", command=self.load_csv)
        self.load_button.pack()

        self.tree_frame = tk.Frame(self.master)
        self.tree_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.tree_scrollbar_x = tk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL)
        self.tree_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree_scrollbar_y = tk.Scrollbar(self.tree_frame)
        self.tree_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.treeview = tk.ttk.Treeview(self.tree_frame, columns=[], show='headings', xscrollcommand=self.tree_scrollbar_x.set, yscrollcommand=self.tree_scrollbar_y.set)
        self.treeview.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.tree_scrollbar_x.config(command=self.treeview.xview)
        self.tree_scrollbar_y.config(command=self.treeview.yview)

        # Add new tab for min/max values
        self.tabControl = ttk.Notebook(self.master)
        self.tabControl.pack(expand=1, fill="both")

        self.min_max_tab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.min_max_tab, text="Min/Max")

        # Add Treeview widget for min/max values
        self.min_max_treeview = ttk.Treeview(self.min_max_tab, columns=["Column", "Min", "Max", "Mean", "St_dev", "Median", "Mode"], show="headings")
        self.min_max_treeview.heading("Column", text="Column")
        self.min_max_treeview.heading("Min", text="Min")
        self.min_max_treeview.heading("Max", text="Max")
        self.min_max_treeview.heading("Mean", text="Mean")
        self.min_max_treeview.heading("St_dev", text="St_dev")
        self.min_max_treeview.heading("Median", text="Median")
        self.min_max_treeview.heading("Mode", text="Mode")
        self.min_max_treeview.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.min_max_button = ttk.Button(self.min_max_tab, text="Calculate Min/Max", command=self.calculate_min_max)
        self.min_max_button.pack(side=tk.BOTTOM)

        # Add new tab for correlation matrix
        self.correlation_tab = ttk.Frame(self.tabControl)
        self.tabControl.add(self.correlation_tab, text="Correlation")

        # Add Treeview widget for correlation matrix
        self.correlation_treeview = ttk.Treeview(self.correlation_tab, columns=[], show="headings")
        self.correlation_treeview.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.correlation_button = ttk.Button(self.correlation_tab, text="Calculate Correlation",
                                             command=self.calculate_correlation)
        self.correlation_button.pack(side=tk.BOTTOM)

    def load_csv(self):
        file_path = filedialog.askopenfilename(title="Open CSV File", filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*")))
        if file_path:
            with open(file_path, "r") as f:
                reader = csv.reader(f)
                data = []
                for row in reader:
                    data.append(row)
            self.display_table(data)

    def display_table(self, data):
        columns = data[0]
        self.treeview["columns"] = columns
        for col in columns:
            self.treeview.column(col, width=100, anchor=tk.CENTER)
            self.treeview.heading(col, text=col, anchor=tk.CENTER)
        for row in data[1:]:
            self.treeview.insert("", tk.END, values=row)

    def calculate_min_max(self):
        # Check if the window is already open
        if getattr(self, "min_max_window", None) is not None and self.min_max_window.winfo_exists():
            # Window is already open, do nothing
            return

        # Create a new window
        self.min_max_window = tk.Toplevel(self.master)
        min_max_window = self.min_max_window
        min_max_window.title("Select Columns")

        # Configure the window size and position
        window_width = 400
        window_height = 300
        screen_width = min_max_window.winfo_screenwidth()
        screen_height = min_max_window.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        min_max_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Create a label
        label = ttk.Label(min_max_window, text="Select columns for statistical calculations",
                          font=("Arial", 14, "bold"))
        label.pack(pady=20)

        # Create a listbox to display available columns
        listbox = tk.Listbox(min_max_window, selectmode=tk.MULTIPLE, font=("Arial", 12), height=8)
        listbox.pack()

        # Add columns to the listbox
        columns = self.treeview["columns"]
        for column in columns:
            listbox.insert(tk.END, column)

        # Select all columns by default
        listbox.selection_set(0, tk.END)

        def calculate():
            # Get selected columns
            selected_columns = [listbox.get(index) for index in listbox.curselection()]

            if len(selected_columns) == 0:
                # Show error message if no columns are selected
                messagebox.showerror("Error", "Please select at least one column.")
                return

            # Clear existing data from Treeview
            self.min_max_treeview.delete(*self.min_max_treeview.get_children())

            # Get data from Treeview
            data = []
            for idx, column in enumerate(self.treeview["columns"]):
                if column in selected_columns:
                    column_data = []
                    for item in self.treeview.get_children():
                        value = self.treeview.set(item, column)
                        try:
                            column_data.append(float(value))
                        except ValueError:
                            column_data.append(value)  # Handle text values
                    data.append(column_data)

            # Calculate statistics for each selected column
            statistics_values = []
            for col_idx in range(len(data)):
                column_data = data[col_idx]
                column_name = selected_columns[col_idx]
                if all(isinstance(val, float) for val in column_data):
                    # Numeric column
                    min_value = min(column_data)
                    max_value = max(column_data)
                    mean_value = round(statistics.mean(column_data), 2)
                    stdev_value = round(statistics.stdev(column_data), 2)
                    median_value = statistics.median(column_data)
                    mode_value = statistics.mode(column_data)
                else:
                    # Text column
                    counter = Counter(column_data)
                    mode_value = counter.most_common(1)[0][0] if counter else ""
                    min_value = ""
                    max_value = ""
                    mean_value = ""
                    stdev_value = ""
                    median_value = ""

                statistics_values.append(
                    (column_name, min_value, max_value, mean_value, stdev_value, median_value, mode_value))

            # Insert statistics values into Treeview
            for i, (column_name, min_value, max_value, mean_value, stdev_value, median_value, mode_value) in enumerate(
                    statistics_values):
                self.min_max_treeview.insert("", tk.END,
                                             values=[column_name, min_value, max_value, mean_value, stdev_value,
                                                     median_value, mode_value])

            for col in self.min_max_treeview["columns"]:
                self.min_max_treeview.column(col, anchor="center")

            # Close the window
            min_max_window.destroy()

        # Create a button to calculate statistics
        calculate_button = ttk.Button(min_max_window, text="Calculate", command=calculate)
        calculate_button.pack()

    def calculate_correlation(self):
            # Check if the window is already open
            if getattr(self, "correlation_window", None) is not None and self.correlation_window.winfo_exists():
                # Window is already open, do nothing
                return

            # Clear existing data from Treeview
            self.correlation_treeview.delete(*self.correlation_treeview.get_children())

            def calculate():
                # Get selected columns
                selected_columns = listbox.curselection()
                selected_columns = [columns[index] for index in selected_columns]

                if len(selected_columns) < 2:
                    # Show error message if less than 2 columns are selected
                    messagebox.showerror("Error", "Please select at least two columns.")
                    return

                # Get data from Treeview
                data = []
                for idx, column in enumerate(self.treeview["columns"]):
                    if column in selected_columns:
                        column_data = []
                        for item in self.treeview.get_children():
                            value = self.treeview.set(item, column)
                            try:
                                column_data.append(float(value))
                            except ValueError:
                                break
                        else:
                            data.append(column_data)

                # Calculate correlation matrix
                data = np.array(data, dtype=np.float64)
                correlation_matrix = np.corrcoef(data)

                # Insert correlation matrix into Treeview
                self.correlation_treeview["columns"] = [""] + selected_columns
                self.correlation_treeview.column("", width=100, anchor=tk.CENTER)
                self.correlation_treeview.heading("", text="", anchor=tk.CENTER)
                for col in selected_columns:
                    self.correlation_treeview.column(col, width=100, anchor=tk.CENTER)
                    self.correlation_treeview.heading(col, text=col, anchor=tk.CENTER)
                for i, row in enumerate(correlation_matrix):
                    values = [round(x, 2) for x in row]
                    self.correlation_treeview.insert("", tk.END, values=[selected_columns[i]] + values)

                # Close the menu
                correlation_window.destroy()

            # Create a new window
            self.correlation_window = tk.Toplevel(self.master)
            correlation_window = self.correlation_window
            correlation_window.title("Select Columns")

            # Create a label
            label = ttk.Label(correlation_window, text="Select columns for correlation calculation",
                              font=("Arial", 14, "bold"))
            label.pack(pady=20)

            # Create a listbox to display available columns
            listbox = tk.Listbox(correlation_window, selectmode=tk.MULTIPLE)
            listbox.pack()

            # Add columns to the listbox
            columns = self.treeview["columns"]
            for column in columns:
                column_data = [self.treeview.set(item, column) for item in self.treeview.get_children()]
                try:
                    column_data = [float(value) for value in column_data]
                    listbox.insert(tk.END, column)
                except ValueError:
                    continue

            # Select all columns by default
            listbox.selection_set(0, tk.END)

            # Create a button to calculate correlation
            calculate_button = ttk.Button(correlation_window, text="Calculate", command=calculate)
            calculate_button.pack(pady=20)

            # Apply styling
            correlation_window.configure(background="#f2f2f2")
            label.configure(foreground="#333333")
            listbox.configure(background="#f2f2f2", foreground="#333333", font=("Arial", 12))
            calculate_button.configure(style="Accent.TButton")

            # Add a custom style for the button
            style = ttk.Style()
            style.configure("Accent.TButton", background="#0078D7", foreground="white", font=("Arial", 12, "bold"))

            # Rest of the code...


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()