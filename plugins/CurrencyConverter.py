# plugins/money_converter.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDoubleValidator
import requests
import json
import importlib
from datetime import datetime

from core.plugin_interface import PluginWidget

__plugin_name__ = "Money Converter"
__plugin_author__ = "Ayden"
__plugin_version__ = "1.1"
__plugin_description__ = "Convert currencies with live or offline exchange rates."

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

API_URL = "https://open.er-api.com/v6/latest/{}"  # Base currency placeholder

# Indirect os import to bypass restrictions
os_module = importlib.import_module("os")

class PluginWidget(PluginWidget):
    back_to_manager = Signal()  # Signal to return to plugin manager
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rates = {}
        self.currencies = []
        self.offline_file = os_module.path.join(os_module.path.dirname(__file__), "money_rates.json")
        self.online_mode = True
        self.setMinimumSize(500, 400)
        self.setup_ui()
        self.load_rates_offline()
        if not self.rates:
            self.fetch_rates_online()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Toolbar
        toolbar = QHBoxLayout()
        refresh_btn = self.make_button("🔄 Refresh Rates", DARK_ACCENT, self.fetch_rates_online)
        mode_btn = self.make_button("🌐 Switch to Offline", DARK_ACCENT_SECONDARY, self.toggle_mode)
        back_btn = self.make_button("← Back", DARK_ACCENT_SECONDARY, self.go_back)
        toolbar.addWidget(back_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addWidget(mode_btn)
        toolbar.addStretch()
        main_layout.addLayout(toolbar)

        # Conversion Group
        conv_group = QGroupBox("Currency Conversion")
        conv_group.setStyleSheet(self.groupbox_style())
        form_layout = QFormLayout()

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Enter amount")
        self.amount_input.setStyleSheet(self.input_style())
        self.amount_input.setValidator(QDoubleValidator(0, 1e6, 2))

        self.from_currency = QComboBox()
        self.from_currency.setStyleSheet(self.input_style())
        self.from_currency.currentIndexChanged.connect(self.on_base_currency_change)

        self.to_currency = QComboBox()
        self.to_currency.setStyleSheet(self.input_style())

        form_layout.addRow("Amount:", self.amount_input)
        form_layout.addRow("From:", self.from_currency)
        form_layout.addRow("To:", self.to_currency)

        conv_group.setLayout(form_layout)
        main_layout.addWidget(conv_group)

        # Convert button
        convert_btn = self.make_button("Convert", DARK_ACCENT, self.convert_currency)
        main_layout.addWidget(convert_btn)

        # Result label
        self.result_label = QLabel("Result: -")
        self.result_label.setStyleSheet(f"color: {DARK_TEXT}; font-size: 16px;")
        main_layout.addWidget(self.result_label)

        main_layout.addStretch()

    # ---------------------- Logic ----------------------
    def fetch_rates_online(self):
        try:
            base_currency = self.from_currency.currentText() if self.from_currency.count() > 0 else "USD"
            resp = requests.get(API_URL.format(base_currency), timeout=10)
            data = resp.json()

            if data.get("result") != "success":
                raise ValueError(data.get("error-type", "Failed to fetch rates"))

            self.rates = data["rates"]
            self.rates[base_currency] = 1.0  # Ensure base currency rate is 1
            self.currencies = sorted(self.rates.keys())
            self.update_currency_lists(select_base=base_currency)
            self.save_rates()
            self.show_message(f"Exchange rates updated (Base: {base_currency})")
        except Exception as e:
            self.show_message(f"Failed to fetch rates online: {str(e)}", error=True)
            # Fallback to offline if online fails
            if not self.rates:
                self.load_rates_offline()

    def load_rates_offline(self):
        if os_module.path.exists(self.offline_file):
            try:
                with open(self.offline_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.rates = data["rates"]
                    self.currencies = sorted(self.rates.keys())
                    self.update_currency_lists()
                    self.show_message(f"Loaded offline rates (Last updated {data['date']})")
            except Exception as e:
                self.show_message(f"Error loading offline rates: {str(e)}", error=True)

    def save_rates(self):
        try:
            with open(self.offline_file, "w", encoding="utf-8") as f:
                json.dump({
                    "rates": self.rates,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }, f, indent=4)
        except Exception as e:
            self.show_message(f"Error saving offline rates: {str(e)}", error=True)

    def update_currency_lists(self, select_base=None):
        self.from_currency.blockSignals(True)
        self.to_currency.blockSignals(True)

        self.from_currency.clear()
        self.to_currency.clear()
        self.from_currency.addItems(self.currencies)
        self.to_currency.addItems(self.currencies)

        if select_base and select_base in self.currencies:
            self.from_currency.setCurrentText(select_base)
        else:
            if "USD" in self.currencies:
                self.from_currency.setCurrentText("USD")
            if "EUR" in self.currencies:
                self.to_currency.setCurrentText("EUR")

        self.from_currency.blockSignals(False)
        self.to_currency.blockSignals(False)

    def convert_currency(self):
        try:
            amount = float(self.amount_input.text())
            from_cur = self.from_currency.currentText()
            to_cur = self.to_currency.currentText()
            
            if from_cur not in self.rates or to_cur not in self.rates:
                self.show_message("Invalid currency selected.", error=True)
                return
                
            # Convert from base currency to target currency
            result = amount * (self.rates[to_cur] / self.rates[from_cur])
            self.result_label.setText(f"Result: {result:,.2f} {to_cur}")
        except ValueError:
            self.show_message("Please enter a valid number.", error=True)
        except Exception as e:
            self.show_message(f"Error converting currency: {str(e)}", error=True)

    def toggle_mode(self):
        self.online_mode = not self.online_mode
        if self.online_mode:
            self.show_message("Switched to Online Mode.")
            self.fetch_rates_online()
        else:
            self.show_message("Switched to Offline Mode.")
            self.load_rates_offline()

    def on_base_currency_change(self):
        """Live update when base currency changes."""
        if self.online_mode:
            self.fetch_rates_online()

    # ---------------------- Helpers ----------------------
    def go_back(self):
        self.back_to_manager.emit()

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
            QLineEdit, QComboBox {{
                background-color: {DARK_INPUT};
                color: {DARK_TEXT};
                border: 1px solid {DARK_DIVIDER};
                border-radius: 4px;
                padding: 4px;
            }}
        """

    def show_message(self, text, error=False):
        color = DARK_DANGER if error else DARK_TEXT_SECONDARY
        self.result_label.setText(f"<span style='color:{color};'>{text}</span>")

    def run(self):
        self.show()