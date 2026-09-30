"""Reusable pieces of the interface: cards, tables, popups, form fields, charts."""

import tkinter as tk

import customtkinter as ctk

import theme as T


def _hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(int(x) for x in rgb)


def _blend(c1, c2, t):
    a, b = _hex_to_rgb(c1), _hex_to_rgb(c2)
    return _rgb_to_hex([a[i] + (b[i] - a[i]) * t for i in range(3)])


class BrandPanel(ctk.CTkCanvas):
    """
    The decorated strip on the left of the login screen Everything text
    included is drawn on the canvas so the gradient shows through behind it
    """

    def __init__(self, master, top="#0a111d", bottom="#14406e", **kw):
        kw.setdefault("highlightthickness", 0)
        kw.setdefault("bd", 0)
        super().__init__(master, **kw)
        self.top, self.bottom = top, bottom
        self.bind("<Configure>", lambda e: self.paint())

    def paint(self):
        self.delete("all")
        w = max(self.winfo_width(), 1)
        h = max(self.winfo_height(), 1)
        step = 3
        for y in range(0, h, step):
            self.create_rectangle(0, y, w, y + step, width=0,
                                  fill=_blend(self.top, self.bottom, min(y / h, 1.0)))
        glow = _blend(self.bottom, "#ffffff", 0.13)
        for cx, cy, r in ((w * 0.82, h * 0.12, 120), (w * 0.12, h * 0.80, 150), (w * 0.94, h * 0.92, 80)):
            self.create_oval(cx - r, cy - r, cx + r, cy + r, width=0, fill=glow)

        x = w * 0.10
        textw = w * 0.80

        self.create_rectangle(x, h * 0.17, x + 176, h * 0.17 + 26, width=0, fill="#1d3f68")
        self.create_text(x + 14, h * 0.17 + 13, text="EST. 2017   ·   BHOPAL, M.P.",
                         fill="#a9cdf5", font=("Segoe UI", 9, "bold"), anchor="w")

        self.create_text(x, h * 0.245, text="VIT BHOPAL", fill="#ffffff",
                         font=("Segoe UI", 34, "bold"), anchor="w")
        self.create_text(x, h * 0.325, text="Central Library", fill="#8fc0f2",
                         font=("Segoe UI", 19), anchor="w")
        self.create_rectangle(x, h * 0.375, x + 64, h * 0.375 + 3, width=0, fill="#f2a93b")

        self.create_text(x, h * 0.42, anchor="nw", width=textw, justify="left",
                         text="One place to discover, borrow, renew and track every book "
                              "on campus. Students, faculty and the library desk each get "
                              "their own portal.",
                         fill="#c2d5ea", font=("Segoe UI", 12))

        y = h * 0.575
        for line in ("Search the catalogue by title, author, ISBN or section",
                     "Live due dates, renewals and fine tracking",
                     "Reserve a title and get notified when it is back"):
            self.create_text(x, y, text="\u25cf", fill="#f2a93b", font=("Segoe UI", 8), anchor="w")
            self.create_text(x + 18, y, text=line, fill="#d6e4f2", font=("Segoe UI", 12),
                             anchor="w", width=textw - 18, justify="left")
            y += 34

        self.create_text(x, h * 0.90, anchor="w",
                         text="Mon - Fri   8:30 AM to 8:00 PM        Sat   9:00 AM to 5:00 PM",
                         fill="#7f9dc0", font=("Segoe UI", 11))


def Badge(master, text, kind="accent"):
    colour = {"accent": T.c("accent"), "ok": T.c("ok"), "warn": T.c("warn"),
              "bad": T.c("bad"), "muted": T.c("muted"), "gold": T.c("gold")}.get(kind, T.c("accent"))
    return ctk.CTkLabel(
        master, text=text, height=24, corner_radius=12,
        text_color="#ffffff", fg_color=colour,
        font=T.font(11, "bold"), padx=10,
    )



# buttons and inputs


