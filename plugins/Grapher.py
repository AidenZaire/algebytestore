# plugins/grapher.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGroupBox, QFormLayout, QTextEdit,
    QStackedWidget
)
from PySide6.QtCore import Signal
import numpy as np
import sympy as sp
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import importlib.util, glob

from PySide6.QtWidgets import QApplication

from core.plugin_interface import PluginWidget

__plugin_name__ = "Grapher"
__plugin_author__ = "Ayden"
__plugin_version__ = "1.0"
__plugin_description__ = "Draw graphs manually, plot functions, and integrate with Function Analyzer for advanced calculations."

# Theme colors
DARK_BG = "#121212"
DARK_CARD = "#1E1E1E"
DARK_TEXT = "#FFFFFF"
DARK_ACCENT = "#BB86FC"
DARK_ACCENT_SECONDARY = "#03DAC6"
DARK_DIVIDER = "#333333"
DARK_HOVER = "#2A2A2A"
DARK_INPUT = "#2D2D2D"
DARK_DANGER = "#CF6679"

class PluginWidget(PluginWidget):
    back_to_manager = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 500)

        self.stack = QStackedWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)

        # Persistent toolbar layout so extensions can add to it
        self.toolbar_layout = QHBoxLayout()

        self.function_analyzer_available = self.detect_function_analyzer()
        self.extensions = self.detect_extensions()

        self.init_main_page()
        self.init_graph_page()

        self.stack.setCurrentIndex(0)

        # Load extensions after UI is ready
        for ext in self.extensions:
            self.run_extension(ext)

    def detect_function_analyzer(self):
        try:
            spec = importlib.util.find_spec("plugins.function_analyzer")
            return spec is not None
        except ImportError:
            return False

    def detect_extensions(self):
        """Load grapher extensions from default appdata folder, auto-create it, and migrate stray extensions."""
        import glob
        from pathlib import Path

        # 1. Define Grapher extensions folder inside default appdata plugins folder
        appdata_plugins = Path.home() / "Algebyte" / "plugins"
        grapher_folder = appdata_plugins / "grapher_extensions"
        grapher_folder.mkdir(parents=True, exist_ok=True)  # Auto-create if missing

        # 2. Check bundled general plugins folder for stray Grapher extensions
        bundled_plugins = Path(__file__).parent.parent / "plugins"
        stray_files = glob.glob(str(bundled_plugins / "grapher_ext_*.py"))

        for stray in stray_files:
            dest = grapher_folder / Path(stray).name
            try:
                Path(stray).rename(dest)  # Move file without shutil
                print(f"[Grapher] Moved extension {Path(stray).name} to {grapher_folder}")
            except Exception as e:
                print(f"[Grapher] Could not move {Path(stray).name}: {e}")

        # 3. Load extensions from the dedicated grapher folder
        ext_files = glob.glob(str(grapher_folder / "grapher_ext_*.py"))

        # Deduplicate (just in case) and return
        seen = set()
        final_list = []
        for f in ext_files:
            if f not in seen:
                seen.add(f)
                final_list.append(f)

        return final_list

    def init_main_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        # Toolbar
        back_btn = self.make_button("← Back", DARK_ACCENT_SECONDARY, self.back_to_manager.emit)
        graph_btn = self.make_button("📈 Graph View", DARK_ACCENT, self.show_graph_page)
        self.toolbar_layout.addWidget(back_btn)
        self.toolbar_layout.addWidget(graph_btn)

        if self.function_analyzer_available:
            self.toolbar_layout.addWidget(self.make_button("Differentiate", DARK_ACCENT, self.differentiate))
            self.toolbar_layout.addWidget(self.make_button("Integrate", DARK_ACCENT, self.integrate))

        self.toolbar_layout.addStretch()
        layout.addLayout(self.toolbar_layout)

        # Function Input
        input_group = QGroupBox("Function Input")
        input_group.setStyleSheet(self.groupbox_style())
        input_layout = QFormLayout()

        self.function_input = QLineEdit("x**2")
        self.variable_input = QLineEdit("x")
        self.function_input.setStyleSheet(self.input_style())
        self.variable_input.setStyleSheet(self.input_style())

        input_layout.addRow("Function f(x):", self.function_input)
        input_layout.addRow("Variable:", self.variable_input)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Results
        results_group = QGroupBox("Results")
        results_group.setStyleSheet(self.groupbox_style())
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet(self.results_style())
        results_layout = QVBoxLayout()
        results_layout.addWidget(self.results_text)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        self.stack.addWidget(page)

    def init_graph_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        back_btn = self.make_button("← Back", DARK_ACCENT_SECONDARY, self.show_main_page)
        layout.addWidget(back_btn)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(toolbar)
        layout.addWidget(self.canvas, 1)

        self.stack.addWidget(page)

    def plot_function(self):
        expr, x = self.parse_function()
        if expr is None:
            return
        try:
            self.ax.clear()
            f = sp.lambdify(x, expr, "numpy")
            x_vals = np.linspace(-10, 10, 400)
            y_vals = f(x_vals)
            self.ax.plot(x_vals, y_vals, label=f"${sp.latex(expr)}$")
            self.ax.axhline(0, color="white", linewidth=0.5)
            self.ax.axvline(0, color="white", linewidth=0.5)
            self.ax.grid(True, linestyle="--", alpha=0.5, color="white")
            self.ax.legend()
            self.canvas.draw()
            self.show_result("Plotted Function", expr)
        except Exception as e:
            self.show_error(f"Plotting error: {e}")

    def differentiate(self):
        expr, x = self.parse_function()
        try:
            derivative = sp.diff(expr, x)
            self.show_result("Derivative", derivative)
        except Exception as e:
            self.show_error(f"Diff error: {e}")

    def integrate(self):
        expr, x = self.parse_function()
        try:
            integral = sp.integrate(expr, x)
            self.show_result("Integral", integral)
        except Exception as e:
            self.show_error(f"Integration error: {e}")

    def run_extension(self, ext_file):
        try:
            spec = importlib.util.spec_from_file_location("grapher_ext", ext_file)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "run_extension"):
                mod.run_extension(self, self.toolbar_layout)
            else:
                self.show_error(f"Extension {ext_file} has no run_extension()")
        except Exception as e:
            self.show_error(f"Extension error: {e}")

    def parse_function(self):
        try:
            var = self.variable_input.text().strip()
            expr = sp.sympify(self.function_input.text().strip())
            return expr, sp.symbols(var)
        except Exception as e:
            self.show_error(f"Parse error: {e}")
            return None, None

    def show_graph_page(self):
        self.stack.setCurrentIndex(1)

    def show_main_page(self):
        self.stack.setCurrentIndex(0)

    def show_result(self, title, result):
        self.results_text.append(f"<b>{title}:</b> {sp.pretty(result)}")

    def show_error(self, message):
        self.results_text.append(f"<font color='{DARK_DANGER}'>{message}</font>")

    def make_button(self, text, color, slot):
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: {DARK_TEXT};
                border-radius: 6px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {DARK_HOVER};
            }}
        """)
        btn.clicked.connect(slot)
        return btn

    def groupbox_style(self):
        return f"""
            QGroupBox {{
                background-color: {DARK_CARD};
                color: {DARK_TEXT};
                border: 1px solid {DARK_DIVIDER};
                border-radius: 6px;
            }}
        """

    def input_style(self):
        return f"""
            QLineEdit {{
                background-color: {DARK_INPUT};
                color: {DARK_TEXT};
                border: 1px solid {DARK_DIVIDER};
                border-radius: 4px;
                padding: 4px;
            }}
        """

    def results_style(self):
        return f"""
            QTextEdit {{
                background-color: {DARK_INPUT};
                color: {DARK_TEXT};
                border: 1px solid {DARK_DIVIDER};
                border-radius: 4px;
            }}
        """

    def run(self):
        self.show_main_page()