"""
Everything that touches SQLite lives here: schema, seed data and the library
rules (borrow limits, loan periods, fines, renewals, reservations).

Dates are stored as plain ISO strings so they are easy to read in the db file.
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "library.db"

# borrowing rules per role
POLICY = {
    "student": {"limit": 2, "days": 14, "label": "Student"},
    "faculty": {"limit": 5, "days": 60, "label": "Faculty"},
    "librarian": {"limit": 0, "days": 0, "label": "Librarian"},
}

FINE_PER_DAY = 2          # rupees charged for every day past the due date
FINE_BLOCK_LIMIT = 50     # unpaid fines above this block new issues
MAX_RENEWALS = 1

SCHEMA = """
create table if not exists users (
    id          integer primary key autoincrement,
    code        text unique not null,
    name        text not null,
    password    text not null,
    role        text not null check (role in ('student', 'faculty', 'librarian')),
    email       text default '',
    phone       text default '',
    department  text default '',
    status      text default 'active' check (status in ('active', 'pending', 'blocked')),
    created_on  text
);

create table if not exists books (
    id          integer primary key autoincrement,
    isbn        text default '',
    title       text not null,
    author      text not null,
    publisher   text default '',
    year        integer default 0,
    category    text default 'General',
    rack        text default '',
    price       real default 0,
    total       integer default 1,
    available   integer default 1
);

create table if not exists issues (
    id          integer primary key autoincrement,
    user_id     integer references users(id),
    book_id     integer references books(id),
    issued_on   text,
    due_on      text,
    returned_on text,
    fine        real default 0,
    fine_paid   integer default 0,
    renewals    integer default 0,
    issued_by   text default ''
);

create table if not exists reservations (
    id          integer primary key autoincrement,
    user_id     integer references users(id),
    book_id     integer references books(id),
    reserved_on text,
    status      text default 'waiting'
);

create table if not exists notices (
    id        integer primary key autoincrement,
    title     text,
    body      text,
    posted_on text,
    posted_by text
);

