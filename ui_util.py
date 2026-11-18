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

    Tk's Treeview already handles Ctrl+click and Shift+click, but not dragging a
    range, and the app's tables (convoy, classes, masteries, flags) are long
    enough that dragging is worth having.
    """
    try:
        tree.configure(selectmode="extended")
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


class ScrollableFrame(ttk.Frame):
    """A form viewport with local wheel handling and keyboard focus reveal.

    Native scrolling widgets retain their own wheel bindings. No bind_all
    handler is installed, so scrolling one page cannot move a hidden page.
    """
    def __init__(self, master, *, style='TFrame', padding=0, **kwargs):
        super().__init__(master, style=style, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0,
                                width=1, height=1, yscrollincrement=1, xscrollincrement=1)
        self.vbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.hbar = ttk.Scrollbar(self, orient='horizontal', command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vbar.set, xscrollcommand=self.hbar.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.vbar.grid(row=0, column=1, sticky='ns')
        self.hbar.grid(row=1, column=0, sticky='ew')
        self.hbar.grid_remove()
        self.body = ttk.Frame(self.canvas, style=style, padding=padding)
        self._window = self.canvas.create_window(0, 0, anchor='nw', window=self.body)
        self._style = style
        self._pending = None
        self._wired = set()
        self._tag = 'FormScroll:' + str(self)
        for sequence, callback in (
                ('<MouseWheel>', self._wheel),
                ('<Button-4>', lambda event: self._wheel(event, -3)),
                ('<Button-5>', lambda event: self._wheel(event, 3))):
            self.bind_class(self._tag, sequence, callback)
            self.canvas.bind(sequence, callback)
        self.bind_class(self._tag, '<FocusIn>', self._focus)
        self.body.bind('<Configure>', self._schedule, add='+')
        self.canvas.bind('<Configure>', self._schedule, add='+')
        self.bind('<<ThemeChanged>>', self._theme, add='+')
        self.bind('<Destroy>', self._destroy, add='+')
        self._theme()
        self._schedule()

    def _theme(self, _event=None):
        self.canvas.configure(background=ttk.Style(self).lookup(self._style, 'background') or '#ffffff')

    def _schedule(self, _event=None):
        if self._pending is None:
            self._pending = self.after_idle(self._layout)

    def _layout(self):
        self._pending = None
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        content_width = max(width, self.body.winfo_reqwidth())
        content_height = max(height, self.body.winfo_reqheight())
        self.canvas.itemconfigure(self._window, width=content_width, height=content_height)
        self.canvas.configure(scrollregion=(0, 0, content_width, content_height))
        if content_width > width:
            self.hbar.grid()
        else:
            self.hbar.grid_remove()
            self.canvas.xview_moveto(0)
        self._wire(self.body)

    def _wire(self, widget):
        if isinstance(widget, (ttk.Treeview, tk.Text, tk.Listbox, tk.Canvas, ScrollableFrame)):
            return
        key = str(widget)
        if key not in self._wired:
            widget.bindtags((self._tag, *widget.bindtags()))
            self._wired.add(key)
        for child in widget.winfo_children():
            self._wire(child)

    def _wheel(self, event, steps=None):
        horizontal = bool(event.state & 1)
        view = self.canvas.xview if horizontal else self.canvas.yview
        if view() == (0.0, 1.0):
            return None
        if steps is None:
            delta = getattr(event, 'delta', 0)
            if not delta:
                return None
            steps = -max(1, abs(int(delta / 120))) * (1 if delta > 0 else -1)
        (self.canvas.xview_scroll if horizontal else self.canvas.yview_scroll)(steps * 24, 'units')
        return 'break'

    def _focus(self, event):
        self.see(event.widget)

    def see(self, widget):
        """Keep a tab-focused input/button within the viewport."""
        self.update_idletasks()
        for coordinate, size, origin, view, move, total in (
            (widget.winfo_rooty()-self.body.winfo_rooty(), widget.winfo_height(),
             self.canvas.canvasy(0), self.canvas.winfo_height(), self.canvas.yview_moveto,
             self.body.winfo_height()),
            (widget.winfo_rootx()-self.body.winfo_rootx(), widget.winfo_width(),
             self.canvas.canvasx(0), self.canvas.winfo_width(), self.canvas.xview_moveto,
             self.body.winfo_width())):
            if coordinate < origin:
                move(max(0, coordinate-8)/max(1, total))
            elif coordinate+size > origin+view:
                move(max(0, coordinate+size-view+8)/max(1, total))

    def _destroy(self, event):
        if event.widget is not self:
            return
        if self._pending is not None:
            self.after_cancel(self._pending)
        for sequence in ('<MouseWheel>', '<Button-4>', '<Button-5>', '<FocusIn>'):
            self.unbind_class(self._tag, sequence)
