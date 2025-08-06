# plugins/function_analyzer.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QGroupBox, QTextEdit, QDoubleSpinBox, QFormLayout, QSizePolicy,
    QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
import sympy as sp
import numpy as np
import matplotlib.pyplot as plt

from core.plugin_interface import PluginWidget

__plugin_name__ = "Function Analyzer"
__plugin_author__ = "Ayden"
__plugin_version__ = "2.0"
__plugin_description__ = "Analyze mathematical functions: differentiate, integrate, evaluate, and plot interactively."


# Dark theme constants
DARK_BG = "#121212"
DARK_CARD = "#1E1E1E"
DARK_TEXT = "#FFFFFF"
DARK_TEXT_SECONDARY = "#B0B0B0"
DARK_ACCENT = "#BB86FC"
DARK_ACCENT_SECONDARY = "#03DAC6"
DARK_DIVIDER = "#333333"
DARK_HOVER = "#2A2A2A"
DARK_INPUT = "#2D2D2D"
DARK_DANGER = "#CF6679"


class PluginWidget(PluginWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 500)

        self.stack = QStackedWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)

        self.init_page1()
        self.init_page2()

        self.stack.setCurrentIndex(0)

    def init_page1(self):
        """Page 1: Function settings and results."""
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Toolbar
        toolbar = QHBoxLayout()
        back_btn = self.make_button(" 🔙 Back", DARK_ACCENT_SECONDARY, self.back_to_manager.emit)
        graph_btn = self.make_button("📈 View Graph", DARK_ACCENT, self.show_graph_page)
        clear_btn = self.make_button("🧹 Clear", DARK_DANGER, self.clear_results)

        toolbar.addWidget(back_btn)
        toolbar.addWidget(graph_btn)
        toolbar.addWidget(clear_btn)
        toolbar.addStretch()
        main_layout.addLayout(toolbar)

        # Input Section
        input_group = QGroupBox("Function Input")
        input_group.setStyleSheet(self.groupbox_style())
        input_layout = QFormLayout()

        self.function_input = QLineEdit("x**2")
        self.variable_input = QLineEdit("x")
        self.eval_point_input = QDoubleSpinBox()
        self.eval_point_input.setRange(-1000, 1000)
        self.eval_point_input.setValue(2.0)

        self.function_input.setStyleSheet(self.input_style())
        self.variable_input.setStyleSheet(self.input_style())
        self.eval_point_input.setStyleSheet(self.input_style())

        input_layout.addRow("Function f(x):", self.function_input)
        input_layout.addRow("Variable:", self.variable_input)
        input_layout.addRow("Evaluation Point:", self.eval_point_input)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # Operation Buttons
        btn_layout = QHBoxLayout()
        self.diff_btn = self.make_button("Differentiate", DARK_ACCENT, self.differentiate)
        self.int_btn = self.make_button("Integrate", DARK_ACCENT, self.integrate)
        self.eval_btn = self.make_button("Evaluate", DARK_ACCENT_SECONDARY, self.evaluate)
        btn_layout.addWidget(self.diff_btn)
        btn_layout.addWidget(self.int_btn)
        btn_layout.addWidget(self.eval_btn)
        main_layout.addLayout(btn_layout)

        # Results Display
        results_group = QGroupBox("Results")
        results_group.setStyleSheet(self.groupbox_style())
        results_layout = QVBoxLayout()

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet(self.results_style())
        results_layout.addWidget(self.results_text)

        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group, 1)

        self.stack.addWidget(page)

    def init_page2(self):
        """Page 2: Interactive graph view."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Toolbar
        toolbar = QHBoxLayout()
        back_btn = self.make_button("🔙 Back", DARK_ACCENT_SECONDARY, self.show_main_page)
        toolbar.addWidget(back_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Matplotlib figure
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, 1)

        self.stack.addWidget(page)

    # ---------- Core Functionalities ----------
    def parse_function(self):
        """Parse user input into a SymPy expression"""
        var_str = self.variable_input.text().strip()
        func_str = self.function_input.text().strip()

        try:
            x = sp.symbols(var_str)
            expr = sp.sympify(func_str)
            return expr, x
        except Exception as e:
            self.show_error(f"Error parsing function: {str(e)}")
            return None, None

    def differentiate(self):
        expr, x = self.parse_function()
        if expr is None: return
        try:
            derivative = sp.diff(expr, x)
            self.show_result("Derivative", derivative)
        except Exception as e:
            self.show_error(f"Differentiation error: {str(e)}")

    def integrate(self):
        expr, x = self.parse_function()
        if expr is None: return
        try:
            integral = sp.integrate(expr, x)
            self.show_result("Indefinite Integral", integral)
        except Exception as e:
            self.show_error(f"Integration error: {str(e)}")

    def evaluate(self):
        expr, x = self.parse_function()
        if expr is None: return
        try:
            point = self.eval_point_input.value()
            result = expr.subs(x, point).evalf()
            self.show_result(f"Evaluation at {x}={point}", result)
        except Exception as e:
            self.show_error(f"Evaluation error: {str(e)}")

    def plot_graph(self):
        """Plot on the graph page."""
        expr, x = self.parse_function()
        if expr is None: return
        try:
            self.ax.clear()
            f = sp.lambdify(x, expr, "numpy")
            x_vals = np.linspace(-10, 10, 400)
            y_vals = f(x_vals)
            self.ax.plot(x_vals, y_vals, label=f"${sp.latex(expr)}$")
            self.ax.axhline(0, color='white', linewidth=0.5)
            self.ax.axvline(0, color='white', linewidth=0.5)
            self.ax.grid(True, linestyle='--', alpha=0.4, color="white")
            self.ax.legend()
            self.ax.set_title(f"Plot of ${sp.latex(expr)}$", color=DARK_TEXT)
            self.canvas.draw()
        except Exception as e:
            self.show_error(f"Plotting error: {str(e)}")

    # ---------- Navigation ----------
    def go_back(self):
        """Emit back signal for plugin manager."""
        if hasattr(self, 'back_requested'):
            self.back_to_manager.emit()

    def show_graph_page(self):
        self.plot_graph()
        self.stack.setCurrentIndex(1)

    def show_main_page(self):
        self.stack.setCurrentIndex(0)

    # ---------- Helpers ----------
    def show_error(self, message):
        self.results_text.append(f"<font color='{DARK_DANGER}'>{message}</font>")

    def show_result(self, title, result):
        self.results_text.append(f"<b>{title}:</b>")
        self.results_text.append(f"{sp.pretty(result)}")
        self.results_text.append("<hr>")

    def clear_results(self):
        self.results_text.clear()

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
                margin-top: 6px;
            }}
            QGroupBox:title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 3px;
            }}
        """

    def input_style(self):
        return f"""
            QLineEdit, QDoubleSpinBox {{
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
        """
        Called by the main app when this plugin is launched.
        Connects the back button signal to the main app if available.
        """
        self.clear_results()
        self.show_main_page()
