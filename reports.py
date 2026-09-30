"""Report exports. Everything the librarian can download lives here."""

import csv
from datetime import date

import database as db

HEAD_FILL = "1B3A5C"


def _style_sheet(ws, headers, rows, widths=None):
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    fill = PatternFill("solid", fgColor=HEAD_FILL)
    thin = Side(style="thin", color="D7DEE8")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for i, title in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=i, value=title)
        cell.font = Font(bold=True, color="FFFFFF", size=11)
        cell.fill = fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border

    for r, row in enumerate(rows, start=2):
        for c, value in enumerate(row, start=1):
            cell = ws.cell(row=r, column=c, value=value)
            cell.border = border
            cell.alignment = Alignment(vertical="center", wrap_text=False)

    ws.row_dimensions[1].height = 24
    ws.freeze_panes = "A2"
    for i, title in enumerate(headers, start=1):
        if widths and i - 1 < len(widths):
            span = widths[i - 1]
        else:
            longest = max([len(str(title))] + [len(str(r[i - 1])) for r in rows if len(r) >= i] or [10])
            span = min(max(longest + 3, 11), 46)
        ws.column_dimensions[get_column_letter(i)].width = span


def transaction_rows(loans):
    out = []
    for loan in loans:
        if loan["returned_on"]:
            state = "Returned"
        elif db.days_left(loan) < 0:
            state = "Overdue"
        else:
            state = "On loan"
        fine = loan["fine"] if loan["returned_on"] else db.fine_for(loan)
        out.append([
            loan["id"], loan["user_code"], loan["user_name"], loan["user_role"].title(),
            loan["title"], loan["author"], db.pretty_date(loan["issued_on"]),
            db.pretty_date(loan["due_on"]), db.pretty_date(loan["returned_on"]),
            state, fine, "Paid" if loan["fine_paid"] else ("Unpaid" if fine else "-"),
        ])
    return out


TRANSACTION_HEADERS = ["Issue #", "User ID", "Name", "Role", "Book", "Author",
                       "Issued", "Due", "Returned", "Status", "Fine (Rs)", "Fine status"]


def export_workbook(path):
    """One xlsx with every report the library needs"""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    numbers = db.stats()
    wb = Workbook()

    ws = wb.active
    ws.title = "Summary"
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 22
    banner = ws.cell(row=1, column=1, value="VIT BHOPAL - CENTRAL LIBRARY")
    banner.font = Font(bold=True, size=15, color="FFFFFF")
    banner.fill = PatternFill("solid", fgColor=HEAD_FILL)
    banner.alignment = Alignment(vertical="center")
    ws.merge_cells("A1:B1")
    ws.row_dimensions[1].height = 30
    ws.cell(row=2, column=1, value="Generated on").font = Font(bold=True)
    ws.cell(row=2, column=2, value=date.today().strftime("%d %B %Y"))

    summary = [
        ("Titles in catalogue", numbers["titles"]),
        ("Total copies", numbers["copies"]),
        ("Copies on shelf", numbers["shelf"]),
        ("Books currently issued", numbers["out"]),
        ("Overdue books", numbers["overdue"]),
        ("Registered members", numbers["total"]),
        ("Students", numbers["students"]),
        ("Faculty", numbers["faculty"]),
        ("Accounts awaiting approval", numbers["pending"]),
        ("Reservations in queue", numbers["reservations"]),
        ("Fine collected (Rs)", numbers["fine_collected"]),
        ("Fine pending (Rs)", numbers["fine_pending"]),
    ]
    for i, (label, value) in enumerate(summary, start=4):
        ws.cell(row=i, column=1, value=label).font = Font(bold=True)
        ws.cell(row=i, column=2, value=value)

    ws = wb.create_sheet("Transactions")
    _style_sheet(ws, TRANSACTION_HEADERS, transaction_rows(db.transactions()))

    ws = wb.create_sheet("Overdue")
    late = []
    for loan in db.overdue():
        late.append([loan["user_code"], loan["user_name"], loan["phone"] or "-", loan["title"],
                     db.pretty_date(loan["due_on"]), -db.days_left(loan), db.fine_for(loan)])
    _style_sheet(ws, ["User ID", "Name", "Phone", "Book", "Due on", "Days late", "Fine (Rs)"], late)

    ws = wb.create_sheet("Books")
    books = [[b["id"], b["isbn"], b["title"], b["author"], b["publisher"], b["year"],
              b["category"], b["rack"], b["price"], b["total"], b["available"]]
             for b in db.list_books()]
    _style_sheet(ws, ["Book #", "ISBN", "Title", "Author", "Publisher", "Year", "Section",
                      "Rack", "Price (Rs)", "Copies", "On shelf"], books)

    ws = wb.create_sheet("Members")
    people = [[u["code"], u["name"], u["role"].title(), u["department"], u["email"],
               u["phone"], u["status"].title(), db.pretty_date(u["created_on"])]
              for u in db.list_users()]
    _style_sheet(ws, ["User ID", "Name", "Role", "Department", "Email", "Phone",
                      "Status", "Joined"], people)

    ws = wb.create_sheet("Fines")
    dues = [[f["code"], f["name"], f["role"].title(), f["phone"] or "-", f["due"]]
            for f in db.unpaid_fines()]
    _style_sheet(ws, ["User ID", "Name", "Role", "Phone", "Pending fine (Rs)"], dues)

    wb.save(path)
    return path


def export_csv(path, headers, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)
    return path
