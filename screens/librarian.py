"""
Librarian portal: dashboard, circulation desk, catalogue management, members,
overdues, reservation queue, purchase requests, notices and reports.
"""

from datetime import date
from tkinter import filedialog

import customtkinter as ctk

import database as db
import reports
import theme as T
from screens.about import about
from screens.shell import PortalShell
from widgets import (FormField, StatCard, Table, TextareaForm, ask_text, button,
                     card, chart, confirm, page_title, popup)

CATEGORIES = ["Computer Science", "Electronics", "Mechanical", "Civil", "Electrical",
              "Mathematics", "Physics", "Chemistry", "Literature", "Management",
              "Competitive Exams", "General"]


def _pick(value):
    """Turn an 'All' dropdown choice into None, anything else into a db value."""
    return None if value == "All" else value.lower()


# --------------------------------------------------------------------------
# dashboard
# --------------------------------------------------------------------------

def _issues_chart(ax, col):
    data = db.issues_last_days(14)
    ax.bar(range(len(data)), [d[1] for d in data], color=col["accent"], width=0.62)
    ax.set_xticks(range(len(data)))
    ax.set_xticklabels([d[0] for d in data], rotation=50, ha="right", fontsize=7)
    ax.set_title("Books issued over the last 14 days", color=col["text"], fontsize=11, fontweight="bold")
    ax.grid(axis="y", color=col["grid"], alpha=0.4)
    ax.set_axisbelow(True)
    ax.margins(y=0.15)


def _category_chart(ax, col):
    rows = db.category_split()
    if not rows:
        ax.text(0.5, 0.5, "No circulation data yet", color=col["muted"], ha="center")
        ax.set_xticks([])
        ax.set_yticks([])
        return
    palette = [col["accent"], col["accent2"], col["gold"], col["bad"], col["ok"],
               "#8b5cf6", "#f472b6", "#38bdf8", "#a3e635", "#fb923c"]
    names = [r["name"] for r in rows][::-1]
    counts = [r["n"] for r in rows][::-1]
    ax.barh(names, counts, color=[palette[i % len(palette)] for i in range(len(names))], height=0.6)
    ax.set_title("Most borrowed sections", color=col["text"], fontsize=11, fontweight="bold")
    ax.grid(axis="x", color=col["grid"], alpha=0.4)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=8)


