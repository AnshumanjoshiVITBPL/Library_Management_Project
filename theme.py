"""Colour palette and appearance handling for the whole app"""

import customtkinter as ctk

DARK = {
    "bg": "#0e1621",
    "surface": "#16212e",
    "surface2": "#1d2a3a",
    "border": "#26374a",
    "text": "#e8eef7",
    "muted": "#8fa3bc",
    "accent": "#2e8bf0",
    "accent2": "#16b8a6",
    "gold": "#f2a93b",
    "ok": "#33c17a",
    "warn": "#f5a524",
    "bad": "#f1595f",
    "sidebar": "#0b121c",
    "sidebar_text": "#93a5bd",
    "head": "#13202e",
    "row_alt": "#18242f",
}

LIGHT = {
    "bg": "#f1f4f9",
    "surface": "#ffffff",
    "surface2": "#f5f8fc",
    "border": "#dce3ee",
    "text": "#16233a",
    "muted": "#64748b",
    "accent": "#1b6fd8",
    "accent2": "#0e9c8d",
    "gold": "#d98b14",
    "ok": "#1f9d5e",
    "warn": "#c98209",
    "bad": "#d33a40",
    # sidebar stays navy in both modes, it just looks better against the brand
    "sidebar": "#101c2c",
    "sidebar_text": "#a8b8ce",
    "head": "#ffffff",
    "row_alt": "#f7f9fc",
}

PALETTES = {"dark": DARK, "light": LIGHT}

_mode = "dark"


def set_mode(name):
    global _mode
    _mode = name if name in PALETTES else "dark"
    ctk.set_appearance_mode(_mode)


def toggle_mode():
    set_mode("light" if _mode == "dark" else "dark")
    return _mode


def mode():
    return _mode


def c(key):
    """Fetch a colour from the palette currently in use."""
    return PALETTES[_mode].get(key, PALETTES["dark"].get(key, "#000000"))


def font(size=13, weight="normal", family="Segoe UI"):
    return ctk.CTkFont(family=family, size=size, weight=weight)


# small helper so screens don't repeat the same four kwargs everywhere
def surface_kwargs(**extra):
    kw = {
        "fg_color": c("surface"),
        "corner_radius": 14,
        "border_width": 1,
        "border_color": c("border"),
    }
    kw.update(extra)
    return kw
