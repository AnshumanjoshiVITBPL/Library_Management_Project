"""
Pages shared by the student and faculty portals. The two portals are almost
identical, the only real difference is the borrowing limit and the purchase
request page which faculty alone can see.
"""

from datetime import datetime

import customtkinter as ctk

import database as db
import theme as T
from widgets import (FormField, StatCard, Table, TextareaForm, button, card,
                     page_title, popup, confirm)


def _first_name(full):
    parts = full.split()
    # "Dr. S. K. Mishra" should greet as S., not Dr.
    if parts and parts[0].rstrip(".") in ("Dr", "Prof", "Mr", "Ms", "Mrs") and len(parts) > 1:
        return parts[1]
    return parts[0] if parts else full


def _greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def _due_label(issue):
    left = db.days_left(issue)
    if left < 0:
        return "%d days overdue" % -left, "bad"
    if left == 0:
        return "Due today", "warn"
    if left <= 3:
        return "%d days left" % left, "warn"
    return "%d days left" % left, "ok"


def _availability(book):
    if book["available"] == 0:
        return "All on loan", "bad"
    if book["available"] <= 2:
        return "%d of %d on shelf" % (book["available"], book["total"]), "warn"
    return "%d of %d on shelf" % (book["available"], book["total"]), "ok"


# --------------------------------------------------------------------------
# dashboard
# --------------------------------------------------------------------------