KINDS = {
    "primary": lambda: dict(fg_color=T.c("accent"), hover_color=_blend(T.c("accent"), "#000000", 0.22), text_color="#ffffff", border_width=0),
    "teal": lambda: dict(fg_color=T.c("accent2"), hover_color=_blend(T.c("accent2"), "#000000", 0.22), text_color="#ffffff", border_width=0),
    "gold": lambda: dict(fg_color=T.c("gold"), hover_color=_blend(T.c("gold"), "#000000", 0.2), text_color="#1b1305", border_width=0),
    "danger": lambda: dict(fg_color=T.c("bad"), hover_color=_blend(T.c("bad"), "#000000", 0.2), text_color="#ffffff", border_width=0),
    "success": lambda: dict(fg_color=T.c("ok"), hover_color=_blend(T.c("ok"), "#000000", 0.2), text_color="#ffffff", border_width=0),
    "ghost": lambda: dict(fg_color=T.c("surface2"), hover_color=_blend(T.c("surface2"), T.c("accent"), 0.18),
                          text_color=T.c("text"), border_width=1, border_color=T.c("border")),
}


def button(master, text, command=None, kind="primary", height=38, width=None, **kw):
    opts = {"corner_radius": 10, "font": T.font(13, "bold")}
    opts.update(KINDS.get(kind, KINDS["primary"])())
    opts.update(kw)
    if width is not None:
        opts["width"] = width
    return ctk.CTkButton(master, text=text, command=command, height=height, **opts)


class FormField(ctk.CTkFrame):
    """A label sitting on top of an entry, so forms stay readable"""

    def __init__(self, master, label, placeholder="", show=None, width=300, values=None):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text=label, anchor="w", font=T.font(12, "bold"),
                     text_color=T.c("muted")).pack(fill="x", padx=2)
        if values:
            self.widget = ctk.CTkComboBox(
                self, values=values, width=width, height=38, corner_radius=10,
                fg_color=T.c("surface2"), border_color=T.c("border"), border_width=1,
                text_color=T.c("text"), button_color=T.c("accent"), dropdown_fg_color=T.c("surface"),
                font=T.font(13),
            )
            self.widget.set(values[0])
        else:
            self.widget = ctk.CTkEntry(
                self, width=width, height=38, corner_radius=10, placeholder_text=placeholder,
                fg_color=T.c("surface2"), border_color=T.c("border"), border_width=1,
                text_color=T.c("text"), placeholder_text_color=T.c("muted"),
                font=T.font(13), show=show or "",
            )
        self.widget.pack(fill="x", pady=(5, 0))

    def get(self):
        return self.widget.get().strip()

    def set(self, value):
        if isinstance(self.widget, ctk.CTkComboBox):
            self.widget.set(value)
        else:
            self.widget.delete(0, "end")
            self.widget.insert(0, str(value))

    def clear(self):
        if not isinstance(self.widget, ctk.CTkComboBox):
            self.widget.delete(0, "end")

    def toggle_secret(self):
        if isinstance(self.widget, ctk.CTkEntry):
            self.widget.configure(show="" if self.widget.cget("show") else "*")


class TextareaForm(ctk.CTkFrame):
    """Label plus a multi line box, used for notices and request reasons"""

    def __init__(self, master, label, width=520, height=110):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text=label, anchor="w", font=T.font(12, "bold"),
                     text_color=T.c("muted")).pack(fill="x", padx=2)
        self.widget = ctk.CTkTextbox(
            self, width=width, height=height, corner_radius=10,
            fg_color=T.c("surface2"), border_color=T.c("border"), border_width=1,
            text_color=T.c("text"), font=T.font(13),
        )
        self.widget.pack(fill="x", pady=(5, 0))

    def get(self):
        return self.widget.get("1.0", "end").strip()

    def set(self, value):
        self.widget.delete("1.0", "end")
        self.widget.insert("1.0", value)

    def clear(self):
        self.widget.delete("1.0", "end")



# layout blocks


def card(master, **extra):
    return ctk.CTkFrame(master, **T.surface_kwargs(**extra))


def page_title(master, title, subtitle=None):
    wrap = ctk.CTkFrame(master, fg_color="transparent")
    ctk.CTkLabel(wrap, text=title, font=T.font(24, "bold"),
                 text_color=T.c("text"), anchor="w").pack(fill="x")
    if subtitle:
        ctk.CTkLabel(wrap, text=subtitle, font=T.font(13),
                     text_color=T.c("muted"), anchor="w").pack(fill="x", pady=(2, 0))
    return wrap


