"""Small Tk helpers shared by editor.py and editor_advanced.py.

Kept in its own module because editor_advanced.py cannot import editor.py
(the app imports the mixin), and both pages need the same behaviour.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


# id(tree) -> {"ready": bool, "anchor": str | None, "drag": bool}
_STATE: dict[int, dict] = {}
_LAST_TREE: "ttk.Treeview | None" = None


def last_tree() -> "ttk.Treeview | None":
    """The table the user last clicked in (Ctrl+A falls back to it)."""
    tree = _LAST_TREE
    try:
        if tree is not None and tree.winfo_exists():
            return tree
    except tk.TclError:
        pass
    return None


def enable_multi_select(tree: ttk.Treeview) -> None:
    """Ctrl+A selects every row; Shift+click / Shift+drag extends the selection.

    Does nothing for a table that isn't selectmode="extended".

    Tk's Treeview already handles Ctrl+click and Shift+click, but not dragging a
    range, and the app's tables (convoy, classes, masteries, flags) are long
    enough that dragging is worth having.
    """
    # Only tables declared selectmode="extended" take a range. A "browse" table
    # (unit pickers, the inventory slot list, catalogues) drives one form or
    # replaces one thing, so letting it select many would promise edits the
    # buttons can't make.
    try:
        if str(tree.cget("selectmode")) != "extended":
            return
    except tk.TclError:
        return
    key = id(tree)
    if _STATE.get(key, {}).get("ready"):
        return
    state = {"ready": True, "anchor": None, "drag": False}
    _STATE[key] = state

    def visible_rows() -> list[str]:
        out: list[str] = []

        def walk(parent: str):
            for iid in tree.get_children(parent):
                out.append(iid)
                if tree.get_children(iid):
                    walk(iid)

        walk("")
        return out

    def select_all(_e=None):
        rows = visible_rows()
        if rows:
            tree.selection_set(rows)
            tree.focus(rows[-1])
        return "break"

    def select_range(anchor, target):
        rows = visible_rows()
        if anchor not in rows or target not in rows:
            if target:
                tree.selection_set((target,))
            return
        i, j = rows.index(anchor), rows.index(target)
        lo, hi = (i, j) if i <= j else (j, i)
        tree.selection_set(rows[lo:hi + 1])

    def on_press(e):
        global _LAST_TREE
        _LAST_TREE = tree
        row = tree.identify_row(e.y)
        if e.state & 0x0001 and row:                  # Shift held
            anchor = state["anchor"] or row
            state["anchor"] = anchor
            state["drag"] = True
            tree.focus_set()
            select_range(anchor, row)
            return "break"
        state["anchor"] = row
        state["drag"] = False
        return None

    def on_motion(e):
        if not state["drag"]:
            return None
        row = tree.identify_row(e.y)
        if row:
            select_range(state["anchor"], row)
        return "break"

    def on_release(_e):
        state["drag"] = False

    tree.bind("<Control-a>", select_all)
    tree.bind("<Control-A>", select_all)
    tree.bind("<ButtonPress-1>", on_press, add="+")
    tree.bind("<Shift-ButtonPress-1>", on_press, add="+")
    tree.bind("<B1-Motion>", on_motion, add="+")
    tree.bind("<Shift-B1-Motion>", on_motion, add="+")
    tree.bind("<ButtonRelease-1>", on_release, add="+")
