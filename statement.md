# Project Statement

## Problem Statement
Managing academic library resources manually or with outdated software leads to inefficiencies, lost books, and inaccurate fine tracking. Students and faculty need a transparent way to check book availability, track their current loans, and manage reservations without physically visiting the issue counter.

## Scope of the Project
This project involves developing a standalone, GUI-based desktop application for the VIT Bhopal Central Library. It handles local data storage via an SQLite database, enforces role-based borrowing limits, automatically calculates late fines, manages reservation queues, and allows the librarian to export circulation reports.

## Target Users
1. **Students:** Can borrow up to 2 books for 14 days, check availability, place reservations, and view pending fines.
2. **Faculty:** Can borrow up to 5 books for 60 days, request new book purchases, and check catalogue availability.
3. **Librarians:** Have administrative control to issue/return books, manage users, update the book catalogue, post notices, and export statistical reports.

## High-Level Features
* **Authentication & Profiles:** Secure login and account status management (active, pending, blocked).
* **Automated Circulation Rules:** Built-in enforcement of borrowing limits and fine accumulation based on user roles.
* **Catalogue Search Engine:** Title, author, and ISBN filtering.
* **Notification System:** Global library notices and direct purchase request approvals.
* **Data Export:** Generation of multi-sheet XLSX reports for transactions, overdue items, and active member lists.