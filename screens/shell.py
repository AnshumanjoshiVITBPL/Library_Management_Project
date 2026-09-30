"""The frame every portal shares: navy sidebar, top bar, swappable content area."""

from datetime import date

import customtkinter as ctk

import theme as T


class PortalShell(ctk.CTkFrame):
    SIDEBAR_W = 238

    def __init__(self, app, user, pages):
        super().__init__(app, fg_color=T.c("bg"), corner_radius=0)
        self.app = app
        self.user = user
        self.pages = pages
        self.current = pages[0][0]
        self.nav_items = {}
        self._build()
        self.pack(fill="both", expand=True)
        self.show(self.current)

    # ------------------------------------------------------------------ ui
    def _build(self):
        self.grid_columnconfigure(0, minsize=self.SIDEBAR_W, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        side = ctk.CTkFrame(self, width=self.SIDEBAR_W, corner_radius=0, fg_color=T.c("sidebar"))
        side.grid(row=0, column=0, sticky="ns")
        side.grid_propagate(False)

        main = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(2, weight=1)
        main.grid_columnconfigure(0, weight=1)

        self._sidebar(side)
        self._topbar(main)

        self.content = ctk.CTkFrame(main, fg_color=T.c("bg"), corner_radius=0)
        self.content.grid(row=2, column=0, sticky="nsew")

    def _sidebar(self, side):
        brand = ctk.CTkFrame(side, fg_color="transparent")
        brand.pack(fill="x", padx=20, pady=(26, 16))

        logo = ctk.CTkLabel(brand, text="V", width=38, height=38, corner_radius=11,
                            fg_color=T.c("accent"), text_color="#ffffff", font=T.font(19, "bold"))
        logo.pack(side="left")
        words = ctk.CTkFrame(brand, fg_color="transparent")
        words.pack(side="left", padx=(11, 0))
        ctk.CTkLabel(words, text="VIT BHOPAL", font=T.font(15, "bold"),
                     text_color="#ffffff", anchor="w").pack(fill="x")
        ctk.CTkLabel(words, text="Central Library", font=T.font(11),
                     text_color=T.c("sidebar_text"), anchor="w").pack(fill="x")

        ctk.CTkFrame(side, height=2, fg_color="#1b293c", corner_radius=1).pack(fill="x", padx=20, pady=(4, 14))

        role = self.user["role"].upper()
        ctk.CTkLabel(side, text=role + " PORTAL", font=T.font(10, "bold"),
                     text_color="#5f718f", anchor="w").pack(fill="x", padx=24, pady=(0, 6))

        nav = ctk.CTkFrame(side, fg_color="transparent")
        nav.pack(fill="both", expand=True, padx=12)
        for key, label, _ in self.pages:
            btn = ctk.CTkButton(nav, text="  " + label, anchor="w", height=40, corner_radius=10,
                                fg_color="transparent", hover_color="#1a2839",
                                text_color=T.c("sidebar_text"), font=T.font(13, "bold"),
                                command=lambda k=key: self.show(k))
            btn.pack(fill="x", pady=3)
            self.nav_items[key] = btn

        foot = ctk.CTkFrame(side, fg_color="transparent")
        foot.pack(fill="x", padx=12, pady=14)
        ctk.CTkButton(foot, text="  Switch theme", anchor="w", height=36, corner_radius=10,
                      fg_color="#131f2e", hover_color="#1a2839", text_color="#c3d1e4",
                      font=T.font(12, "bold"), border_width=1, border_color="#1f2e42",
                      command=self.app.flip_theme).pack(fill="x", pady=(0, 6))
        ctk.CTkButton(foot, text="  Logout", anchor="w", height=36, corner_radius=10,
                      fg_color="#26181f", hover_color="#3a2129", text_color="#f2888d",
                      font=T.font(12, "bold"), border_width=1, border_color="#3a2530",
                      command=self.app.logout).pack(fill="x")

    def _topbar(self, main):
        top = ctk.CTkFrame(main, fg_color=T.c("head"), corner_radius=0, height=70)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_propagate(False)

        inner = ctk.CTkFrame(top, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left")
        self.title_label = ctk.CTkLabel(left, text="", font=T.font(19, "bold"),
                                        text_color=T.c("text"), anchor="w")
        self.title_label.pack(fill="x")
        self.crumb = ctk.CTkLabel(left, text=date.today().strftime("%A, %d %B %Y"),
                                  font=T.font(11), text_color=T.c("muted"), anchor="w")
        self.crumb.pack(fill="x")

        chip = ctk.CTkFrame(inner, fg_color=T.c("surface2"), corner_radius=22,
                            border_width=1, border_color=T.c("border"))
        chip.pack(side="right")
        initial = self.user["name"].strip()[0].upper()
        ctk.CTkLabel(chip, text=initial, width=32, height=32, corner_radius=16,
                     fg_color=T.c("accent2"), text_color="#ffffff", font=T.font(14, "bold")
                     ).pack(side="left", padx=(6, 0), pady=5)
        who = ctk.CTkFrame(chip, fg_color="transparent")
        who.pack(side="left", padx=(9, 14))
        ctk.CTkLabel(who, text=self.user["name"], font=T.font(12, "bold"),
                     text_color=T.c("text"), anchor="w").pack(fill="x")
        ctk.CTkLabel(who, text=self.user["code"], font=T.font(10),
                     text_color=T.c("muted"), anchor="w").pack(fill="x")

        ctk.CTkFrame(main, height=1, fg_color=T.c("border"), corner_radius=0).grid(row=1, column=0, sticky="ew")

    # -------------------------------------------------------------- pages
    def show(self, key):
        for child in self.content.winfo_children():
            child.destroy()
        self.current = key
        for k, btn in self.nav_items.items():
            on = k == key
            btn.configure(fg_color=T.c("accent") if on else "transparent",
                          text_color="#ffffff" if on else T.c("sidebar_text"))
        page = next(p for p in self.pages if p[0] == key)
        self.title_label.configure(text=page[1])
        page[2](self, self.content)

    def refresh(self):
        self.show(self.current)

    def body(self, scroll=True, padx=24, pady=20):
        frame = (ctk.CTkScrollableFrame(self.content, fg_color="transparent") if scroll
                 else ctk.CTkFrame(self.content, fg_color="transparent"))
        frame.pack(fill="both", expand=True, padx=padx, pady=pady)
        return frame

    def flip_theme(self):
        self.app.flip_theme()