class StatCard(ctk.CTkFrame):
    """One of the little numbers along the top of a dashboard"""

    def __init__(self, master, label, value, symbol="", kind="accent", note=None):
        super().__init__(master, corner_radius=14, border_width=1,
                         border_color=T.c("border"), fg_color=T.c("surface"))
        colour = T.c(kind if kind in ("accent", "accent2", "gold", "ok", "warn", "bad") else "accent")

        ctk.CTkFrame(self, width=4, corner_radius=2, fg_color=colour).place(relheight=0.62, rely=0.19, x=0)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=14)

        top = ctk.CTkFrame(body, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=label.upper(), font=T.font(11, "bold"),
                     text_color=T.c("muted"), anchor="w").pack(side="left")
        if symbol:
            ctk.CTkLabel(top, text=symbol, width=30, height=30, corner_radius=9,
                         fg_color=_blend(colour, T.c("surface"), 0.78), text_color=colour,
                         font=T.font(15, "bold")).pack(side="right")

        self.value_label = ctk.CTkLabel(body, text=str(value), font=T.font(28, "bold"),
                                       text_color=T.c("text"), anchor="w")
        self.value_label.pack(fill="x", pady=(6, 0))
        if note:
            ctk.CTkLabel(body, text=note, font=T.font(11), text_color=T.c("muted"),
                         anchor="w").pack(fill="x")

    def set_value(self, value):
        self.value_label.configure(text=str(value))


# table


