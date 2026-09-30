"""Self registration for students and faculty. Accounts start as 'pending'."""

import customtkinter as ctk

import database as db
import theme as T
from widgets import FormField, button, popup

DEPARTMENTS = [
    "School of Computer Science & Engineering",
    "School of Electronics & Communication",
    "School of Electrical Engineering",
    "School of Mechanical Engineering",
    "School of Civil Engineering",
    "School of Science (Physics & Chemistry)",
    "School of Mathematics & Statistics",
    "School of Management Studies",
    "School of Law",
    "School of Liberal Arts",
]


class RegisterScreen(ctk.CTkFrame):
    def __init__(self, app):
        super().__init__(app, fg_color=T.c("bg"), corner_radius=0)
        self.app = app
        self.role = "student"
        self._build()

    def _build(self):
        self.pack(fill="both", expand=True)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", padx=28, pady=(22, 0))
        button(bar, "<   Back to login", self.app.show_login, kind="ghost", height=34, width=160,
               font=T.font(12, "bold")).pack(side="left")
        button(bar, "Switch theme", self.app.flip_theme, kind="ghost", height=34, width=140,
               font=T.font(12, "bold")).pack(side="right")

        outer = ctk.CTkScrollableFrame(self, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=20, pady=10)

        card = ctk.CTkFrame(outer, width=640, fg_color=T.c("surface"), corner_radius=18,
                            border_width=1, border_color=T.c("border"))
        card.pack(expand=True, pady=8)

        ctk.CTkFrame(card, fg_color=T.c("accent"), height=5, corner_radius=0).pack(fill="x")
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=36, pady=26)

        ctk.CTkLabel(body, text="Create your library account", font=T.font(24, "bold"),
                     text_color=T.c("text"), anchor="w").pack(fill="x")
        ctk.CTkLabel(body, text="The librarian approves new accounts, usually within a working day.",
                     font=T.font(12), text_color=T.c("muted"), anchor="w").pack(fill="x", pady=(2, 18))

        ctk.CTkLabel(body, text="I am registering as", font=T.font(12, "bold"),
                     text_color=T.c("muted"), anchor="w").pack(fill="x")
        self.role_menu = ctk.CTkSegmentedButton(
            body, values=["Student", "Faculty"], command=self.pick_role, height=38, corner_radius=10,
            fg_color=T.c("surface2"), selected_color=T.c("accent"), selected_hover_color=T.c("accent"),
            unselected_color=T.c("surface2"), unselected_hover_color=T.c("border"),
            text_color="#ffffff", font=T.font(12, "bold"),
        )
        self.role_menu.set("Student")
        self.role_menu.pack(fill="x", pady=(6, 16))

        row = ctk.CTkFrame(body, fg_color="transparent")
        row.pack(fill="x", pady=(0, 12))
        self.code = FormField(row, self.id_label(), placeholder="22BEC10145", width=252)
        self.code.pack(side="left", expand=True, fill="x")
        ctk.CTkFrame(row, width=16, fg_color="transparent").pack(side="left")
        self.name = FormField(row, "Full name", placeholder="As per university records", width=252)
        self.name.pack(side="left", expand=True, fill="x")

        self.department = FormField(body, "School / Department", values=DEPARTMENTS, width=520)
        self.department.pack(fill="x", pady=(0, 12))

        row2 = ctk.CTkFrame(body, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 12))
        self.email = FormField(row2, "Email", placeholder="name2022@vitbhopal.ac.in", width=252)
        self.email.pack(side="left", expand=True, fill="x")
        ctk.CTkFrame(row2, width=16, fg_color="transparent").pack(side="left")
        self.phone = FormField(row2, "Phone", placeholder="10 digit mobile", width=252)
        self.phone.pack(side="left", expand=True, fill="x")

        row3 = ctk.CTkFrame(body, fg_color="transparent")
        row3.pack(fill="x", pady=(0, 6))
        self.password = FormField(row3, "Password", show="*", placeholder="At least 4 characters", width=252)
        self.password.pack(side="left", expand=True, fill="x")
        ctk.CTkFrame(row3, width=16, fg_color="transparent").pack(side="left")
        self.confirm = FormField(row3, "Confirm password", show="*", width=252)
        self.confirm.pack(side="left", expand=True, fill="x")

        self.error = ctk.CTkLabel(body, text="", font=T.font(12), text_color=T.c("bad"),
                                  anchor="w", wraplength=520, justify="left")
        self.error.pack(fill="x", pady=(4, 0))

        button(body, "Submit registration", self.submit, kind="primary", height=44).pack(fill="x", pady=(14, 0))

        tip = ctk.CTkFrame(body, fg_color=T.c("surface2"), corner_radius=12, border_width=1,
                           border_color=T.c("border"))
        tip.pack(fill="x", pady=(18, 0))
        ctk.CTkLabel(tip, text="Students can borrow 2 books for 14 days.\n"
                               "Faculty can borrow 5 books for 60 days.\n"
                               "Late returns cost Rs %d per day." % db.FINE_PER_DAY,
                     font=T.font(12), text_color=T.c("muted"), justify="left", anchor="w"
                     ).pack(fill="x", padx=16, pady=14)

    def id_label(self):
        return "Registration number" if self.role == "student" else "Employee ID"

    def pick_role(self, label):
        self.role = "student" if label == "Student" else "faculty"
        self.code.widget.configure(placeholder_text="22BEC10145" if self.role == "student" else "EMP1042")
        # rebuild just the label above the id box
        self.code.winfo_children()[0].configure(text=self.id_label())

    def submit(self):
        password = self.password.widget.get()
        if password != self.confirm.widget.get():
            self.error.configure(text="The two passwords do not match")
            return

        phone = self.phone.get()
        if phone and not (phone.isdigit() and len(phone) == 10):
            self.error.configure(text="Phone number should be exactly 10 digits")
            return

        ok, message = db.register(
            self.code.get(), self.name.get(), password, self.role,
            self.email.get(), phone, self.department.get(),
        )
        if not ok:
            self.error.configure(text=message)
            return

        self.error.configure(text="")
        popup(self, "Registration received", message, kind="ok")
        self.app.show_login()
