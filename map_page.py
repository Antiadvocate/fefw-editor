"""map_page.py - the World map page: show or hide the map's points.

A mixin for the App (see editor_advanced.AdvancedMixin).  The page lists the
game's map points and roads from `map_spots.json`, reads what this save says
about each (`GmapSpotMgr`, see worldmap.py) and writes the two bytes that
control whether a point is drawn and whether it is marked visited.  Every
edit goes through `_core_edit`, so it is undoable, mirrored across the route's
slots like every other page, and written with Ctrl+S.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

import fefw_core as core
import worldmap as wm
from ui_util import enable_multi_select

VIEWS = (("places", "Places"), ("roads", "Roads"), ("points", "Junctions & road points"))
NOTE = (
    "“Shown” makes a point appear on the world map; it does not open anything behind it — "
    "gates, battles, rewards, quests and fast travel keep their own conditions. “Visited” "
    "is the white versus the dark icon. Roads are drawn through their own points, so "
    "showing a road also shows the places and junctions at its ends; hiding one only hides "
    "the points that belong to that road. “State 2” is a value the game writes on some "
    "road points that isn't understood yet: it is listed as it is and changed only if you "
    "pick it. Close the game and keep a backup before you write."
)


class MapPageMixin:
    # ------------------------------------------------------------------ build
    def _build_world_map(self):
        page = self.world_page
        self.map_view = "places"
        self._map_rows: dict[str, tuple] = {}
        top = ttk.Frame(page, style="Card.TFrame", padding=(14, 12))
        top.pack(fill="x")
        row = ttk.Frame(top, style="Card.TFrame")
        row.pack(fill="x")
        ttk.Label(row, text="World map", style="CardH3.TLabel").pack(side="left")
        self.map_count = ttk.Label(row, text="", style="CardMuted.TLabel")
        self.map_count.pack(side="left", padx=(10, 0))
        for text, cmd in (("Mark unvisited", lambda: self.map_selected(None, 0)),
                          ("Mark visited", lambda: self.map_selected(None, 1)),
                          ("Hide", lambda: self.map_selected(wm.HIDDEN, None)),
                          ("Show", lambda: self.map_selected(wm.SHOWN, None))):
            ttk.Button(row, text=text, style="Small.TButton", command=cmd).pack(
                side="right", padx=(6, 0))

        views = ttk.Frame(top, style="Card.TFrame")
        views.pack(fill="x", pady=(8, 0))
        self._map_view_btns = {}
        for key, text in VIEWS:
            b = ttk.Button(views, text=text, style="Small.TButton",
                           command=lambda k=key: self.set_map_view(k))
            b.pack(side="left", padx=(0, 6))
            self._map_view_btns[key] = b
        self.map_search = ttk.Entry(views, width=34)
        self.map_search.pack(side="right")
        self.map_search.bind("<KeyRelease>", lambda e: self.refresh_world_map())

        bulk = ttk.Frame(top, style="Card.TFrame")
        bulk.pack(fill="x", pady=(8, 0))
        ttk.Label(bulk, text="Everything at once:", style="CardMuted.TLabel").pack(side="left")
        ttk.Button(bulk, text="Show all places", style="Small.TButton",
                   command=self.map_show_all_places).pack(side="left", padx=(8, 0))
        ttk.Button(bulk, text="Show all roads", style="Small.TButton",
                   command=self.map_show_all_roads).pack(side="left", padx=(6, 0))
        self.map_mark_visited = tk.BooleanVar(value=False)
        ttk.Checkbutton(bulk, text="also mark those places visited", style="Card.TCheckbutton",
                        variable=self.map_mark_visited).pack(side="left", padx=(12, 0))

        # the note goes in before the table so a short window can't push it off
        ttk.Label(page, style="CardFaint.TLabel", justify="left", wraplength=980,
                  text=NOTE).pack(side="bottom", anchor="w", pady=(8, 0))
        self.map_tree = _scrolled_tree(page, columns=("jp", "kind", "state", "visited"),
                                       show="tree headings", selectmode="extended")
        t = self.map_tree
        t.heading("#0", text="Name", anchor="w")
        t.heading("jp", text="Game name", anchor="w")
        t.heading("kind", text="Kind", anchor="w")
        t.heading("state", text="On the map", anchor="w")
        t.heading("visited", text="Visited", anchor="w")
        t.column("#0", width=300)
        t.column("jp", width=190)
        t.column("kind", width=140, stretch=False)
        t.column("state", width=110, stretch=False)
        t.column("visited", width=80, stretch=False)
        t.container.pack(fill="both", expand=True, pady=(8, 0))
        enable_multi_select(t)
        self._style_map_views()

    def _style_map_views(self):
        for key, b in self._map_view_btns.items():
            b.configure(style="Accent.TButton" if key == self.map_view else "Small.TButton")

    def set_map_view(self, view: str):
        self.map_view = view
        self._style_map_views()
        self.refresh_world_map()

    # ------------------------------------------------------------------- read
    def _map_records(self):
        """(records, error) for the shown slot, cached until its payload changes."""
        sv = self.sv
        if sv is None:
            return None, None
        f = self.core_of(sv)             # replaced whenever the payload is edited
        cached = getattr(sv, "_map_cache", None)
        if cached and cached[0] is f:
            return cached[1], cached[2]
        try:
            recs, err = wm.read(f), None
        except (wm.MapError, core.SaveError) as exc:
            recs, err = None, str(exc)
        sv._map_cache = (f, recs, err)
        return recs, err

    def refresh_world_map(self):
        if not hasattr(self, "map_tree"):
            return
        tree = self.map_tree
        keep = set(tree.selection())
        tree.delete(*tree.get_children())
        self._map_rows = {}
        cat = wm.catalog()
        recs, err = self._map_records()
        if cat is None:
            self.map_count.configure(text="map_spots.json is missing — the map can't be named.")
            return
        if recs is None:
            self.map_count.configure(text=err or "Open a save to see its map.")
            return
        tree.tag_configure("flag_unknown", foreground=self.p["muted"])
        q = self.map_search.get().strip().lower()
        listed = total = 0
        if self.map_view == "roads":
            total = len(cat.roads)
            for n, road in enumerate(cat.roads):
                pts = [recs.get(cat.spots[i].key) for i in road]
                name = cat.road_name(road)
                jp = "%s \u2192 %s" % (cat.spots[road[0]].jp, cat.spots[road[-1]].jp)
                if any(r is None for r in pts) or (q and q not in (name + " " + jp).lower()):
                    continue
                on = sum(1 for r in pts if r.state == wm.SHOWN)
                state = ("Shown" if on == len(pts) else "Hidden" if on == 0
                         else "%d of %d" % (on, len(pts)))
                iid = "r%d" % n
                tree.insert("", "end", iid=iid, text=name, tags=() if on else ("flag_unknown",),
                            values=(jp, "%d points" % len(road), state, ""))
                self._map_rows[iid] = ("road", n)
                listed += 1
        else:
            want_places = self.map_view == "places"
            for s in cat.spots:
                rec = recs.get(s.key)
                if rec is None or s.is_place != want_places:
                    continue
                total += 1
                if q and q not in (s.name + " " + s.jp + " " + cat.kind_name(s.kind)).lower():
                    continue
                iid = "s%d" % s.index
                tree.insert("", "end", iid=iid, text=s.name,
                            tags=() if rec.state != wm.HIDDEN else ("flag_unknown",),
                            values=(s.jp if s.jp != s.name else "", cat.kind_name(s.kind),
                                    wm.STATE_NAMES.get(rec.state, "state %d" % rec.state),
                                    {0: "No", 1: "Yes"}.get(rec.visited, str(rec.visited))))
                self._map_rows[iid] = ("spot", s.index)
                listed += 1
        keep = [i for i in keep if tree.exists(i)]
        if keep:
            tree.selection_set(keep)
        pl = [recs[s.key] for s in wm.places(cat) if s.key in recs]
        on = sum(1 for r in pl if r.state != wm.HIDDEN)
        self.map_count.configure(text="%d of %d places on the map · listing %d of %d"
                                      % (on, len(pl), listed, total))

    # ------------------------------------------------------------------ write
    def map_selected(self, state, visited):
        if not self.sv:
            return
        cat = wm.catalog()
        picked: dict[int, tuple] = {}
        roads = bare = 0
        for iid in self.map_tree.selection():
            kind, n = self._map_rows.get(iid, (None, None))
            if kind == "spot":
                picked[cat.spots[n].key] = (state, visited)
            elif kind == "road" and state is not None:
                # showing a road shows the places and junctions it joins; hiding it
                # only hides what belongs to it, never a town or a shared junction
                roads += 1
                pts = wm.road_points(cat, cat.roads[n], whole=state == wm.SHOWN)
                bare += not pts
                for s in pts:
                    picked[s.key] = (state, None)
        if not picked:
            if not self.map_tree.selection():
                msg = "Pick a row first."
            elif roads and bare == roads:
                msg = "That road has no points of its own to hide — it joins two places directly."
            else:
                msg = "A visited mark applies to places, not to roads."
            self.flash(msg, "info")
            return
        parts = []
        if state is not None:
            parts.append("Shown" if state == wm.SHOWN else "Hidden")
        if visited is not None:
            parts.append("marked " + ("visited" if visited else "unvisited"))
        self._map_write(picked, "%s %d map point%s" % (" and ".join(parts), len(picked),
                                                       "" if len(picked) == 1 else "s"))

    def _map_write(self, edits: dict, what: str):
        skipped = {"n": 0}

        def edit(g):
            _changed, skip = wm.apply(g, edits)
            skipped["n"] = max(skipped["n"], skip)
            return g.payload

        if self._core_edit(edit, what) and skipped["n"]:
            self.flash("%s — %d skipped (a layout or value the editor hasn't seen) — "
                       "Ctrl+S to write it." % (what, skipped["n"]), "warn")

    def map_show_all_places(self):
        recs, _ = self._map_records()
        cat = wm.catalog()
        if recs is None or cat is None:
            self.flash("Open a save with a world map first.", "info")
            return
        mark = self.map_mark_visited.get()
        edits = {s.key: (wm.SHOWN, 1 if mark else None) for s in wm.places(cat)
                 if s.key in recs and (recs[s.key].state == wm.HIDDEN
                                       or (mark and recs[s.key].visited == 0))}
        if not edits:
            self.flash("Every place is already on the map.", "info")
            return
        self._map_write(edits, "Showed %d places" % len(edits))

    def map_show_all_roads(self):
        recs, _ = self._map_records()
        cat = wm.catalog()
        if recs is None or cat is None:
            self.flash("Open a save with a world map first.", "info")
            return
        edits = {s.key: (wm.SHOWN, None) for s in wm.network(cat)
                 if s.key in recs and recs[s.key].state == wm.HIDDEN}
        if not edits:
            self.flash("Every junction and road point is already shown.", "info")
            return
        if not messagebox.askyesno(
                "Save editor",
                "Show %d hidden junctions and road points?\n\nThis draws every road the game "
                "has, including ones the story hasn't opened yet. Ctrl+Z undoes it." % len(edits),
                parent=self):
            return
        self._map_write(edits, "Showed %d junctions and road points" % len(edits))


def _scrolled_tree(master, **kw) -> ttk.Treeview:
    """Treeview with its own scrollbar, in a Card frame (same as editor.py)."""
    frame = ttk.Frame(master, style="Card.TFrame")
    tree = ttk.Treeview(frame, **kw)
    sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    tree.container = frame
    return tree
