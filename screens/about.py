"""The Help & rules page, shared by all three portals."""

import customtkinter as ctk

import database as db
import theme as T
from widgets import card, page_title

RULES = [
    "Students may borrow 2 books at a time for 14 days.",
    "Faculty may borrow 5 books at a time for 60 days.",
    "A book can be renewed once, only before its due date and only if nobody else has queued for it.",
    "Late returns are charged Rs %d for every extra day." % db.FINE_PER_DAY,
    "Unpaid fines above Rs %d stop you from borrowing anything new." % db.FINE_BLOCK_LIMIT,
    "Reference books, journals and question papers are for reading room use only.",
    "A reserved copy is held at the desk for three working days.",
    "Carry your VIT Bhopal ID card to the issue counter every time.",
    "Damaged or lost books must be replaced, or twice the price paid.",
]

TIMINGS = [
    ("Monday to Friday", "8:30 AM - 8:00 PM"),
    ("Saturday", "9:00 AM - 5:00 PM"),
    ("Sunday", "Closed"),
    ("Reading hall (exam weeks)", "Open till 2:00 AM"),
    ("Issue counter", "9:00 AM - 6:00 PM"),
]

ROLES = [
    ("Student", "Search, borrow, renew, reserve, read notices", "2 books / 14 days"),
    ("Faculty", "Everything a student can, plus purchase requests", "5 books / 60 days"),
    ("Librarian", "Issue and return, catalogue, users, fines, reports", "Full access"),
]


def about(shell, parent):
    body = shell.body()
    page_title(body, "Help and library rules",
               "Everything you need to know about using the central library").pack(fill="x")

    banner = card(body, fg_color=T.c("accent"))
    banner.pack(fill="x", pady=(16, 0))
    pad = ctk.CTkFrame(banner, fg_color="transparent")
    pad.pack(fill="x", padx=24, pady=20)
    ctk.CTkLabel(pad, text="VIT Bhopal University", font=T.font(22, "bold"),
                 text_color="#ffffff", anchor="w").pack(fill="x")
    ctk.CTkLabel(pad, text="Central Library  ·  Library Management System  ·  Academic year 2026-27",
                 font=T.font(13), text_color="#d6e6fb", anchor="w").pack(fill="x", pady=(4, 0))

    cols = ctk.CTkFrame(body, fg_color="transparent")
    cols.pack(fill="both", expand=True, pady=(16, 0))
    cols.grid_columnconfigure(0, weight=3, uniform="a")
    cols.grid_columnconfigure(1, weight=2, uniform="a")
    left = ctk.CTkFrame(cols, fg_color="transparent")
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
    right = ctk.CTkFrame(cols, fg_color="transparent")
    right.grid(row=0, column=1, sticky="nsew")

    rules = card(left)
    rules.pack(fill="x")
    rpad = ctk.CTkFrame(rules, fg_color="transparent")
    rpad.pack(fill="x", padx=22, pady=20)
    ctk.CTkLabel(rpad, text="Library rules", font=T.font(16, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x", pady=(0, 12))
    for i, rule in enumerate(RULES, start=1):
        line = ctk.CTkFrame(rpad, fg_color="transparent")
        line.pack(fill="x", pady=5)
        ctk.CTkLabel(line, text="%02d" % i, font=T.font(11, "bold"), width=24,
                     text_color=T.c("accent"), anchor="w").pack(side="left")
        ctk.CTkLabel(line, text=rule, font=T.font(12), text_color=T.c("muted"),
                     anchor="w", justify="left", wraplength=560).pack(side="left", padx=(6, 0))

    roles = card(left)
    roles.pack(fill="x", pady=(16, 0))
    qpad = ctk.CTkFrame(roles, fg_color="transparent")
    qpad.pack(fill="x", padx=22, pady=20)
    ctk.CTkLabel(qpad, text="Who can do what", font=T.font(16, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x", pady=(0, 12))
    for name, can, limit in ROLES:
        block = ctk.CTkFrame(qpad, fg_color=T.c("surface2"), corner_radius=12)
        block.pack(fill="x", pady=5)
        inner = ctk.CTkFrame(block, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(inner, text=name, font=T.font(13, "bold"),
                     text_color=T.c("accent2"), anchor="w").pack(fill="x")
        ctk.CTkLabel(inner, text=can, font=T.font(11), text_color=T.c("muted"),
                     anchor="w", wraplength=480, justify="left").pack(fill="x", pady=(2, 0))
        ctk.CTkLabel(inner, text=limit, font=T.font(11, "bold"),
                     text_color=T.c("text"), anchor="w").pack(fill="x", pady=(4, 0))

    hours = card(right)
    hours.pack(fill="x")
    hpad = ctk.CTkFrame(hours, fg_color="transparent")
    hpad.pack(fill="x", padx=22, pady=20)
    ctk.CTkLabel(hpad, text="Timings", font=T.font(16, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x", pady=(0, 12))
    for day, slot in TIMINGS:
        line = ctk.CTkFrame(hpad, fg_color="transparent")
        line.pack(fill="x", pady=6)
        ctk.CTkLabel(line, text=day, font=T.font(12), text_color=T.c("muted"),
                     anchor="w").pack(side="left")
        ctk.CTkLabel(line, text=slot, font=T.font(12, "bold"), text_color=T.c("text"),
                     anchor="e").pack(side="right")

    contact = card(right)
    contact.pack(fill="x", pady=(16, 0))
    cpad = ctk.CTkFrame(contact, fg_color="transparent")
    cpad.pack(fill="x", padx=22, pady=20)
    ctk.CTkLabel(cpad, text="Reach us", font=T.font(16, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x", pady=(0, 12))
    for label, value in (("Location", "Ground floor, Academic Block 1"),
                         ("Email", "library@vitbhopal.ac.in"),
                         ("Phone", "+91 755 667 0100"),
                         ("Desk hours", "9:00 AM - 6:00 PM")):
        ctk.CTkLabel(cpad, text=label.upper(), font=T.font(10, "bold"),
                     text_color=T.c("accent"), anchor="w").pack(fill="x")
        ctk.CTkLabel(cpad, text=value, font=T.font(12), text_color=T.c("muted"),
                     anchor="w").pack(fill="x", pady=(1, 10))

    tech = card(right)
    tech.pack(fill="x", pady=(16, 0))
    tpad = ctk.CTkFrame(tech, fg_color="transparent")
    tpad.pack(fill="x", padx=22, pady=20)
    ctk.CTkLabel(tpad, text="About this project", font=T.font(16, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x", pady=(0, 10))
    ctk.CTkLabel(tpad, text="A desktop library management system built for the VIT Bhopal "
                            "central library. It handles cataloguing, circulation, reservations, "
                            "fines and reporting, with a separate portal for students, faculty "
                            "and library staff.",
                 font=T.font(12), text_color=T.c("muted"), anchor="w", justify="left",
                 wraplength=380).pack(fill="x")
    ctk.CTkFrame(tpad, height=1, fg_color=T.c("border")).pack(fill="x", pady=12)
    for label, value in (("Language", "Python 3"),
                         ("Interface", "CustomTkinter"),
                         ("Database", "SQLite"),
                         ("Charts", "Matplotlib"),
                         ("Reports", "openpyxl (xlsx)")):
        line = ctk.CTkFrame(tpad, fg_color="transparent")
        line.pack(fill="x", pady=3)
        ctk.CTkLabel(line, text=label, font=T.font(11), text_color=T.c("muted"),
                     anchor="w").pack(side="left")
        ctk.CTkLabel(line, text=value, font=T.font(11, "bold"), text_color=T.c("text"),
                     anchor="e").pack(side="right")