def dashboard(shell, parent):
    body = shell.body()
    person = shell.user
    policy = db.POLICY[person["role"]]
    loans = db.active_issues(person["id"])
    late = [r for r in loans if db.days_left(r) < 0]
    soon = [r for r in loans if 0 <= db.days_left(r) <= 3]
    dues = sum(r["fine"] for r in db.query(
        "select fine from issues where user_id = ? and fine > 0 and fine_paid = 0", (person["id"],)))

    head = card(body)
    head.pack(fill="x")
    row = ctk.CTkFrame(head, fg_color="transparent")
    row.pack(fill="x", padx=22, pady=18)
    words = ctk.CTkFrame(row, fg_color="transparent")
    words.pack(side="left")
    ctk.CTkLabel(words, text="%s, %s" % (_greeting(), _first_name(person["name"])),
                 font=T.font(22, "bold"), text_color=T.c("text"), anchor="w").pack(fill="x")
    ctk.CTkLabel(words, text="You can hold %d books for %d days at a time"
                 % (policy["limit"], policy["days"]),
                 font=T.font(12), text_color=T.c("muted"), anchor="w").pack(fill="x", pady=(2, 0))
    button(row, "Browse catalogue", lambda: shell.show("catalogue"), kind="primary",
           height=38, width=170).pack(side="right")
    button(row, "My books", lambda: shell.show("mybooks"), kind="ghost", height=38,
           width=130).pack(side="right", padx=10)

    stats = ctk.CTkFrame(body, fg_color="transparent")
    stats.pack(fill="x", pady=(16, 0))
    for i in range(4):
        stats.grid_columnconfigure(i, weight=1, uniform="stat")
    cards = [
        ("Books with you", "%d / %d" % (len(loans), policy["limit"]), "B", "accent"),
        ("Due in 3 days", len(soon), "D", "warn"),
        ("Overdue", len(late), "O", "bad" if late else "ok"),
        ("Fine payable", "Rs %d" % dues, "R", "bad" if dues else "ok"),
    ]
    for i, (label, value, symbol, kind) in enumerate(cards):
        StatCard(stats, label, value, symbol=symbol, kind=kind).grid(
            row=0, column=i, sticky="nsew", padx=(0, 0) if i == 3 else (0, 14))

    cols = ctk.CTkFrame(body, fg_color="transparent")
    cols.pack(fill="both", expand=True, pady=(16, 0))
    cols.grid_columnconfigure(0, weight=3)
    cols.grid_columnconfigure(1, weight=2)
    left = ctk.CTkFrame(cols, fg_color="transparent")
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
    right = ctk.CTkFrame(cols, fg_color="transparent")
    right.grid(row=0, column=1, sticky="nsew")

    ctk.CTkLabel(left, text="Currently borrowed", font=T.font(15, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x", pady=(0, 8))
    rows = []
    for loan in loans:
        text, colour = _due_label(loan)
        rows.append({
            "title": loan["title"],
            "due": db.pretty_date(loan["due_on"]),
            "left": (text, colour),
            "fine": "Rs %d" % db.fine_for(loan) if db.fine_for(loan) else "-",
        })
    borrowed = Table(left, [("title", "Title", 4), ("due", "Due on", 2),
                            ("left", "Status", 2), ("fine", "Fine", 1)],
                     height=210, empty_text="No books borrowed right now")
    borrowed.pack(fill="both", expand=True)
    borrowed.load(rows)

    ctk.CTkLabel(right, text="Notice board", font=T.font(15, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x", pady=(0, 8))
    board = card(right)
    board.pack(fill="both", expand=True)
    inner = ctk.CTkFrame(board, fg_color="transparent")
    inner.pack(fill="both", expand=True, padx=18, pady=14)
    for notice in db.notices()[:3]:
        ctk.CTkLabel(inner, text=notice["title"], font=T.font(13, "bold"),
                     text_color=T.c("text"), anchor="w", wraplength=300,
                     justify="left").pack(fill="x")
        ctk.CTkLabel(inner, text=db.pretty_date(notice["posted_on"]) + "  ·  " + notice["posted_by"],
                     font=T.font(10), text_color=T.c("accent"), anchor="w").pack(fill="x", pady=(1, 3))
        ctk.CTkLabel(inner, text=_clip(notice["body"], 130), font=T.font(11),
                     text_color=T.c("muted"), anchor="w", wraplength=300,
                     justify="left").pack(fill="x")
        ctk.CTkFrame(inner, height=1, fg_color=T.c("border")).pack(fill="x", pady=12)
    if not db.notices():
        ctk.CTkLabel(inner, text="No notices posted yet", font=T.font(12),
                     text_color=T.c("muted")).pack(pady=20)

    rules = card(right)
    rules.pack(fill="x", pady=(14, 0))
    pad = ctk.CTkFrame(rules, fg_color="transparent")
    pad.pack(fill="x", padx=18, pady=14)
    ctk.CTkLabel(pad, text="Borrowing rules", font=T.font(13, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x")
    for line in ("%d books at a time, %d days each" % (policy["limit"], policy["days"]),
                 "Renewal allowed once, before the due date",
                 "Fine of Rs %d per day after the due date" % db.FINE_PER_DAY,
                 "Unpaid fines above Rs %d block new issues" % db.FINE_BLOCK_LIMIT):
        bullet = ctk.CTkFrame(pad, fg_color="transparent")
        bullet.pack(fill="x", pady=3)
        ctk.CTkLabel(bullet, text="\u25aa", font=T.font(11), text_color=T.c("accent")).pack(side="left")
        ctk.CTkLabel(bullet, text=line, font=T.font(11), text_color=T.c("muted"),
                     anchor="w").pack(side="left", padx=8)


def _clip(text, limit):
    return text if len(text) <= limit else text[:limit - 3] + "..."


# --------------------------------------------------------------------------
# catalogue
# --------------------------------------------------------------------------

CATALOGUE_COLUMNS = [
    ("title", "Title", 4),
    ("author", "Author", 3),
    ("category", "Section", 2),
    ("rack", "Rack", 1),
    ("available", "Availability", 2),
]


def catalogue(shell, parent):
    body = shell.body(scroll=False)
    page_title(body, "Catalogue", "Search the whole collection by title, author, ISBN or publisher").pack(fill="x")

    filters = card(body)
    filters.pack(fill="x", pady=(14, 0))
    bar = ctk.CTkFrame(filters, fg_color="transparent")
    bar.pack(fill="x", padx=16, pady=14)

    search = ctk.CTkEntry(bar, height=40, corner_radius=10, placeholder_text="Type to search...",
                          fg_color=T.c("surface2"), border_color=T.c("border"), border_width=1,
                          text_color=T.c("text"), font=T.font(13))
    search.pack(side="left", fill="x", expand=True)

    category = ctk.CTkOptionMenu(bar, values=db.categories(), height=40, corner_radius=10, width=210,
                                 fg_color=T.c("surface2"), button_color=T.c("accent"),
                                 button_hover_color=T.c("accent"), text_color=T.c("text"),
                                 dropdown_fg_color=T.c("surface"), dropdown_text_color=T.c("text"),
                                 font=T.font(12))
    category.pack(side="left", padx=(10, 0))

    only_free = ctk.CTkCheckBox(bar, text="Available only", font=T.font(12), text_color=T.c("muted"),
                                fg_color=T.c("accent"), hover_color=T.c("accent"),
                                checkbox_width=20, checkbox_height=20, border_color=T.c("border"))
    only_free.pack(side="left", padx=(14, 0))

    result = ctk.CTkFrame(body, fg_color="transparent")
    result.pack(fill="x", pady=(12, 6))
    counter = ctk.CTkLabel(result, text="", font=T.font(12), text_color=T.c("muted"), anchor="w")
    counter.pack(side="left")

    table = Table(body, CATALOGUE_COLUMNS, actions=[("Reserve", None, "teal")], height=400)
    table.pack(fill="both", expand=True)

    def run(*_):
        books = db.list_books(search.get(), category.get(), bool(only_free.get()))
        rows = []
        for b in books:
            text, colour = _availability(b)
            rows.append({"id": b["id"], "title": b["title"], "author": b["author"],
                         "category": b["category"], "rack": b["rack"] or "-",
                         "available": (text, colour)})
        counter.configure(text="%d title(s) found" % len(rows))
        table.actions = [("Reserve", reserve, "teal")]
        table.load(rows)

    def reserve(row):
        target = db.book(row["id"])
        if target["available"] > 0:
            popup(shell, "Available on the shelf",
                  "%d copy(s) of '%s' are on the shelf at rack %s. Collect it from the issue desk."
                  % (target["available"], target["title"], target["rack"] or "-"), kind="info")
            return
        ok, message = db.reserve(shell.user["id"], target["id"])
        popup(shell, "Reservation", message, kind="ok" if ok else "warn")
        if ok:
            run()

    search.bind("<KeyRelease>", run)
    category.configure(command=run)
    only_free.configure(command=run)
    run()


# --------------------------------------------------------------------------
# books on loan, history, reservations
# --------------------------------------------------------------------------

LOAN_COLUMNS = [
    ("title", "Title", 4),
    ("author", "Author", 3),
    ("issued", "Issued on", 2),
    ("due", "Due on", 2),
    ("left", "Status", 2),
    ("fine", "Fine so far", 1.6),
]


def my_books(shell, parent):
    body = shell.body(scroll=False)
    person = shell.user
    policy = db.POLICY[person["role"]]
    page_title(body, "My books",
               "You may hold %d books for %d days. Renewal is allowed once, before the due date."
               % (policy["limit"], policy["days"])).pack(fill="x")

    loans = db.active_issues(person["id"])
    total_fine = sum(db.fine_for(r) for r in loans)
    strip = ctk.CTkFrame(body, fg_color="transparent")
    strip.pack(fill="x", pady=(14, 10))
    for i in range(3):
        strip.grid_columnconfigure(i, weight=1, uniform="m")
    for i, (label, value, kind) in enumerate([
        ("On loan", "%d of %d" % (len(loans), policy["limit"]), "accent"),
        ("Overdue", len([r for r in loans if db.days_left(r) < 0]), "bad"),
        ("Fine accruing", "Rs %d" % total_fine, "warn"),
    ]):
        StatCard(strip, label, value, kind=kind).grid(row=0, column=i, sticky="nsew",
                                                     padx=(0, 0) if i == 2 else (0, 14))

    table = Table(body, LOAN_COLUMNS, height=380, empty_text="You have no books on loan")
    table.pack(fill="both", expand=True)

    def renew(row):
        ok, message = db.renew(row["id"])
        popup(shell, "Renewal", message, kind="ok" if ok else "warn")
        load()

    table.actions = [("Renew", renew, "teal")]

    def load():
        rows = []
        for loan in db.active_issues(person["id"]):
            text, colour = _due_label(loan)
            fine = db.fine_for(loan)
            rows.append({
                "id": loan["id"], "title": loan["title"], "author": loan["author"],
                "issued": db.pretty_date(loan["issued_on"]), "due": db.pretty_date(loan["due_on"]),
                "left": (text, colour),
                "fine": ("Rs %d" % fine, "bad") if fine else "None",
            })
        table.load(rows)

    load()


def history(shell, parent):
    body = shell.body(scroll=False)
    page_title(body, "Borrowing history", "Every book you have returned so far").pack(fill="x")

    rows = []
    for loan in db.history(shell.user["id"]):
        paid = "No fine" if not loan["fine"] else ("Paid" if loan["fine_paid"] else "Unpaid")
        rows.append({
            "title": loan["title"], "author": loan["author"],
            "issued": db.pretty_date(loan["issued_on"]), "due": db.pretty_date(loan["due_on"]),
            "returned": db.pretty_date(loan["returned_on"]),
            "fine": ("Rs %d" % loan["fine"], "bad") if loan["fine"] else "-",
            "paid": (paid, {"No fine": "muted", "Paid": "ok", "Unpaid": "bad"}[paid]),
        })
    table = Table(body, [("title", "Title", 4), ("author", "Author", 3), ("issued", "Issued", 2),
                         ("due", "Due", 2), ("returned", "Returned", 2), ("fine", "Fine", 1.4),
                         ("paid", "Status", 1.4)],
                  height=470, empty_text="No returns recorded yet")
    table.pack(fill="both", expand=True, pady=(14, 0))
    table.load(rows)


def reservations(shell, parent):
    body = shell.body(scroll=False)
    page_title(body, "My reservations",
               "Titles you are queued for. A copy is held for three days once it comes back.").pack(fill="x")

    table = Table(body, [("title", "Title", 4), ("author", "Author", 3),
                         ("reserved", "Reserved on", 2), ("status", "Status", 2)],
                  height=440, empty_text="You have not reserved anything")
    table.pack(fill="both", expand=True, pady=(14, 0))

    def cancel(row):
        def go():
            db.cancel_reservation(row["id"])
            popup(shell, "Cancelled", "Your spot in the queue for '%s' was removed." % row["title"], kind="info")
            load()
        confirm(shell, "Cancel reservation", "Remove '%s' from your queue?" % row["title"], go)

    table.actions = [("Cancel", cancel, "danger")]

    def load():
        rows = []
        for item in db.my_reservations(shell.user["id"]):
            colour = {"waiting": "warn", "ready": "ok", "cancelled": "muted",
                      "collected": "muted"}.get(item["status"], "muted")
            rows.append({"id": item["id"], "title": item["title"], "author": item["author"],
                         "reserved": db.pretty_date(item["reserved_on"]),
                         "status": (item["status"].title(), colour)})
        table.load(rows)

    load()


# --------------------------------------------------------------------------
# purchase requests (faculty)
# --------------------------------------------------------------------------

def requests(shell, parent):
    body = shell.body()
    page_title(body, "Book purchase requests",
               "Suggest a title for the library to buy. The librarian reviews every request.").pack(fill="x")

    form = card(body)
    form.pack(fill="x", pady=(14, 0))
    pad = ctk.CTkFrame(form, fg_color="transparent")
    pad.pack(fill="x", padx=20, pady=18)

    row = ctk.CTkFrame(pad, fg_color="transparent")
    row.pack(fill="x")
    title = FormField(row, "Book title", placeholder="Designing Data-Intensive Applications", width=330)
    title.pack(side="left", expand=True, fill="x")
    ctk.CTkFrame(row, width=14, fg_color="transparent").pack(side="left")
    author = FormField(row, "Author", placeholder="Martin Kleppmann", width=330)
    author.pack(side="left", expand=True, fill="x")

    reason = TextareaForm(pad, "Why should the library buy it?", width=674, height=90)
    reason.pack(fill="x", pady=(14, 0))

    button(pad, "Send request", lambda: send(), kind="primary", height=40, width=170).pack(anchor="e", pady=(14, 0))

    ctk.CTkLabel(body, text="My requests", font=T.font(15, "bold"), text_color=T.c("text"),
                 anchor="w").pack(fill="x", pady=(22, 8))
    table = Table(body, [("title", "Title", 4), ("author", "Author", 3), ("sent", "Sent on", 2),
                         ("status", "Status", 1.6), ("remark", "Librarian remark", 3)],
                  height=240, empty_text="You have not sent any requests")
    table.pack(fill="both", expand=True)

    def load():
        rows = []
        for item in db.my_requests(shell.user["id"]):
            colour = {"pending": "warn", "approved": "ok", "rejected": "bad"}.get(item["status"], "muted")
            rows.append({"title": item["title"], "author": item["author"] or "-",
                         "sent": db.pretty_date(item["requested_on"]),
                         "status": (item["status"].title(), colour),
                         "remark": item["remark"] or "-"})
        table.load(rows)

    def send():
        ok, message = db.add_request(shell.user["id"], title.get(), author.get(), reason.get())
        popup(shell, "Purchase request", message, kind="ok" if ok else "warn")
        if ok:
            title.clear()
            author.clear()
            reason.clear()
            load()

    load()


# --------------------------------------------------------------------------
# notices, profile
# --------------------------------------------------------------------------

def notices(shell, parent):
    body = shell.body()
    page_title(body, "Notices", "Announcements from the central library").pack(fill="x")

    items = db.notices()
    if not items:
        empty = card(body)
        empty.pack(fill="x", pady=(16, 0))
        ctk.CTkLabel(empty, text="Nothing has been posted yet", font=T.font(13),
                     text_color=T.c("muted")).pack(pady=40)
        return

    for notice in items:
        block = card(body)
        block.pack(fill="x", pady=(14, 0))
        ctk.CTkFrame(block, fg_color=T.c("accent"), width=4).place(relheight=0.6, rely=0.2, x=0)
        pad = ctk.CTkFrame(block, fg_color="transparent")
        pad.pack(fill="x", padx=22, pady=16)

        top = ctk.CTkFrame(pad, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=notice["title"], font=T.font(15, "bold"),
                     text_color=T.c("text"), anchor="w").pack(side="left")
        ctk.CTkLabel(top, text=db.pretty_date(notice["posted_on"]), font=T.font(11),
                     text_color=T.c("muted")).pack(side="right")
        ctk.CTkLabel(pad, text="Posted by " + (notice["posted_by"] or "Library desk"),
                     font=T.font(11), text_color=T.c("accent2"), anchor="w").pack(fill="x", pady=(2, 8))
        ctk.CTkLabel(pad, text=notice["body"], font=T.font(12), text_color=T.c("muted"),
                     anchor="w", justify="left", wraplength=820).pack(fill="x")


def profile(shell, parent):
    body = shell.body()
    person = shell.user
    page_title(body, "My profile", "Your library account details").pack(fill="x")

    cols = ctk.CTkFrame(body, fg_color="transparent")
    cols.pack(fill="both", expand=True, pady=(16, 0))
    cols.grid_columnconfigure(0, weight=1, uniform="p")
    cols.grid_columnconfigure(1, weight=1, uniform="p")

    left = ctk.CTkFrame(cols, fg_color="transparent")
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
    right = ctk.CTkFrame(cols, fg_color="transparent")
    right.grid(row=0, column=1, sticky="nsew")

    info = card(left)
    info.pack(fill="x")
    pad = ctk.CTkFrame(info, fg_color="transparent")
    pad.pack(fill="x", padx=22, pady=20)
    avatar = ctk.CTkLabel(pad, text=person["name"].strip()[0].upper(), width=56, height=56,
                          corner_radius=28, fg_color=T.c("accent"), text_color="#ffffff",
                          font=T.font(24, "bold"))
    avatar.pack(anchor="w")
    ctk.CTkLabel(pad, text=person["name"], font=T.font(20, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x", pady=(12, 0))
    ctk.CTkLabel(pad, text=person["role"].title() + "  ·  " + person["code"], font=T.font(12),
                 text_color=T.c("accent"), anchor="w").pack(fill="x")

    ctk.CTkFrame(pad, height=1, fg_color=T.c("border")).pack(fill="x", pady=16)
    for label, value in (("School / Department", person["department"] or "-"),
                         ("Account status", person["status"].title()),
                         ("Member since", db.pretty_date(person["created_on"])),
                         ("Borrowing limit", "%d books / %d days" % (
                             db.POLICY[person["role"]]["limit"], db.POLICY[person["role"]]["days"]))):
        line = ctk.CTkFrame(pad, fg_color="transparent")
        line.pack(fill="x", pady=5)
        ctk.CTkLabel(line, text=label, font=T.font(12), text_color=T.c("muted"),
                     anchor="w").pack(side="left")
        ctk.CTkLabel(line, text=value, font=T.font(12, "bold"), text_color=T.c("text"),
                     anchor="e").pack(side="right")

    contact = card(right)
    contact.pack(fill="x")
    cpad = ctk.CTkFrame(contact, fg_color="transparent")
    cpad.pack(fill="x", padx=22, pady=20)
    ctk.CTkLabel(cpad, text="Contact details", font=T.font(15, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x")
    email = FormField(cpad, "Email", width=380)
    email.set(person["email"])
    email.pack(fill="x", pady=(14, 10))
    phone = FormField(cpad, "Phone", width=380)
    phone.set(person["phone"])
    phone.pack(fill="x")

    def save():
        if phone.get() and not (phone.get().isdigit() and len(phone.get()) == 10):
            popup(shell, "Check phone number", "It should be exactly 10 digits", kind="warn")
            return
        db.save_profile(person["id"], email.get(), phone.get())
        shell.app.user = db.user(person["id"])
        popup(shell, "Saved", "Your contact details were updated", kind="ok")

    button(cpad, "Save changes", save, kind="primary", height=40).pack(anchor="e", pady=(16, 0))

    security = card(right)
    security.pack(fill="x", pady=(16, 0))
    spad = ctk.CTkFrame(security, fg_color="transparent")
    spad.pack(fill="x", padx=22, pady=20)
    ctk.CTkLabel(spad, text="Change password", font=T.font(15, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x")
    old = FormField(spad, "Current password", show="*", width=380)
    old.pack(fill="x", pady=(14, 10))
    new = FormField(spad, "New password", show="*", width=380)
    new.pack(fill="x")

    def update():
        ok, message = db.change_password(person["id"], old.widget.get(), new.widget.get())
        popup(shell, "Password", message, kind="ok" if ok else "warn")
        if ok:
            old.clear()
            new.clear()

    button(spad, "Update password", update, kind="teal", height=40).pack(anchor="e", pady=(16, 0))
