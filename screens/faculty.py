"""Faculty portal - same as the student one, with purchase requests added."""

from screens.about import about
from screens.borrower import (catalogue, dashboard, history, my_books, notices,
                              profile, requests, reservations)
from screens.shell import PortalShell


class FacultyPortal(PortalShell):
    def __init__(self, app, user):
        super().__init__(app, user, [
            ("dashboard", "Dashboard", dashboard),
            ("catalogue", "Search books", catalogue),
            ("mybooks", "My books", my_books),
            ("history", "History", history),
            ("reservations", "Reservations", reservations),
            ("requests", "Purchase requests", requests),
            ("notices", "Notices", notices),
            ("profile", "My profile", profile),
            ("about", "Help and rules", about),
        ])
