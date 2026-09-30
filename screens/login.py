"""Landing screen: role picker and login form."""

import customtkinter as ctk

import database as db
import theme as T
from widgets import BrandPanel, FormField, button

LABEL_TO_ROLE = {"Student": "student", "Faculty": "faculty", "Librarian": "librarian"}
ROLE_TO_LABEL = {v: k for k, v in LABEL_TO_ROLE.items()}

PLACEHOLDERS = {
    "student": "Registration number, e.g. 22BEC10145",
    "faculty": "Employee ID, e.g. EMP1042",
    "librarian": "Librarian ID, e.g. LIB001",
}

DEMO = [
    ("Librarian", "LIB001", "admin123"),
    ("Faculty", "EMP1042", "faculty123"),
    ("Student", "22BEC10145", "student123"),
]


class LoginScreen(ctk.CTkFrame):
    def __init__(self, app):
        super().__init__(app, fg_color=T.c("bg"), corner_radius=0)
        self.app = app
        self.role = "student"
        self._build()

    def _build(self):
        self.pack(fill="both", expand=True)

        panel = BrandPanel(self, "#0a111d", "#14406e")
        panel.configure(width=470)
        panel.pack(side="left", fill="y")

        right = ctk.CTkFrame(self, fg_color=T.c("bg"), corner_radius=0)
        right.pack(side="left", fill="both", expand=True)

        button(right, "Switch theme", self.app.flip_theme, kind="ghost", height=32, width=130,
               font=T.font(11, "bold")).place(relx=1.0, x=-24, y=20, anchor="ne")

        form = ctk.CTkFrame(right, width=440, fg_color=T.c("surface"), corner_radius=18,
                            border_width=1, border_color=T.c("border"))
        form.pack(expand=True, pady=20)
        inner = ctk.CTkFrame(form, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=34, pady=28)

        ctk.CTkLabel(inner, text="Sign in", font=T.font(26, "bold"),
                     text_color=T.c("text"), anchor="w").pack(fill="x")
        ctk.CTkLabel(inner, text="Choose your portal to continue", font=T.font(12),
                     text_color=T.c("muted"), anchor="w").pack(fill="x", pady=(2, 18))

        self.role_menu = ctk.CTkSegmentedButton(
            inner, values=list(LABEL_TO_ROLE), command=self.pick_role, height=38, corner_radius=10,
            fg_color=T.c("surface2"), selected_color=T.c("accent"), selected_hover_color=T.c("accent"),
            unselected_color=T.c("surface2"), unselected_hover_color=T.c("border"),
            text_color="#ffffff", font=T.font(12, "bold"),
        )
        self.role_menu.set(ROLE_TO_LABEL[self.role])
        self.role_menu.pack(fill="x")

        self.code_field = FormField(inner, "User ID", placeholder=PLACEHOLDERS[self.role], width=362)
        self.code_field.pack(fill="x", pady=(18, 0))

        self.pass_field = FormField(inner, "Password", show="*", width=362)
        self.pass_field.pack(fill="x", pady=(14, 0))
        ctk.CTkCheckBox(inner, text="Show password", command=self.pass_field.toggle_secret,
                        font=T.font(11), text_color=T.c("muted"), fg_color=T.c("accent"),
                        hover_color=T.c("accent"), checkbox_width=18, checkbox_height=18,
                        border_color=T.c("border")).pack(anchor="w", pady=(8, 0))

        self.error = ctk.CTkLabel(inner, text="", font=T.font(12), text_color=T.c("bad"),
                                  anchor="w", wraplength=360, justify="left")
        self.error.pack(fill="x", pady=(10, 0))

        button(inner, "Login", self.submit, kind="primary", height=44).pack(fill="x", pady=(10, 0))

        line = ctk.CTkFrame(inner, fg_color="transparent")
        line.pack(fill="x", pady=(16, 0))
        ctk.CTkLabel(line, text="New to the library?", font=T.font(12),
                     text_color=T.c("muted")).pack(side="left")
        ctk.CTkButton(line, text="Create an account", command=self.app.show_register, height=26,
                      corner_radius=8, fg_color="transparent", hover_color=T.c("surface2"),
                      text_color=T.c("accent"), font=T.font(12, "bold")).pack(side="left", padx=4)

        ctk.CTkFrame(inner, height=1, fg_color=T.c("border")).pack(fill="x", pady=(18, 14))
        ctk.CTkLabel(inner, text="DEMO ACCOUNTS - click to fill", font=T.font(10, "bold"),
                     text_color=T.c("muted"), anchor="w").pack(fill="x")
        quick = ctk.CTkFrame(inner, fg_color="transparent")
        quick.pack(fill="x", pady=(8, 0))
        for label, code, password in DEMO:
            button(quick, label, lambda l=label, c=code, p=password: self.fill_demo(l, c, p),
                   kind="ghost", height=30, font=T.font(11, "bold")).pack(side="left", padx=(0, 8))

        self.code_field.widget.bind("<Return>", lambda e: self.submit())
        self.pass_field.widget.bind("<Return>", lambda e: self.submit())

    def pick_role(self, label):
        self.role = LABEL_TO_ROLE[label]
        self.code_field.widget.configure(placeholder_text=PLACEHOLDERS[self.role])
        self.error.configure(text="")

    def fill_demo(self, label, code, password):
        self.role_menu.set(label)
        self.pick_role(label)
        self.code_field.set(code)
        self.pass_field.set(password)
        self.error.configure(text="")

    def submit(self):
        code = self.code_field.get()
        password = self.pass_field.widget.get()
        if not code or not password:
            self.error.configure(text="Please enter both your ID and password")
            return

        person, problem = db.login(code, password, self.role)
        if not person:
            self.error.configure(text=problem)
            return

        self.error.configure(text="")
        self.app.enter_portal(person)