class Table(ctk.CTkFrame):
    """
    A scrollable grid.

    columns is a list of (key, heading, weight). A cell value may also be a
    tuple of (text, colour-key) when it should be highlighted, e.g. ("Overdue", "bad").
    actions is a list of (label, callback, kind) rendered as small buttons per row
    """

    def __init__(self, master, columns, actions=None, height=380, empty_text="Nothing to show right now",
                 action_filter=None):
        super().__init__(master, **T.surface_kwargs())
        # grid weights have to be whole numbers, so round whatever the page asked for
        self.columns = [(key, title, max(1, int(round(float(weight))))) for key, title, weight in columns]
        self.actions = actions or []
        self.empty_text = empty_text
        # optional callable(row, label) -> bool to hide a button on some rows
        self.action_filter = action_filter
        self.ncols = len(self.columns) + (1 if self.actions else 0)
        # room for every button at once, so rows with fewer buttons (hidden by
        # action_filter) still line up with the header
        self.actions_logical = 26 + sum(26 + 7 * len(label) for label, _, _ in self.actions) \
            + 6 * max(len(self.actions) - 1, 0)
        self.actions_px = self.actions_logical

        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent", height=height)
        self.body.pack(fill="both", expand=True, padx=8, pady=8)
        self._frames = []
        self._tries = 0
        self._done = False

    def _cells(self, parent, values, header=False):
        """
        Lay one line of the table out in `parent`. Header and data rows share
        this single code path, and _layout gives every line the same column
        widths, so the columns stay lined up.
        """
        parent.cell_labels = []
        for i, (_, _, _) in enumerate(self.columns):
            label = values[i]
            colour = T.c("muted") if header else T.c("text")
            if not header and isinstance(label, tuple):
                label, hint = label
                palette = T.PALETTES[T.mode()]
                colour = palette[hint] if hint in palette else hint
            widget = ctk.CTkLabel(parent, text=str(label), anchor="w",
                                  font=T.font(11, "bold") if header else T.font(12),
                                  text_color=colour, justify="left", wraplength=60)
            widget.grid(row=0, column=i, sticky="ew", padx=10, pady=9)
            parent.cell_labels.append(widget)
        if self.actions:
            if header:
                ctk.CTkLabel(parent, text=values[-1], anchor="e", font=T.font(11, "bold"),
                             text_color=T.c("muted")).grid(
                    row=0, column=len(self.columns), sticky="ew", padx=10, pady=9)
                return None
            box = ctk.CTkFrame(parent, fg_color="transparent")
            box.grid(row=0, column=len(self.columns), sticky="e", padx=10, pady=5)
            return box
        return None

    def _layout(self, _event=None, force=False):
        """
        Give every line of the table the same fixed column widths, worked out
        from how wide the table actually ended up. Fixed widths beat letting
        each line size itself which is what made headers drift off the rows
        """
        if not self._frames:
            return
        if self._done and not force:
            return
        # measure the table itself: a line frame can already be overflowing the
        # canvas, so asking a line how wide it is would freeze the overflow in
        width = self.winfo_width() - 42
        if width < 80:
            # not on screen yet, try again in a moment
            if self._tries < 6:
                self._tries += 1
                self.after(120, self._layout)
            return
        self._done = True
        # scaling is only trustworthy once the widget is on screen
        self.actions_px = int(self.actions_logical * ctk.ScalingTracker.get_widget_scaling(self))
        # leave room for the scrollbar so the button column never gets clipped
        data_w = width - (self.actions_px if self.actions else 0)
        total = sum(weight for _, _, weight in self.columns)
        shares = [data_w * weight // total for _, _, weight in self.columns]
        shares[-1] += data_w - sum(shares)
        for frame in self._frames:
            for i, share in enumerate(shares):
                frame.grid_columnconfigure(i, weight=0, minsize=share)
                frame.cell_labels[i].configure(wraplength=max(50, share - 24))
            if self.actions:
                frame.grid_columnconfigure(len(self.columns), weight=0, minsize=self.actions_px)

    def load(self, rows):
        for child in self.body.winfo_children():
            child.destroy()
        self._frames = []
        self._tries = 0
        self._done = False
        # pages attach their buttons after building the table, so work out
        # how much room the button column needs here, not in __init__
        self.ncols = len(self.columns) + (1 if self.actions else 0)
        self.actions_logical = 26 + sum(26 + 7 * len(label) for label, _, _ in self.actions) \
            + 6 * max(len(self.actions) - 1, 0)

        if not rows:
            ctk.CTkLabel(self.body, text=self.empty_text, font=T.font(13),
                         text_color=T.c("muted")).pack(pady=40)
            return

        self.body.grid_columnconfigure(0, weight=1)

        head = ctk.CTkFrame(self.body, fg_color=T.c("surface2"), corner_radius=10)
        head.grid(row=0, column=0, columnspan=self.ncols, sticky="ew", pady=(0, 4))
        titles = [title for _, title, _ in self.columns]
        if self.actions:
            titles.append("Actions")
        self._cells(head, titles, header=True)
        self._frames.append(head)

        for r, row in enumerate(rows):
            shade = T.c("surface") if r % 2 == 0 else T.c("row_alt")
            line = ctk.CTkFrame(self.body, fg_color=shade, corner_radius=8)
            line.grid(row=r + 1, column=0, columnspan=self.ncols, sticky="ew", pady=2)
            slot = self._cells(line, [row.get(key, "") for key, _, _ in self.columns])
            self._frames.append(line)
            if self.actions:
                for label, callback, kind in reversed(self.actions):
                    if self.action_filter and not self.action_filter(row, label):
                        continue
                    button(slot, label, lambda row=row, fn=callback: fn(row), kind=kind,
                           height=28, width=26 + 7 * len(label), font=T.font(11, "bold"),
                           corner_radius=8).pack(side="right", padx=(6, 0))

        self.after(120, self._layout)
        # by now the scrollbar has appeared or not, so measure once more
        self.after(650, lambda: self._layout(force=True))



# popups


def popup(parent, title, message, kind="info"):
    colour = {"info": T.c("accent"), "ok": T.c("ok"), "warn": T.c("warn"),
              "error": T.c("bad")}.get(kind, T.c("accent"))

    win = ctk.CTkToplevel(parent)
    win.title(title)
    win.geometry("430x230")
    win.resizable(False, False)
    win.configure(fg_color=T.c("bg"))
    win.attributes("-topmost", True)
    win.after(120, win.grab_set)

    ctk.CTkFrame(win, fg_color=colour, height=5).pack(fill="x")
    body = ctk.CTkFrame(win, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=26, pady=20)
    ctk.CTkLabel(body, text=title, font=T.font(18, "bold"), text_color=T.c("text"),
                 anchor="w").pack(fill="x")
    ctk.CTkLabel(body, text=message, font=T.font(13), text_color=T.c("muted"),
                 anchor="w", justify="left", wraplength=370).pack(fill="x", pady=(10, 0))
    button(body, "Okay", win.destroy, kind="primary", width=110).pack(anchor="e", pady=(16, 0))
    _centre(win, parent)
    return win


def confirm(parent, title, message, on_yes):
    win = ctk.CTkToplevel(parent)
    win.title(title)
    win.geometry("430x220")
    win.resizable(False, False)
    win.configure(fg_color=T.c("bg"))
    win.attributes("-topmost", True)
    win.after(120, win.grab_set)

    ctk.CTkFrame(win, fg_color=T.c("warn"), height=5).pack(fill="x")
    body = ctk.CTkFrame(win, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=26, pady=20)
    ctk.CTkLabel(body, text=title, font=T.font(18, "bold"), text_color=T.c("text"),
                 anchor="w").pack(fill="x")
    ctk.CTkLabel(body, text=message, font=T.font(13), text_color=T.c("muted"),
                 anchor="w", justify="left", wraplength=370).pack(fill="x", pady=(10, 0))

    row = ctk.CTkFrame(body, fg_color="transparent")
    row.pack(fill="x", pady=(16, 0))
    button(row, "Cancel", win.destroy, kind="ghost", width=110).pack(side="right")

    def yes():
        win.destroy()
        on_yes()

    button(row, "Yes, go ahead", yes, kind="danger", width=140).pack(side="right", padx=10)
    _centre(win, parent)
    return win


def ask_text(parent, title, prompt, on_submit, placeholder=""):
    win = ctk.CTkToplevel(parent)
    win.title(title)
    win.geometry("430x220")
    win.resizable(False, False)
    win.configure(fg_color=T.c("bg"))
    win.attributes("-topmost", True)
    win.after(120, win.grab_set)

    ctk.CTkFrame(win, fg_color=T.c("accent"), height=5).pack(fill="x")
    body = ctk.CTkFrame(win, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=26, pady=20)
    ctk.CTkLabel(body, text=title, font=T.font(18, "bold"), text_color=T.c("text"),
                 anchor="w").pack(fill="x")
    ctk.CTkLabel(body, text=prompt, font=T.font(12), text_color=T.c("muted"),
                 anchor="w").pack(fill="x", pady=(6, 8))
    entry = ctk.CTkEntry(body, height=38, corner_radius=10, placeholder_text=placeholder,
                         fg_color=T.c("surface2"), border_color=T.c("border"),
                         text_color=T.c("text"), font=T.font(13))
    entry.pack(fill="x")
    entry.focus_set()

    def submit(event=None):
        value = entry.get().strip()
        win.destroy()
        on_submit(value)

    row = ctk.CTkFrame(body, fg_color="transparent")
    row.pack(fill="x", pady=(16, 0))
    button(row, "Cancel", win.destroy, kind="ghost", width=110).pack(side="right")
    button(row, "Save", submit, kind="primary", width=110).pack(side="right", padx=10)
    entry.bind("<Return>", submit)
    _centre(win, parent)
    return win


def _centre(win, parent):
    win.update_idletasks()
    try:
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
    except tk.TclError:
        px, py, pw, ph = 200, 200, 900, 600
    w, h = win.winfo_width(), win.winfo_height()
    win.geometry("+%d+%d" % (max(px + (pw - w) // 2, 0), max(py + (ph - h) // 2, 0)))



# charts


def chart(parent, build, height=230):
    """build(ax, colours) draws whatever it likes on the given axes."""
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    fig = Figure(figsize=(5.4, height / 100), dpi=100, facecolor=T.c("surface"))
    ax = fig.add_subplot(111)
    ax.set_facecolor(T.c("surface"))
    build(ax, {
        "text": T.c("text"), "muted": T.c("muted"), "accent": T.c("accent"),
        "accent2": T.c("accent2"), "gold": T.c("gold"), "grid": T.c("border"),
        "surface": T.c("surface"), "bad": T.c("bad"), "ok": T.c("ok"),
    })
    for spine in ax.spines.values():
        spine.set_color(T.c("border"))
    ax.tick_params(colors=T.c("muted"), labelsize=8)
    fig.tight_layout(pad=1.2)

    holder = ctk.CTkFrame(parent, **T.surface_kwargs())
    canvas = FigureCanvasTkAgg(fig, master=holder)
    canvas.draw()
    canvas.get_tk_widget().configure(bg=T.c("surface"), highlightthickness=0)
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
    return holder