create table if not exists requests (
    id           integer primary key autoincrement,
    user_id      integer references users(id),
    title        text,
    author       text,
    reason       text,
    requested_on text,
    status       text default 'pending',
    remark       text default ''
);
"""

# connection helpers

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma foreign_keys = on")
    return conn


def query(sql, params=()):
    conn = connect()
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    conn = connect()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def today():
    return date.today().isoformat()


def init_db():
    conn = connect()
    conn.executescript(SCHEMA)
    conn.commit()
    empty = conn.execute("select count(*) from users").fetchone()[0] == 0
    conn.close()
    if empty:
        seed()



# date / fine helpers


def fine_for(issue, on=None):
    """Fine for an issue, counted up to the return date or to today."""
    due = date.fromisoformat(issue["due_on"])
    end = date.fromisoformat(issue["returned_on"]) if issue.get("returned_on") else (on or date.today())
    late = (end - due).days
    return late * FINE_PER_DAY if late > 0 else 0


def days_left(issue):
    """Negative means it is already overdue."""
    due = date.fromisoformat(issue["due_on"])
    end = date.fromisoformat(issue["returned_on"]) if issue.get("returned_on") else date.today()
    return (due - end).days


def pretty_date(value):
    if not value:
        return "-"
    return date.fromisoformat(value).strftime("%d %b %Y")



# users


def login(code, password, role):
    row = one("select * from users where code = ? and role = ?", (code.strip().upper(), role))
    if not row:
        return None, "No %s account found with that ID" % POLICY[role]["label"].lower()
    if row["password"] != password:
        return None, "Incorrect password, please try again"
    if row["status"] == "pending":
        return None, "Your account is still waiting for librarian approval"
    if row["status"] == "blocked":
        return None, "This account has been blocked. Please contact the library desk"
    return row, None


def register(code, name, password, role, email, phone, department):
    code = code.strip().upper()
    if not code or not name or not password:
        return False, "ID, name and password are all required"
    if len(password) < 4:
        return False, "Password should be at least 4 characters"
    if role == "student" and not (code[:2].isdigit() and len(code) >= 8):
        return False, "Registration number should look like 22BEC10145"
    if one("select id from users where code = ?", (code,)):
        return False, "That ID is already registered"
    execute(
        "insert into users (code, name, password, role, email, phone, department, status, created_on) "
        "values (?,?,?,?,?,?,?,?,?)",
        (code, name.strip(), password, role, email.strip(), phone.strip(), department.strip(),
         "pending", today()),
    )
    return True, "Registered. Your account will be active once the librarian approves it"


def user_by_code(code):
    return one("select * from users where code = ?", ((code or "").strip().upper(),))


def user(pk):
    return one("select * from users where id = ?", (pk,))


def list_users(role=None, status=None):
    sql = "select * from users where 1 = 1"
    params = []
    if role and role != "All":
        sql += " and role = ?"
        params.append(role)
    if status and status != "All":
        sql += " and status = ?"
        params.append(status)
    return query(sql + " order by role, name", params)


def set_status(pk, status):
    execute("update users set status = ? where id = ?", (status, pk))


def save_profile(pk, email, phone):
    execute("update users set email = ?, phone = ? where id = ?", (email.strip(), phone.strip(), pk))


def change_password(pk, old, new):
    row = user(pk)
    if not row or row["password"] != old:
        return False, "Current password does not match"
    if len(new) < 4:
        return False, "New password should be at least 4 characters"
    execute("update users set password = ? where id = ?", (new, pk))
    return True, "Password updated"


def reset_password(pk, new="library@123"):
    execute("update users set password = ? where id = ?", (new, pk))
    return new


def unpaid_fines(pk=None):
    sql = ("select u.code, u.name, u.role, u.phone, sum(i.fine) as due "
           "from issues i join users u on u.id = i.user_id "
           "where i.fine > 0 and i.fine_paid = 0 ")
    params = []
    if pk:
        sql += "and i.user_id = ? "
        params.append(pk)
    return query(sql + "group by u.id order by due desc", params)



# books


def list_books(search="", category="All", only_available=False):
    sql = "select * from books where 1 = 1"
    params = []
    if search:
        sql += " and (title like ? or author like ? or isbn like ? or publisher like ?)"
        like = "%" + search.strip() + "%"
        params += [like, like, like, like]
    if category and category != "All":
        sql += " and category = ?"
        params.append(category)
    if only_available:
        sql += " and available > 0"
    return query(sql + " order by title", params)


def book(pk):
    return one("select * from books where id = ?", (pk,))


def categories():
    rows = query("select distinct category from books order by category")
    return ["All"] + [r["category"] for r in rows]


def add_book(data):
    if not data.get("title") or not data.get("author"):
        return False, "Title and author cannot be empty"
    try:
        total = int(data.get("total") or 1)
    except ValueError:
        return False, "Number of copies should be a whole number"
    if total < 1:
        return False, "There should be at least one copy"
    execute(
        "insert into books (isbn, title, author, publisher, year, category, rack, price, total, available) "
        "values (?,?,?,?,?,?,?,?,?,?)",
        (data.get("isbn", ""), data["title"].strip(), data["author"].strip(),
         data.get("publisher", ""), int(data.get("year") or 0),
         data.get("category", "General"), data.get("rack", ""),
         float(data.get("price") or 0), total, total),
    )
    return True, "Book added to the catalogue"


def update_book(pk, data):
    old = book(pk)
    if not old:
        return False, "That book no longer exists"
    try:
        total = int(data.get("total") or old["total"])
    except ValueError:
        return False, "Number of copies should be a whole number"
    on_loan = old["total"] - old["available"]
    if total < on_loan:
        return False, "%d copies are out on loan, cannot go below that" % on_loan
    available = total - on_loan
    execute(
        "update books set isbn=?, title=?, author=?, publisher=?, year=?, category=?, rack=?, price=?, "
        "total=?, available=? where id=?",
        (data.get("isbn", old["isbn"]), data.get("title", old["title"]).strip(),
         data.get("author", old["author"]).strip(), data.get("publisher", old["publisher"]),
         int(data.get("year") or 0), data.get("category", old["category"]),
         data.get("rack", old["rack"]), float(data.get("price") or 0),
         total, available, pk),
    )
    return True, "Book details updated"


def delete_book(pk):
    row = book(pk)
    if not row:
        return False, "That book no longer exists"
    if query("select id from issues where book_id = ? and returned_on is null", (pk,)):
        return False, "Some copies are still issued, return them first"
    execute("delete from reservations where book_id = ?", (pk,))
    execute("delete from issues where book_id = ?", (pk,))
    execute("delete from books where id = ?", (pk,))
    return True, "Book removed from the catalogue"



# circulation


ISSUE_JOIN = ("select i.*, u.code as user_code, u.name as user_name, u.role as user_role, u.phone, "
              "b.title, b.author, b.category, b.rack "
              "from issues i join users u on u.id = i.user_id join books b on b.id = i.book_id ")


def active_issues(pk=None):
    sql = ISSUE_JOIN + "where i.returned_on is null "
    params = []
    if pk:
        sql += "and i.user_id = ? "
        params.append(pk)
    return query(sql + "order by i.due_on", params)


def history(pk=None, limit=None):
    sql = ISSUE_JOIN + "where i.returned_on is not null "
    params = []
    if pk:
        sql += "and i.user_id = ? "
        params.append(pk)
    sql += "order by i.returned_on desc"
    if limit:
        sql += " limit %d" % int(limit)
    return query(sql, params)


def issue_row(pk):
    return one(ISSUE_JOIN + "where i.id = ?", (pk,))


def overdue():
    rows = active_issues()
    return [r for r in rows if days_left(r) < 0]


def can_issue(person):
    """Returns (allowed, reason). Used by the issue desk before anything is written."""
    if not person:
        return False, "No user found with that ID"
    if person["status"] != "active":
        return False, "This account is %s" % person["status"]
    if person["role"] == "librarian":
        return False, "Librarian accounts do not borrow books"

    policy = POLICY[person["role"]]
    held = len(active_issues(person["id"]))
    if held >= policy["limit"]:
        return False, "%s already has %d of %d allowed books" % (person["name"], held, policy["limit"])

    dues = one("select coalesce(sum(fine), 0) as due from issues where user_id = ? and fine > 0 and fine_paid = 0",
               (person["id"],))
    if dues["due"] >= FINE_BLOCK_LIMIT:
        return False, "Unpaid fine of Rs %d blocks new issues" % dues["due"]
    return True, ""


def issue_book(code, book_pk, librarian=""):
    person = user_by_code(code)
    allowed, reason = can_issue(person)
    if not allowed:
        return False, reason

    row = book(book_pk)
    if not row:
        return False, "No book found with that ID"
    if row["available"] <= 0:
        return False, "Every copy of '%s' is on loan" % row["title"]

    if one("select id from issues where user_id = ? and book_id = ? and returned_on is null",
           (person["id"], book_pk)):
        return False, "%s has already borrowed this title" % person["name"]

    due = date.today() + timedelta(days=POLICY[person["role"]]["days"])
    execute("insert into issues (user_id, book_id, issued_on, due_on, issued_by) values (?,?,?,?,?)",
            (person["id"], book_pk, today(), due.isoformat(), librarian))
    execute("update books set available = available - 1 where id = ?", (book_pk,))

    # whoever was waiting in the queue gets told their copy is ready
    waiting = one("select id from reservations where book_id = ? and status = 'waiting' "
                  "and user_id = ? order by id limit 1", (book_pk, person["id"]))
    if waiting:
        execute("update reservations set status = 'ready' where id = ?", (waiting["id"],))

    return True, "'%s' issued to %s until %s" % (row["title"], person["name"], pretty_date(due.isoformat()))


def return_book(issue_pk):
    row = issue_row(issue_pk)
    if not row:
        return False, "That issue record does not exist", 0
    if row["returned_on"]:
        return False, "This book was already returned on %s" % pretty_date(row["returned_on"]), 0

    fine = fine_for(row)
    execute("update issues set returned_on = ?, fine = ? where id = ?", (today(), fine, issue_pk))
    execute("update books set available = min(available + 1, total) where id = ?", (row["book_id"],))

    # next person in the reservation queue now has a copy waiting
    nxt = one("select id from reservations where book_id = ? and status = 'waiting' order by id limit 1",
              (row["book_id"],))
    if nxt:
        execute("update reservations set status = 'ready' where id = ?", (nxt["id"],))
        return True, "'%s' returned. A copy is now held for the next requester. Fine: Rs %d" % (row["title"], fine), fine

    if fine:
        return True, "'%s' returned %d days late. Fine payable: Rs %d" % (row["title"], -days_left(row), fine), fine
    return True, "'%s' returned on time. No fine" % row["title"], 0


def mark_fine_paid(issue_pk):
    execute("update issues set fine_paid = 1 where id = ?", (issue_pk,))


def renew(issue_pk):
    row = issue_row(issue_pk)
    if not row:
        return False, "That issue record does not exist"
    if row["returned_on"]:
        return False, "This book has already been returned"
    if row["renewals"] >= MAX_RENEWALS:
        return False, "This issue has already been renewed once"
    if days_left(row) < 0:
        return False, "Overdue books cannot be renewed. Return it and pay the fine first"
    if one("select id from reservations where book_id = ? and status = 'waiting'", (row["book_id"],)):
        return False, "Someone else is waiting for this title"

    new_due = date.today() + timedelta(days=POLICY[row["user_role"]]["days"])
    execute("update issues set due_on = ?, renewals = renewals + 1 where id = ?",
            (new_due.isoformat(), issue_pk))
    return True, "Renewed until %s" % pretty_date(new_due.isoformat())


# reservations


def reserve(person_pk, book_pk):
    row = book(book_pk)
    if not row:
        return False, "That book does not exist"
    if one("select id from reservations where user_id = ? and book_id = ? and status in ('waiting','ready')",
           (person_pk, book_pk)):
        return False, "You are already in the queue for this title"
    execute("insert into reservations (user_id, book_id, reserved_on, status) values (?,?,?,?)",
            (person_pk, book_pk, today(), "waiting"))
    return True, "Added to the queue for '%s'. We will hold a copy when it comes back" % row["title"]


def my_reservations(pk):
    return query("select r.*, b.title, b.author, b.category from reservations r "
                 "join books b on b.id = r.book_id where r.user_id = ? order by r.id desc", (pk,))


def all_reservations(status=None):
    sql = ("select r.*, b.title, b.author, b.category, u.name as user_name, u.code as user_code "
           "from reservations r join books b on b.id = r.book_id "
           "join users u on u.id = r.user_id ")
    params = []
    if status and status != "All":
        sql += "where r.status = ? "
        params.append(status)
    return query(sql + "order by r.status, r.id", params)


def cancel_reservation(pk):
    execute("update reservations set status = 'cancelled' where id = ?", (pk,))

# notices and purchase requests


def notices():
    return query("select * from notices order by posted_on desc, id desc")


def add_notice(title, body, author):
    if not title.strip():
        return False, "Notice needs a title"
    execute("insert into notices (title, body, posted_on, posted_by) values (?,?,?,?)",
            (title.strip(), body.strip(), today(), author))
    return True, "Notice published"


def delete_notice(pk):
    execute("delete from notices where id = ?", (pk,))


def my_requests(pk):
    return query("select * from requests where user_id = ? order by id desc", (pk,))


def all_requests(status=None):
    sql = ("select r.*, u.name as user_name, u.code as user_code, u.role as user_role "
           "from requests r join users u on u.id = r.user_id ")
    params = []
    if status and status != "All":
        sql += "where r.status = ? "
        params.append(status)
    return query(sql + "order by r.status, r.id desc", params)


def add_request(pk, title, author, reason):
    if not title.strip():
        return False, "Please mention the book title"
    execute("insert into requests (user_id, title, author, reason, requested_on) values (?,?,?,?,?)",
            (pk, title.strip(), author.strip(), reason.strip(), today()))
    return True, "Request sent to the librarian"


def set_request_status(pk, status, remark=""):
    execute("update requests set status = ?, remark = ? where id = ?", (status, remark, pk))


# dashboard numbers


def stats():
    books = one("select count(*) as titles, coalesce(sum(total),0) as copies, "
                "coalesce(sum(available),0) as shelf from books")
    people = one("select count(*) as total, "
                 "sum(case when role='student' then 1 else 0 end) as students, "
                 "sum(case when role='faculty' then 1 else 0 end) as faculty, "
                 "sum(case when status='pending' then 1 else 0 end) as pending from users")
    loans = one("select count(*) as out from issues where returned_on is null")
    money = one("select coalesce(sum(case when fine_paid=1 then fine else 0 end),0) as fine_collected, "
                "coalesce(sum(case when fine_paid=0 then fine else 0 end),0) as fine_pending "
                "from issues where fine > 0")
    late = len(overdue())
    stats = dict(books)
    stats.update(people)
    stats.update(loans)
    stats.update(money)
    stats["overdue"] = late
    stats["reservations"] = one("select count(*) as n from reservations where status='waiting'")["n"]
    return stats


def issues_last_days(days=14):
    since = (date.today() - timedelta(days=days - 1)).isoformat()
    rows = query("select issued_on as d, count(*) as n from issues where issued_on >= ? "
                 "group by issued_on", (since,))
    counts = {r["d"]: r["n"] for r in rows}
    return [((date.today() - timedelta(days=i)).strftime("%d %b"),
             counts.get((date.today() - timedelta(days=i)).isoformat(), 0))
            for i in range(days - 1, -1, -1)]


def top_books(n=6):
    return query("select b.title, count(*) as times from issues i join books b on b.id = i.book_id "
                 "group by b.id order by times desc, b.title limit ?", (n,))


def category_split():
    return query("select b.category as name, count(*) as n from issues i "
                 "join books b on b.id = i.book_id group by b.category order by n desc")


def transactions(since=None):
    sql = ISSUE_JOIN
    params = []
    if since:
        sql += "where i.issued_on >= ? "
        params.append(since)
    return query(sql + "order by i.issued_on desc, i.id desc", params)

# demo data

SEED_BOOKS = [
    ("9780131103627", "The C Programming Language", "Kernighan & Ritchie", "Prentice Hall", 1988, "Computer Science", "A1-01", 650, 4),
    ("9780132350884", "Clean Code", "Robert C. Martin", "Prentice Hall", 2008, "Computer Science", "A1-04", 899, 3),
    ("9780262046305", "Introduction to Algorithms", "Cormen, Leiserson, Rivest", "MIT Press", 2022, "Computer Science", "A1-07", 1450, 5),
    ("9788120344846", "Operating System Concepts", "Galvin & Silberschatz", "Wiley India", 2018, "Computer Science", "A2-02", 780, 4),
    ("9789352607075", "Database System Concepts", "Korth, Sudarshan", "McGraw Hill", 2019, "Computer Science", "A2-05", 820, 3),
    ("9780134685915", "Computer Networks", "Andrew S. Tanenbaum", "Pearson", 2020, "Computer Science", "A2-08", 940, 3),
    ("9781491950227", "Python Crash Course", "Eric Matthes", "No Starch Press", 2019, "Computer Science", "A3-01", 720, 6),
    ("9789351474432", "Data Structures Using C", "Reema Thareja", "Oxford University Press", 2014, "Computer Science", "A3-04", 610, 4),
    ("9788131765456", "Digital Signal Processing", "Proakis & Manolakis", "Pearson India", 2015, "Electronics", "B1-02", 880, 3),
    ("9780070667594", "Microprocessors and Microcontrollers", "Ramesh Gaonkar", "McGraw Hill", 2017, "Electronics", "B1-05", 540, 3),
    ("9788125930075", "Electronic Devices and Circuit Theory", "Boylestad & Nashelsky", "Pearson", 2013, "Electronics", "B2-01", 760, 2),
    ("9780070680807", "Control Systems Engineering", "Nagrath & Gopal", "McGraw Hill", 2018, "Electronics", "B2-04", 690, 4),
    ("9789353160746", "Engineering Thermodynamics", "P.K. Nag", "McGraw Hill", 2018, "Mechanical", "C1-01", 720, 3),
    ("9780070634954", "Fluid Mechanics", "Frank M. White", "McGraw Hill", 2016, "Mechanical", "C1-04", 850, 3),
    ("9788126584345", "Theory of Machines", "S.S. Rattan", "McGraw Hill", 2019, "Mechanical", "C2-02", 640, 2),
    ("9780199470921", "Higher Engineering Mathematics", "B.S. Grewal", "Khanna Publishers", 2020, "Mathematics", "D1-01", 899, 8),
    ("9789332548374", "Linear Algebra and Its Applications", "David C. Lay", "Pearson", 2016, "Mathematics", "D1-05", 940, 3),
    ("9780134591902", "Thomas' Calculus", "Hass, Weir, Thomas", "Pearson", 2018, "Mathematics", "D2-01", 1120, 3),
    ("9788123921266", "Engineering Physics", "R.K. Gaur & S.L. Gupta", "CBS Publishers", 2019, "Physics", "E1-02", 560, 4),
    ("9781107180529", "Concepts of Physics Vol 1", "H.C. Verma", "Bharati Bhawan", 2018, "Physics", "E1-06", 480, 5),
    ("9780133918519", "Materials Science and Engineering", "William D. Callister", "Wiley", 2018, "Mechanical", "C2-06", 1350, 2),
    ("9780061120084", "To Kill a Mockingbird", "Harper Lee", "Harper Perennial", 1960, "Literature", "F1-01", 399, 3),
    ("9780143421382", "The God of Small Things", "Arundhati Roy", "Penguin India", 1997, "Literature", "F1-04", 350, 3),
    ("9780062515872", "Wings of Fire", "A.P.J. Abdul Kalam", "Universities Press", 1999, "Literature", "F1-07", 250, 6),
    ("9788172234980", "The Discovery of India", "Jawaharlal Nehru", "Penguin India", 1946, "Literature", "F2-02", 420, 2),
    ("9789387553439", "The Alchemist", "Paulo Coelho", "HarperCollins India", 2015, "Literature", "F2-05", 299, 4),
    ("9780091929787", "How to Win Friends and Influence People", "Dale Carnegie", "Vermilion", 2013, "Management", "G1-01", 350, 4),
    ("9789351344063", "Marketing Management", "Philip Kotler", "Pearson India", 2016, "Management", "G1-04", 890, 3),
    ("9789352607761", "Quantitative Aptitude for Competitive Exams", "R.S. Aggarwal", "S. Chand", 2019, "Competitive Exams", "H1-01", 480, 7),
    ("9789351952268", "GATE 2025: Computer Science Solved Papers", "G.K. Publications", "GKP", 2024, "Competitive Exams", "H1-05", 720, 5),
]

SEED_PEOPLE = [
    ("LIB001", "Anjali Verma", "admin123", "librarian", "anjali.verma@vitbhopal.ac.in", "9893012345", "Central Library", "active"),
    ("LIB002", "Rakesh Tiwari", "admin123", "librarian", "rakesh.t@vitbhopal.ac.in", "9893054321", "Central Library", "active"),
    ("22BEC10145", "Rahul Sharma", "student123", "student", "rahul.sharma2022@vitbhopal.ac.in", "9981022145", "Electronics & Communication", "active"),
    ("23BCE10287", "Priya Nair", "student123", "student", "priya.nair2023@vitbhopal.ac.in", "9752110287", "Computer Science", "active"),
    ("21BCS10093", "Arjun Mehta", "student123", "student", "arjun.mehta2021@vitbhopal.ac.in", "9301456093", "Computer Science", "active"),
    ("24BME10412", "Sneha Patil", "student123", "student", "sneha.patil2024@vitbhopal.ac.in", "9644010412", "Mechanical", "active"),
    ("EMP1042", "Dr. S. K. Mishra", "faculty123", "faculty", "sk.mishra@vitbhopal.ac.in", "9826011042", "School of ECE", "active"),
    ("EMP1108", "Prof. Neha Kulkarni", "faculty123", "faculty", "neha.kulkarni@vitbhopal.ac.in", "9826033108", "School of Computing", "active"),
    ("23BEC11002", "Imran Qureshi", "student123", "student", "imran.q2023@vitbhopal.ac.in", "9098111002", "Electronics & Communication", "pending"),
]


def seed():
    """Fill a brand new database with data that makes the demo look alive."""
    for row in SEED_PEOPLE:
        execute("insert into users (code, name, password, role, email, phone, department, status, created_on) "
                "values (?,?,?,?,?,?,?,?,?)", (*row, today()))

    for isbn, title, author, publisher, year, category, rack, price, total in SEED_BOOKS:
        execute("insert into books (isbn, title, author, publisher, year, category, rack, price, total, available) "
                "values (?,?,?,?,?,?,?,?,?,?)", (isbn, title, author, publisher, year, category, rack, price, total, total))

    people = {r["code"]: r["id"] for r in query("select id, code from users")}

    # (borrower, title, days ago issued, days ago returned or None, fine already settled)
    loans = [
        ("22BEC10145", "Digital Signal Processing", 6, None, False),
        ("23BCE10287", "Introduction to Algorithms", 21, None, False),   # overdue on purpose
        ("21BCS10093", "Clean Code", 30, 8, False),                      # returned late, fine still due
        ("24BME10412", "Engineering Thermodynamics", 2, None, False),
        ("EMP1042", "Computer Networks", 12, None, False),
        ("EMP1042", "Materials Science and Engineering", 12, None, False),
        ("EMP1108", "Database System Concepts", 25, None, False),
        ("22BEC10145", "Concepts of Physics Vol 1", 40, 28, False),      # back on time
        ("23BCE10287", "Python Crash Course", 55, 41, False),
        ("21BCS10093", "The C Programming Language", 60, 44, True),      # late, but settled
        ("EMP1108", "The Alchemist", 70, 66, False),
        ("24BME10412", "Higher Engineering Mathematics", 90, 78, False),
        # Arjun ended up a defaulter: long overdue and still unpaid
        ("21BCS10093", "The God of Small Things", 80, 30, False),
    ]

    books_by_title = {r["title"]: r["id"] for r in query("select id, title from books")}

    for code, title, back_when, returned_back, settled in loans:
        uid, bid = people[code], books_by_title[title]
        issued = date.today() - timedelta(days=back_when)
        role = one("select role from users where id = ?", (uid,))["role"]
        due = issued + timedelta(days=POLICY[role]["days"])
        returned = date.today() - timedelta(days=returned_back) if returned_back is not None else None
        fine = fine_for({"due_on": due.isoformat(), "returned_on": returned.isoformat() if returned else None})
        execute("insert into issues (user_id, book_id, issued_on, due_on, returned_on, fine, fine_paid, issued_by) "
                "values (?,?,?,?,?,?,?,?)",
                (uid, bid, issued.isoformat(), due.isoformat(),
                 returned.isoformat() if returned else None, fine,
                 1 if settled else 0, "Anjali Verma"))
        if not returned:
            execute("update books set available = available - 1 where id = ?", (bid,))

    execute("insert into reservations (user_id, book_id, reserved_on, status) values (?,?,?,?)",
            (people["24BME10412"], books_by_title["Introduction to Algorithms"], today(), "waiting"))
    execute("insert into reservations (user_id, book_id, reserved_on, status) values (?,?,?,?)",
            (people["22BEC10145"], books_by_title["Clean Code"],
             (date.today() - timedelta(days=1)).isoformat(), "ready"))

    notices = [
        ("Library timings during mid-semester exams",
         "The reading hall will stay open till 2:00 AM from 10 October to 25 October. "
         "Issue counter works 9:00 AM to 6:00 PM as usual.", 6),
        ("New arrivals: GATE 2025 solved papers",
         "Twenty copies of GATE 2025 Computer Science solved papers have been added to rack H1. "
         "These can be borrowed for the usual 14 days.", 12),
        ("Fine reminder for overdue books",
         "Students holding books past the due date are requested to clear dues at the earliest. "
         "Unpaid fines above Rs 50 block further issues.", 20),
        ("Book exhibition on 5 October",
         "A one day exhibition with academic publishers will be held in the ground floor lobby. "
         "Faculty and students are welcome.", 31),
    ]
    for title, body, ago in notices:
        execute("insert into notices (title, body, posted_on, posted_by) values (?,?,?,?)",
                (title, body, (date.today() - timedelta(days=ago)).isoformat(), "Anjali Verma"))

    execute("insert into requests (user_id, title, author, reason, requested_on, status, remark) "
            "values (?,?,?,?,?,?,?)",
            (people["EMP1042"], "VLSI Design Principles", "Neil Weste & Harris",
             "Needed for the VLSI design course reference list",
             (date.today() - timedelta(days=9)).isoformat(), "pending", ""))
    execute("insert into requests (user_id, title, author, reason, requested_on, status, remark) "
            "values (?,?,?,?,?,?,?)",
            (people["EMP1108"], "Designing Data-Intensive Applications", "Martin Kleppmann",
             "Good background reading for the distributed systems elective",
             (date.today() - timedelta(days=26)).isoformat(), "approved", "Ordered, expected next week"))