def dashboard(shell, parent):
    body = shell.body()
    n = db.stats()
    page_title(body, "Library dashboard", "A live picture of the collection and circulation").pack(fill="x")

    for row_index, group in enumerate([
        [("Titles", n["titles"], "T", "accent"), ("Copies on shelf", "%d / %d" % (n["shelf"], n["copies"]), "S", "accent2"),
         ("Books issued", n["out"], "I", "gold"), ("Overdue", n["overdue"], "O", "bad" if n["overdue"] else "ok")],
        [("Members", n["total"], "M", "accent"), ("Awaiting approval", n["pending"], "P", "warn" if n["pending"] else "ok"),
         ("Fine collected", "Rs %d" % n["fine_collected"], "C", "ok"), ("Fine pending", "Rs %d" % n["fine_pending"], "D", "bad" if n["fine_pending"] else "ok")],
    ]):
        strip = ctk.CTkFrame(body, fg_color="transparent")
        strip.pack(fill="x", pady=(14 if row_index else 16, 0))
        for i in range(4):
            strip.grid_columnconfigure(i, weight=1, uniform="d%d" % row_index)
        for i, (label, value, symbol, kind) in enumerate(group):
            StatCard(strip, label, value, symbol=symbol, kind=kind).grid(
                row=0, column=i, sticky="nsew", padx=(0, 0) if i == 3 else (0, 14))

    charts = ctk.CTkFrame(body, fg_color="transparent")
    charts.pack(fill="x", pady=(16, 0))
    charts.grid_columnconfigure(0, weight=3, uniform="ch")
    charts.grid_columnconfigure(1, weight=2, uniform="ch")
    chart(charts, _issues_chart, height=250).grid(row=0, column=0, sticky="nsew", padx=(0, 14))
    chart(charts, _category_chart, height=250).grid(row=0, column=1, sticky="nsew")

    bottom = ctk.CTkFrame(body, fg_color="transparent")
    bottom.pack(fill="both", expand=True, pady=(16, 0))
    bottom.grid_columnconfigure(0, weight=3, uniform="bt")
    bottom.grid_columnconfigure(1, weight=2, uniform="bt")

    left = ctk.CTkFrame(bottom, fg_color="transparent")
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
    ctk.CTkLabel(left, text="Most borrowed titles", font=T.font(15, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x", pady=(0, 8))
    popular = Table(left, [("rank", "#", 1), ("title", "Title", 6), ("times", "Times issued", 2)], height=200,
                    empty_text="No circulation yet")
    popular.pack(fill="both", expand=True)
    popular.load([{"rank": i + 1, "title": b["title"], "times": b["times"]}
                  for i, b in enumerate(db.top_books(6))])

    right = ctk.CTkFrame(bottom, fg_color="transparent")
    right.grid(row=0, column=1, sticky="nsew")

    alert = card(right, fg_color=T.c("surface"))
    alert.pack(fill="x")
    apad = ctk.CTkFrame(alert, fg_color="transparent")
    apad.pack(fill="x", padx=20, pady=18)
    ctk.CTkLabel(apad, text="Needs your attention", font=T.font(14, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x")
    for label, count, page, colour in (
        ("Books past the due date", n["overdue"], "overdue", "bad"),
        ("Registrations to approve", n["pending"], "members", "warn"),
        ("Reservations waiting", n["reservations"], "queue", "accent"),
        ("Purchase requests pending", len(db.all_requests("pending")), "requests", "accent2"),
    ):
        line = ctk.CTkFrame(apad, fg_color="transparent")
        line.pack(fill="x", pady=6)
        ctk.CTkLabel(line, text=label, font=T.font(12), text_color=T.c("muted"),
                     anchor="w").pack(side="left")
        ctk.CTkButton(line, text=str(count), width=46, height=26, corner_radius=8,
                      fg_color=T.c(colour), hover_color=T.c(colour), text_color="#ffffff",
                      font=T.font(12, "bold"), command=lambda p=page: shell.show(p)).pack(side="right")

    ctk.CTkLabel(right, text="Latest transactions", font=T.font(15, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x", pady=(18, 8))
    recent = Table(right, [("who", "Member", 3), ("title", "Book", 4),
                           ("when", "Issued", 2), ("state", "Status", 2)], height=180)
    recent.pack(fill="both", expand=True)
    rows = []
    for loan in db.transactions()[:8]:
        state = "Returned" if loan["returned_on"] else ("Overdue" if db.days_left(loan) < 0 else "On loan")
        rows.append({"who": "%s (%s)" % (loan["user_name"], loan["user_code"]), "title": loan["title"],
                     "when": db.pretty_date(loan["issued_on"]),
                     "state": (state, {"Returned": "muted", "Overdue": "bad", "On loan": "ok"}[state])})
    recent.load(rows)


# --------------------------------------------------------------------------
# circulation desk
# --------------------------------------------------------------------------

def _loan_state(left):
    """Turn a days-remaining number into a label plus a colour for the table."""
    if left < 0:
        return "%d days late" % -left, "bad"
    if left == 0:
        return "Due today", "warn"
    if left <= 3:
        return "%d days left" % left, "warn"
    return "%d days left" % left, "ok"


def desk(shell, parent):
    body = shell.body()
    page_title(body, "Circulation desk", "Issue a book to a member or take one back").pack(fill="x")

    # ----- issue side -----------------------------------------------------
    issue_card = card(body)
    issue_card.pack(fill="x", pady=(16, 0))
    ipad = ctk.CTkFrame(issue_card, fg_color="transparent")
    ipad.pack(fill="x", padx=22, pady=20)

    ctk.CTkLabel(ipad, text="Issue a book", font=T.font(16, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x")
    ctk.CTkLabel(ipad, text="Look the member up first, then pick the title from the search below.",
                 font=T.font(11), text_color=T.c("muted"), anchor="w").pack(fill="x", pady=(2, 14))

    lookup = ctk.CTkFrame(ipad, fg_color="transparent")
    lookup.pack(fill="x")
    code = FormField(lookup, "Member ID", placeholder="22BEC10145 or EMP1042", width=280)
    code.pack(side="left")
    button(lookup, "Look up", lambda: find_member(), kind="primary", height=38, width=120
           ).pack(side="left", padx=(12, 0), pady=(20, 0))

    panel = ctk.CTkFrame(ipad, fg_color=T.c("surface2"), corner_radius=12)
    panel.pack(fill="x", pady=(14, 0))
    panel_body = ctk.CTkFrame(panel, fg_color="transparent")
    panel_body.pack(fill="x", padx=18, pady=14)
    hint = ctk.CTkLabel(panel_body, text="Enter a member ID to see their borrowing position",
                        font=T.font(12), text_color=T.c("muted"), anchor="w")
    hint.pack(fill="x")

    picked = {"code": None}

    def find_member():
        for child in panel_body.winfo_children():
            child.destroy()
        person = db.user_by_code(code.get())
        if not person:
            picked["code"] = None
            ctk.CTkLabel(panel_body, text="No member found with that ID", font=T.font(13, "bold"),
                         text_color=T.c("bad"), anchor="w").pack(fill="x")
            return

        allowed, reason = db.can_issue(person)
        picked["code"] = person["code"] if allowed else None
        policy = db.POLICY[person["role"]]
        held = len(db.active_issues(person["id"]))
        dues = sum(r["fine"] for r in db.query(
            "select fine from issues where user_id = ? and fine > 0 and fine_paid = 0", (person["id"],)))

        top = ctk.CTkFrame(panel_body, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=person["name"], font=T.font(15, "bold"),
                     text_color=T.c("text"), anchor="w").pack(side="left")
        ctk.CTkLabel(top, text="%s  ·  %s" % (person["code"], person["role"].title()),
                     font=T.font(12), text_color=T.c("accent"), anchor="w").pack(side="left", padx=10)

        if allowed:
            verdict = "Eligible to borrow"
            colour = T.c("ok")
        else:
            verdict = reason
            colour = T.c("bad")
        ctk.CTkLabel(panel_body, text=verdict, font=T.font(12, "bold"),
                     text_color=colour, anchor="w", wraplength=760, justify="left").pack(fill="x", pady=(6, 10))

        grid = ctk.CTkFrame(panel_body, fg_color="transparent")
        grid.pack(fill="x")
        for i in range(4):
            grid.grid_columnconfigure(i, weight=1, uniform="g")
        for i, (label, value) in enumerate([("Books held", "%d of %d" % (held, policy["limit"])),
                                            ("Loan period", "%d days" % policy["days"]),
                                            ("Unpaid fine", "Rs %d" % dues),
                                            ("Department", person["department"] or "-")]):
            cell = ctk.CTkFrame(grid, fg_color="transparent")
            cell.grid(row=0, column=i, sticky="w", padx=(0, 12))
            ctk.CTkLabel(cell, text=label.upper(), font=T.font(10, "bold"),
                         text_color=T.c("muted"), anchor="w").pack(fill="x")
            ctk.CTkLabel(cell, text=value, font=T.font(13, "bold"), text_color=T.c("text"),
                         anchor="w", wraplength=180, justify="left").pack(fill="x")

    code.widget.bind("<Return>", lambda e: find_member())

    ctk.CTkFrame(ipad, height=1, fg_color=T.c("border")).pack(fill="x", pady=18)

    ctk.CTkLabel(ipad, text="Find the title", font=T.font(13, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x")
    bar = ctk.CTkFrame(ipad, fg_color="transparent")
    bar.pack(fill="x", pady=(8, 10))
    search = ctk.CTkEntry(bar, height=38, corner_radius=10, placeholder_text="Search by title, author or ISBN...",
                          fg_color=T.c("surface2"), border_color=T.c("border"), border_width=1,
                          text_color=T.c("text"), font=T.font(13))
    search.pack(side="left", fill="x", expand=True)
    section = ctk.CTkOptionMenu(bar, values=db.categories(), height=38, corner_radius=10, width=200,
                                fg_color=T.c("surface2"), button_color=T.c("accent"),
                                button_hover_color=T.c("accent"), text_color=T.c("text"),
                                dropdown_fg_color=T.c("surface"), dropdown_text_color=T.c("text"),
                                font=T.font(12))
    section.pack(side="left", padx=(10, 0))
    counter = ctk.CTkLabel(ipad, text="", font=T.font(11), text_color=T.c("muted"), anchor="w")
    counter.pack(fill="x")

    results = Table(ipad, [("title", "Title", 5), ("author", "Author", 3), ("category", "Section", 2),
                           ("rack", "Rack", 1), ("available", "On shelf", 2)], height=250,
                    empty_text="No matching titles")
    results.pack(fill="x", pady=(8, 0))

    def run_search(*_):
        books = db.list_books(search.get(), section.get())
        rows = []
        for b in books:
            if b["available"] > 0:
                state = ("%d of %d" % (b["available"], b["total"]), "ok")
            else:
                state = ("None", "bad")
            rows.append({"id": b["id"], "title": b["title"], "author": b["author"],
                         "category": b["category"], "rack": b["rack"] or "-", "available": state})
        counter.configure(text="%d title(s) in the catalogue" % len(rows))
        results.load(rows)

    def issue(row):
        if not picked["code"]:
            popup(shell, "Pick a member first", "Look up the member ID above before issuing a book.", kind="warn")
            return
        ok, message = db.issue_book(picked["code"], row["id"], shell.user["name"])
        popup(shell, "Issue book", message, kind="ok" if ok else "error")
        if ok:
            find_member()
            run_search()

    results.actions = [("Issue", issue, "primary")]
    search.bind("<KeyRelease>", run_search)
    section.configure(command=run_search)
    run_search()

    # ----- return side ----------------------------------------------------
    back_card = card(body)
    back_card.pack(fill="x", pady=(18, 0))
    bpad = ctk.CTkFrame(back_card, fg_color="transparent")
    bpad.pack(fill="x", padx=22, pady=20)
    ctk.CTkLabel(bpad, text="Return a book", font=T.font(16, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x")
    ctk.CTkLabel(bpad, text="Fines are worked out automatically at Rs %d per day past the due date."
                 % db.FINE_PER_DAY, font=T.font(11), text_color=T.c("muted"), anchor="w").pack(fill="x", pady=(2, 14))

    return_lookup = ctk.CTkFrame(bpad, fg_color="transparent")
    return_lookup.pack(fill="x")
    return_code = FormField(return_lookup, "Member ID", placeholder="Whose book is coming back?", width=280)
    return_code.pack(side="left")
    button(return_lookup, "Show loans", lambda: show_loans(), kind="teal", height=38, width=140
           ).pack(side="left", padx=(12, 0), pady=(20, 0))

    loans = Table(bpad, [("title", "Title", 5), ("issued", "Issued", 2), ("due", "Due", 2),
                         ("state", "Status", 2), ("fine", "Fine now", 2)], height=220,
                  empty_text="Look up a member to see what they are holding")
    loans.pack(fill="x", pady=(14, 0))

    def do_return(row):
        ok, message, _fine = db.return_book(row["id"])
        popup(shell, "Return book", message, kind="ok" if ok else "error")
        if ok:
            show_loans()
            run_search()

    def take_fine(row):
        db.mark_fine_paid(row["id"])
        popup(shell, "Fine settled", "Rs %d marked as paid for %s." % (row["amount"], row["who"]), kind="ok")
        show_loans()

    loans.actions = [("Return", do_return, "primary")]

    def show_loans():
        person = db.user_by_code(return_code.get())
        if not person:
            popup(shell, "Not found", "No member with that ID", kind="warn")
            return
        rows = []
        for loan in db.active_issues(person["id"]):
            fine = db.fine_for(loan)
            rows.append({"id": loan["id"], "title": loan["title"],
                         "issued": db.pretty_date(loan["issued_on"]), "due": db.pretty_date(loan["due_on"]),
                         "state": _loan_state(db.days_left(loan)),
                         "fine": ("Rs %d" % fine, "bad") if fine else "None"})
        # returned-but-unpaid items show up too so the desk can settle them
        for loan in db.history(person["id"]):
            if loan["fine"] and not loan["fine_paid"]:
                rows.append({"id": loan["id"], "title": loan["title"] + "  (already returned)",
                             "issued": db.pretty_date(loan["issued_on"]), "due": db.pretty_date(loan["due_on"]),
                             "state": ("Returned", "muted"), "fine": ("Rs %d" % loan["fine"], "bad"),
                             "settle": True, "amount": loan["fine"], "who": person["name"]})
        loans.actions = [("Return", do_return, "primary")]
        if any(r.get("settle") for r in rows):
            loans.actions.append(("Take fine", lambda r: take_fine(r) if r.get("settle") else popup(
                shell, "Nothing to settle", "This record has no unpaid fine.", kind="info"), "gold"))
        loans.load(rows)

    return_code.widget.bind("<Return>", lambda e: show_loans())


# --------------------------------------------------------------------------
# catalogue management
# --------------------------------------------------------------------------

def book_form(shell, on_done, existing=None):
    win = ctk.CTkToplevel(shell)
    win.title("Edit book" if existing else "Add a book")
    win.geometry("560x640")
    win.resizable(False, False)
    win.configure(fg_color=T.c("bg"))
    win.attributes("-topmost", True)
    win.after(120, win.grab_set)

    ctk.CTkFrame(win, fg_color=T.c("accent"), height=5).pack(fill="x")
    body = ctk.CTkScrollableFrame(win, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=28, pady=22)

    ctk.CTkLabel(body, text="Book details", font=T.font(19, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x", pady=(0, 14))

    fields = {}
    fields["title"] = FormField(body, "Title", width=480)
    fields["title"].pack(fill="x", pady=(0, 10))
    fields["author"] = FormField(body, "Author", width=480)
    fields["author"].pack(fill="x", pady=(0, 10))

    row = ctk.CTkFrame(body, fg_color="transparent")
    row.pack(fill="x", pady=(0, 10))
    fields["isbn"] = FormField(row, "ISBN", width=232)
    fields["isbn"].pack(side="left")
    ctk.CTkFrame(row, width=16, fg_color="transparent").pack(side="left")
    fields["year"] = FormField(row, "Year of publication", placeholder="2020", width=232)
    fields["year"].pack(side="left")

    fields["publisher"] = FormField(body, "Publisher", width=480)
    fields["publisher"].pack(fill="x", pady=(0, 10))

    row2 = ctk.CTkFrame(body, fg_color="transparent")
    row2.pack(fill="x", pady=(0, 10))
    fields["category"] = FormField(row2, "Section", values=CATEGORIES, width=232)
    fields["category"].pack(side="left")
    ctk.CTkFrame(row2, width=16, fg_color="transparent").pack(side="left")
    fields["rack"] = FormField(row2, "Rack / shelf", placeholder="A1-04", width=232)
    fields["rack"].pack(side="left")

    row3 = ctk.CTkFrame(body, fg_color="transparent")
    row3.pack(fill="x", pady=(0, 10))
    fields["price"] = FormField(row3, "Price in Rs", placeholder="650", width=232)
    fields["price"].pack(side="left")
    ctk.CTkFrame(row3, width=16, fg_color="transparent").pack(side="left")
    fields["total"] = FormField(row3, "Number of copies", placeholder="3", width=232)
    fields["total"].pack(side="left")

    note = ctk.CTkLabel(body, text="", font=T.font(12), text_color=T.c("bad"),
                        anchor="w", wraplength=480, justify="left")
    note.pack(fill="x", pady=(4, 0))

    if existing:
        for key in ("title", "author", "isbn", "publisher", "category", "rack"):
            fields[key].set(existing[key])
        fields["year"].set(existing["year"] or "")
        fields["price"].set(int(existing["price"]) if existing["price"] else "")
        fields["total"].set(existing["total"])

    def save():
        data = {key: field.get() for key, field in fields.items()}
        ok, message = (db.update_book(existing["id"], data) if existing else db.add_book(data))
        if not ok:
            note.configure(text=message)
            return
        win.destroy()
        popup(shell, "Catalogue", message, kind="ok")
        on_done()

    buttons = ctk.CTkFrame(body, fg_color="transparent")
    buttons.pack(fill="x", pady=(18, 0))
    button(buttons, "Cancel", win.destroy, kind="ghost", width=120).pack(side="right")
    button(buttons, "Save book", save, kind="primary", width=150).pack(side="right", padx=10)


def books(shell, parent):
    body = shell.body(scroll=False)
    page_title(body, "Catalogue", "Add, edit and remove titles held by the library").pack(fill="x")

    bar = card(body)
    bar.pack(fill="x", pady=(14, 0))
    row = ctk.CTkFrame(bar, fg_color="transparent")
    row.pack(fill="x", padx=16, pady=14)
    search = ctk.CTkEntry(row, height=40, corner_radius=10, placeholder_text="Search the catalogue...",
                          fg_color=T.c("surface2"), border_color=T.c("border"), border_width=1,
                          text_color=T.c("text"), font=T.font(13))
    search.pack(side="left", fill="x", expand=True)
    section = ctk.CTkOptionMenu(row, values=db.categories(), height=40, corner_radius=10, width=210,
                                fg_color=T.c("surface2"), button_color=T.c("accent"),
                                button_hover_color=T.c("accent"), text_color=T.c("text"),
                                dropdown_fg_color=T.c("surface"), dropdown_text_color=T.c("text"),
                                font=T.font(12))
    section.pack(side="left", padx=(10, 0))
    button(row, "Add a book", lambda: book_form(shell, load), kind="primary", height=40,
           width=150).pack(side="left", padx=(10, 0))

    counter = ctk.CTkLabel(body, text="", font=T.font(11), text_color=T.c("muted"), anchor="w")
    counter.pack(fill="x", pady=(12, 6))

    table = Table(body, [("title", "Title", 5), ("author", "Author", 3), ("isbn", "ISBN", 2.4),
                         ("category", "Section", 2), ("rack", "Rack", 1.2),
                         ("copies", "On shelf", 1.6), ("price", "Price", 1.4)], height=400)
    table.pack(fill="both", expand=True)

    def edit(row):
        book_form(shell, load, existing=db.book(row["id"]))

    def remove(row):
        def go():
            ok, message = db.delete_book(row["id"])
            popup(shell, "Delete book", message, kind="ok" if ok else "error")
            if ok:
                load()
        confirm(shell, "Remove from catalogue",
                "Delete '%s' and all its records? This cannot be undone." % row["title"], go)

    table.actions = [("Edit", edit, "teal"), ("Delete", remove, "danger")]

    def load():
        found = db.list_books(search.get(), section.get())
        counter.configure(text="%d title(s)  ·  %d copies in total"
                          % (len(found), sum(b["total"] for b in found)))
        rows = []
        for b in found:
            if b["available"] == 0:
                copies = ("None free", "bad")
            elif b["available"] < b["total"]:
                copies = ("%d of %d" % (b["available"], b["total"]), "warn")
            else:
                copies = ("%d of %d" % (b["available"], b["total"]), "ok")
            rows.append({"id": b["id"], "title": b["title"], "author": b["author"],
                         "isbn": b["isbn"] or "-", "category": b["category"],
                         "rack": b["rack"] or "-", "copies": copies,
                         "price": "Rs %d" % b["price"] if b["price"] else "-"})
        table.load(rows)

    search.bind("<KeyRelease>", lambda e: load())
    section.configure(command=lambda _: load())
    load()


# --------------------------------------------------------------------------
# members
# --------------------------------------------------------------------------

def members(shell, parent):
    body = shell.body(scroll=False)
    pending = db.stats()["pending"]
    subtitle = "Approve new registrations, block defaulters and reset passwords"
    if pending:
        subtitle = "%d account(s) waiting for approval.  " % pending + subtitle
    page_title(body, "Members", subtitle).pack(fill="x")

    bar = card(body)
    bar.pack(fill="x", pady=(14, 0))
    row = ctk.CTkFrame(bar, fg_color="transparent")
    row.pack(fill="x", padx=16, pady=14)
    role = ctk.CTkOptionMenu(row, values=["All", "Student", "Faculty", "Librarian"], height=38,
                             corner_radius=10, width=150, fg_color=T.c("surface2"),
                             button_color=T.c("accent"), button_hover_color=T.c("accent"),
                             text_color=T.c("text"), dropdown_fg_color=T.c("surface"),
                             dropdown_text_color=T.c("text"), font=T.font(12))
    role.pack(side="left")
    status = ctk.CTkOptionMenu(row, values=["All", "Active", "Pending", "Blocked"], height=38,
                               corner_radius=10, width=150, fg_color=T.c("surface2"),
                               button_color=T.c("accent"), button_hover_color=T.c("accent"),
                               text_color=T.c("text"), dropdown_fg_color=T.c("surface"),
                               dropdown_text_color=T.c("text"), font=T.font(12))
    status.pack(side="left", padx=(10, 0))
    counter = ctk.CTkLabel(row, text="", font=T.font(12), text_color=T.c("muted"))
    counter.pack(side="left", padx=16)

    table = Table(body, [("code", "User ID", 2), ("name", "Name", 3), ("role", "Role", 1.6),
                         ("department", "Department", 3.4), ("phone", "Phone", 1.8),
                         ("held", "Books", 1.2), ("dues", "Fines", 1.4), ("status", "Status", 1.6)],
                  height=430)
    table.pack(fill="both", expand=True, pady=(14, 0))

    def approve(row):
        if row["raw"]["status"] != "pending":
            popup(shell, "Already handled", "%s is already %s." % (row["name"], row["raw"]["status"]), kind="info")
            return
        db.set_status(row["raw"]["id"], "active")
        popup(shell, "Approved", "%s can now log in and borrow books." % row["name"], kind="ok")
        load()

    def toggle_block(row):
        person = row["raw"]
        if person["role"] == "librarian":
            popup(shell, "Not allowed", "Librarian accounts cannot be blocked.", kind="warn")
            return
        new = "blocked" if person["status"] == "active" else "active"
        if person["status"] == "pending":
            popup(shell, "Still pending", "Approve or leave this registration as it is.", kind="info")
            return
        db.set_status(person["id"], new)
        popup(shell, "Account updated", "%s is now %s." % (person["name"], new), kind="ok" if new == "active" else "warn")
        load()

    def reset(row):
        def go(value):
            password = value or "library@123"
            db.reset_password(row["raw"]["id"], password)
            popup(shell, "Password reset", "New password for %s is:  %s" % (row["name"], password), kind="ok")
        ask_text(shell, "Reset password", "Type a new password for %s, or leave it blank for the default."
                 % row["name"], go, placeholder="library@123")

    table.actions = [("Approve", approve, "success"), ("Block", toggle_block, "gold"),
                     ("Reset", reset, "ghost")]
    table.action_filter = lambda row, label: not (label == "Approve" and row["raw"]["status"] != "pending")

    def load():
        people = db.list_users(_pick(role.get()), _pick(status.get()))
        dues = {r["code"]: r["due"] for r in db.unpaid_fines()}
        held = {}
        for loan in db.active_issues():
            held[loan["user_code"]] = held.get(loan["user_code"], 0) + 1
        rows = []
        for person in people:
            colour = {"active": "ok", "pending": "warn", "blocked": "bad"}[person["status"]]
            limit = db.POLICY[person["role"]]["limit"]
            rows.append({
                "raw": person, "code": person["code"], "name": person["name"],
                "role": person["role"].title(), "department": person["department"] or "-",
                "phone": person["phone"] or "-",
                "held": "%d / %d" % (held.get(person["code"], 0), limit) if limit else "-",
                "dues": ("Rs %d" % dues[person["code"]], "bad") if person["code"] in dues else "-",
                "status": (person["status"].title(), colour),
            })
        counter.configure(text="%d member(s)" % len(rows))
        table.load(rows)

    role.configure(command=lambda _: load())
    status.configure(command=lambda _: load())
    load()


# --------------------------------------------------------------------------
# overdue, reservations, requests, notices
# --------------------------------------------------------------------------

def overdue(shell, parent):
    body = shell.body(scroll=False)
    late = db.overdue()
    page_title(body, "Overdue books",
               "%d book(s) are past their due date, Rs %d in fines so far"
               % (len(late), sum(db.fine_for(r) for r in late))).pack(fill="x")

    table = Table(body, [("who", "Member", 3), ("contact", "Contact", 2.4), ("title", "Book", 4),
                         ("due", "Due on", 1.8), ("late", "Days late", 1.4), ("fine", "Fine", 1.4)],
                  height=470, empty_text="Nothing is overdue. Well done.")
    table.pack(fill="both", expand=True, pady=(14, 0))

    def send_back(row):
        ok, message, _fine = db.return_book(row["id"])
        popup(shell, "Return book", message, kind="ok" if ok else "error")
        shell.refresh()

    def settled(row):
        db.mark_fine_paid(row["id"])
        popup(shell, "Fine settled", "Rs %d recorded as paid." % row["amount"], kind="ok")
        shell.refresh()

    table.actions = [("Return now", send_back, "primary")]
    rows = []
    for loan in late:
        fine = db.fine_for(loan)
        rows.append({
            "id": loan["id"], "amount": fine,
            "who": "%s (%s)" % (loan["user_name"], loan["user_code"]),
            "contact": loan["phone"] or "-", "title": loan["title"],
            "due": db.pretty_date(loan["due_on"]),
            "late": ("%d" % -db.days_left(loan), "bad"),
            "fine": ("Rs %d" % fine, "bad") if fine else "-",
        })
    if rows and any(r["amount"] for r in rows):
        table.actions.append(("Fine paid", settled, "gold"))
    table.load(rows)


def queue(shell, parent):
    body = shell.body(scroll=False)
    page_title(body, "Reservation queue",
               "Copies coming back are held for the next person in line").pack(fill="x")

    row = ctk.CTkFrame(body, fg_color="transparent")
    row.pack(fill="x", pady=(14, 10))
    status = ctk.CTkOptionMenu(row, values=["All", "Waiting", "Ready", "Cancelled"], height=38,
                               corner_radius=10, width=160, fg_color=T.c("surface2"),
                               button_color=T.c("accent"), button_hover_color=T.c("accent"),
                               text_color=T.c("text"), dropdown_fg_color=T.c("surface"),
                               dropdown_text_color=T.c("text"), font=T.font(12))
    status.pack(side="left")

    table = Table(body, [("who", "Member", 3), ("title", "Book", 4), ("section", "Section", 2.4),
                         ("when", "Reserved on", 2), ("status", "Status", 1.8)], height=430,
                  empty_text="The queue is empty")
    table.pack(fill="both", expand=True)

    def cancel(row):
        def go():
            db.cancel_reservation(row["id"])
            popup(shell, "Cancelled", "Reservation removed from the queue.", kind="info")
            load()
        confirm(shell, "Cancel reservation", "Remove %s from the queue for '%s'?" % (row["who"], row["title"]), go)

    table.actions = [("Cancel", cancel, "danger")]
    table.action_filter = lambda r, label: r["raw"]["status"] in ("waiting", "ready")

    def load():
        items = db.all_reservations(_pick(status.get()))
        rows = []
        for item in items:
            colour = {"waiting": "warn", "ready": "ok", "cancelled": "muted",
                      "collected": "muted"}.get(item["status"], "muted")
            rows.append({"raw": item, "id": item["id"],
                         "who": "%s (%s)" % (item["user_name"], item["user_code"]),
                         "title": item["title"], "section": item["category"],
                         "when": db.pretty_date(item["reserved_on"]),
                         "status": (item["status"].title(), colour)})
        table.load(rows)

    status.configure(command=lambda _: load())
    load()


def requests(shell, parent):
    body = shell.body(scroll=False)
    page_title(body, "Purchase requests", "Titles faculty have asked the library to buy").pack(fill="x")

    row = ctk.CTkFrame(body, fg_color="transparent")
    row.pack(fill="x", pady=(14, 10))
    status = ctk.CTkOptionMenu(row, values=["All", "Pending", "Approved", "Rejected"], height=38,
                               corner_radius=10, width=160, fg_color=T.c("surface2"),
                               button_color=T.c("accent"), button_hover_color=T.c("accent"),
                               text_color=T.c("text"), dropdown_fg_color=T.c("surface"),
                               dropdown_text_color=T.c("text"), font=T.font(12))
    status.pack(side="left")

    table = Table(body, [("who", "Requested by", 2.6), ("title", "Book", 3.4), ("author", "Author", 2.4),
                         ("reason", "Reason", 4), ("when", "Sent", 1.8), ("status", "Status", 1.6)],
                  height=430, empty_text="No requests")
    table.pack(fill="both", expand=True)

    def decide(row, verdict):
        def go(remark):
            db.set_request_status(row["id"], verdict, remark)
            popup(shell, "Request %s" % verdict, "'%s' marked as %s." % (row["title"], verdict), kind="ok")
            load()
        ask_text(shell, "%s request" % verdict.title(),
                 "Add a short note for %s (optional)." % row["who"], go, placeholder="Ordered, expected next week")

    table.actions = [("Approve", lambda r: decide(r, "approved"), "success"),
                     ("Reject", lambda r: decide(r, "rejected"), "danger")]
    table.action_filter = lambda r, label: r["raw"]["status"] == "pending"

    def load():
        items = db.all_requests(_pick(status.get()))
        rows = []
        for item in items:
            colour = {"pending": "warn", "approved": "ok", "rejected": "bad"}.get(item["status"], "muted")
            rows.append({"raw": item, "id": item["id"],
                         "who": "%s (%s)" % (item["user_name"], item["user_code"]),
                         "title": item["title"], "author": item["author"] or "-",
                         "reason": item["reason"] or "-", "when": db.pretty_date(item["requested_on"]),
                         "status": (item["status"].title(), colour)})
        table.load(rows)

    status.configure(command=lambda _: load())
    load()


def notices(shell, parent):
    body = shell.body()
    page_title(body, "Notices", "Announcements shown to every student and faculty member").pack(fill="x")

    form = card(body)
    form.pack(fill="x", pady=(16, 0))
    pad = ctk.CTkFrame(form, fg_color="transparent")
    pad.pack(fill="x", padx=22, pady=20)
    ctk.CTkLabel(pad, text="Post a notice", font=T.font(15, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x")
    title = FormField(pad, "Title", placeholder="Library timings during exams", width=760)
    title.pack(fill="x", pady=(12, 10))
    text = TextareaForm(pad, "Message", width=760, height=100)
    text.pack(fill="x")

    def post():
        ok, message = db.add_notice(title.get(), text.get(), shell.user["name"])
        popup(shell, "Notice", message, kind="ok" if ok else "warn")
        if ok:
            title.clear()
            text.clear()
            load()

    button(pad, "Publish notice", post, kind="primary", height=40, width=170).pack(anchor="e", pady=(14, 0))

    ctk.CTkLabel(body, text="Published", font=T.font(15, "bold"), text_color=T.c("text"),
                 anchor="w").pack(fill="x", pady=(22, 8))
    table = Table(body, [("title", "Title", 5), ("body", "Message", 7),
                         ("when", "Posted on", 2), ("who", "By", 2)], height=250,
                  empty_text="Nothing published yet")
    table.pack(fill="both", expand=True)

    def remove(row):
        def go():
            db.delete_notice(row["id"])
            load()
        confirm(shell, "Delete notice", "Remove '%s'?" % row["title"], go)

    table.actions = [("Delete", remove, "danger")]

    def load():
        table.load([{"id": n["id"], "title": n["title"], "body": n["body"][:90] + ("..." if len(n["body"]) > 90 else ""),
                     "when": db.pretty_date(n["posted_on"]), "who": n["posted_by"] or "-"}
                    for n in db.notices()])

    load()


# --------------------------------------------------------------------------
# reports
# --------------------------------------------------------------------------

def reports_page(shell, parent):
    body = shell.body()
    page_title(body, "Reports", "Download records as an Excel workbook or CSV files").pack(fill="x")

    n = db.stats()
    strip = ctk.CTkFrame(body, fg_color="transparent")
    strip.pack(fill="x", pady=(16, 0))
    for i in range(4):
        strip.grid_columnconfigure(i, weight=1, uniform="r")
    for i, (label, value, kind) in enumerate([
        ("Transactions logged", len(db.transactions()), "accent"),
        ("Books out now", n["out"], "gold"),
        ("Fine collected", "Rs %d" % n["fine_collected"], "ok"),
        ("Fine pending", "Rs %d" % n["fine_pending"], "bad"),
    ]):
        StatCard(strip, label, value, kind=kind).grid(row=0, column=i, sticky="nsew",
                                                     padx=(0, 0) if i == 3 else (0, 14))

    exports = card(body)
    exports.pack(fill="x", pady=(16, 0))
    epad = ctk.CTkFrame(exports, fg_color="transparent")
    epad.pack(fill="x", padx=22, pady=20)
    ctk.CTkLabel(epad, text="Downloads", font=T.font(15, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x")
    ctk.CTkLabel(epad, text="The full workbook has six sheets: summary, transactions, overdue, books, members and fines.",
                 font=T.font(11), text_color=T.c("muted"), anchor="w").pack(fill="x", pady=(2, 14))

    grid = ctk.CTkFrame(epad, fg_color="transparent")
    grid.pack(fill="x")
    options = [
        ("Full library report (xlsx)", "xlsx", lambda p: reports.export_workbook(p)),
        ("Transactions (csv)", "csv", lambda p: reports.export_csv(p, reports.TRANSACTION_HEADERS,
                                                                   reports.transaction_rows(db.transactions()))),
        ("Catalogue (csv)", "csv", lambda p: reports.export_csv(
            p, ["ID", "ISBN", "Title", "Author", "Publisher", "Year", "Section", "Rack", "Price", "Copies", "On shelf"],
            [[b["id"], b["isbn"], b["title"], b["author"], b["publisher"], b["year"], b["category"],
              b["rack"], b["price"], b["total"], b["available"]] for b in db.list_books()])),
        ("Members (csv)", "csv", lambda p: reports.export_csv(
            p, ["User ID", "Name", "Role", "Department", "Email", "Phone", "Status", "Joined"],
            [[u["code"], u["name"], u["role"], u["department"], u["email"], u["phone"], u["status"],
              u["created_on"]] for u in db.list_users()])),
        ("Unpaid fines (csv)", "csv", lambda p: reports.export_csv(
            p, ["User ID", "Name", "Role", "Phone", "Pending fine"],
            [[f["code"], f["name"], f["role"], f["phone"], f["due"]] for f in db.unpaid_fines()])),
    ]
    for i, (label, ext, producer) in enumerate(options):
        holder = ctk.CTkFrame(grid, fg_color="transparent")
        holder.grid(row=i // 2, column=i % 2, sticky="w", pady=5, padx=(0, 20))
        button(holder, label, lambda e=ext, f=producer: download(shell, e, f),
               kind="primary" if ext == "xlsx" else "ghost", height=38, width=300).pack(side="left")

    ctk.CTkLabel(body, text="Recent transactions", font=T.font(15, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x", pady=(24, 8))
    table = Table(body, [("who", "Member", 3), ("title", "Book", 4), ("issued", "Issued", 2),
                         ("due", "Due", 2), ("back", "Returned", 2), ("state", "Status", 2),
                         ("fine", "Fine", 1.4)], height=280, empty_text="No transactions yet")
    table.pack(fill="both", expand=True)
    rows = []
    for loan in db.transactions()[:40]:
        if loan["returned_on"]:
            state, colour = "Returned", "muted"
        elif db.days_left(loan) < 0:
            state, colour = "Overdue", "bad"
        else:
            state, colour = "On loan", "ok"
        fine = loan["fine"] if loan["returned_on"] else db.fine_for(loan)
        rows.append({"who": "%s (%s)" % (loan["user_name"], loan["user_code"]), "title": loan["title"],
                     "issued": db.pretty_date(loan["issued_on"]), "due": db.pretty_date(loan["due_on"]),
                     "back": db.pretty_date(loan["returned_on"]), "state": (state, colour),
                     "fine": ("Rs %d" % fine, "bad") if fine else "-"})
    table.load(rows)


def download(shell, ext, producer):
    default = "library_report_%s.%s" % (date.today().strftime("%Y_%m_%d"), ext)
    path = filedialog.asksaveasfilename(
        parent=shell, title="Save report", defaultextension="." + ext, initialfile=default,
        filetypes=[("Excel workbook", "*.xlsx"), ("CSV file", "*.csv"), ("All files", "*.*")],
    )
    if not path:
        return
    try:
        producer(path)
    except PermissionError:
        popup(shell, "Could not save", "That file is open in another program. Close it and try again.", kind="error")
        return
    except Exception as error:      # noqa: BLE001 - the desk just needs to know it failed
        popup(shell, "Export failed", str(error), kind="error")
        return
    popup(shell, "Saved", "Report written to:\n%s" % path, kind="ok")


# --------------------------------------------------------------------------
# portal
# --------------------------------------------------------------------------

class LibrarianPortal(PortalShell):
    def __init__(self, app, user):
        super().__init__(app, user, [
            ("dashboard", "Dashboard", dashboard),
            ("desk", "Issue / Return", desk),
            ("books", "Catalogue", books),
            ("members", "Members", members),
            ("overdue", "Overdue", overdue),
            ("queue", "Reservations", queue),
            ("requests", "Purchase requests", requests),
            ("notices", "Notices", notices),
            ("reports", "Reports", reports_page),
            ("about", "Help and rules", about),
        ])
