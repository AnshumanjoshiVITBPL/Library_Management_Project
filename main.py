"""VIT Bhopal Central Library - Management System

Run this file. The database is created next to it on first launch and comes
pre-loaded with demo books, users and transactions
"""

import customtkinter as ctk

import database as db
import theme as T
from screens.login import LoginScreen
from screens.register import RegisterScreen
from screens.student import StudentPortal
from screens.faculty import FacultyPortal
from screens.librarian import LibrarianPortal

PORTALS = {
    "student": StudentPortal,
    "faculty": FacultyPortal,
    "librarian": LibrarianPortal,
}


class LibraryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        db.init_db()
        T.set_mode("dark")

        self.title("VIT Bhopal  |  Central Library Management System")
        self.geometry("1320x820")
        self.minsize(1160, 720)
        self.configure(fg_color=T.c("bg"))

        self.user = None
        self.view = None
        self.where = "login"
        self.show_login()


    def _swap(self, widget):
        if self.view is not None:
            self.view.destroy()
        self.view = widget

    def show_login(self):
        self.user = None
        self.where = "login"
        self._swap(LoginScreen(self))

    def show_register(self):
        self.where = "register"
        self._swap(RegisterScreen(self))

    def enter_portal(self, person):
        self.user = person
        self.where = "portal"
        self._swap(PORTALS[person["role"]](self, person))

    def logout(self):
        self.show_login()

    def flip_theme(self):
        """Rebuilds whatever is on screen so the new palette applies everywhere"""
        T.toggle_mode()
        self.configure(fg_color=T.c("bg"))
        if self.where == "portal":
            self._swap(PORTALS[self.user["role"]](self, self.user))
        elif self.where == "register":
            self.show_register()
        else:
            self.show_login()


if __name__ == "__main__":
    app = LibraryApp()
    app.mainloop()
