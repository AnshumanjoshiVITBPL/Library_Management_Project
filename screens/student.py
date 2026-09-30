"""Student portal - the borrower pages with the student borrowing limits."""

from screens.about import about
from screens.borrower import (catalogue, dashboard, history, my_books, notices,
                              profile, reservations)
from screens.shell import PortalShell


class StudentPortal(PortalShell):
    def __init__(self, app, user):
        super().__init__(app, user, [
            ("dashboard", "Dashboard", dashboard),
            ("catalogue", "Search books", catalogue),
            ("mybooks", "My books", my_books),
            ("history", "History", history),
            ("reservations", "Reservations", reservations),
            ("notices", "Notices", notices),
            ("profile", "My profile", profile),
            ("about", "Help and rules", about),
        ])
