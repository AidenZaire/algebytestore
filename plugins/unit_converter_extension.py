"""
Unit Converter Extension for Algebyte Math Suite
------------------------------------------------
This plugin is NOT runnable on its own — it only extends the Unit Converter tool
inside the Core Tools plugin.

When placed in the same directory as `core_tools.py` (in /plugins/), the Unit Converter
will automatically detect and merge these extra units into its default set.

Tested with the Dropbox + GitHub Action auto-update workflow.
"""

__plugin_name__ = "Unit Converter Extension"
__plugin_author__ = "Ayden"
__plugin_version__ = "1.0"
__plugin_description__ = "Adds more categories and units to the Unit Converter."

# Extra unit categories for testing
EXTRA_UNITS = {
    "Currency": {  # Fixed sample rates (manual update required)
        "USD": 1,
        "EUR": 0.91,
        "GBP": 0.78,
        "JPY": 142.12,
        "AUD": 1.48
    },
    "Data Storage": {
        "bit": 1,
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4
    },
    "Speed": {
        "m/s": 1,
        "km/h": 3.6,
        "mph": 2.23694,
        "knot": 1.94384
    },
    "Area": {
        "m²": 1,
        "km²": 1_000_000,
        "cm²": 0.0001,
        "mm²": 0.000001,
        "ft²": 0.092903,
        "in²": 0.00064516
    }
}
