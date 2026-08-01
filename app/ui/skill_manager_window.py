from __future__ import annotations

import logging
from collections.abc import Callable
from tkinter import messagebox, simpledialog, ttk

import customtkinter as ctk

from app.services.skill_service import SkillService

LOGGER = logging.getLogger(__name__)


class SkillManagerWindow(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk, service: SkillService, on_changed: Callable[[], None]) -> None:
        super().__init__(master)
        self.service = service
        self.on_changed = on_changed
        self.title("技能管理")
        self.geometry("760x520")
        self.transient(master)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        columns = ("id", "name", "category", "enabled", "available", "reserved", "consumed")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        labels = ("ID", "技能名称", "分类", "状态", "可用", "预留", "已消耗")
        widths = (55, 180, 120, 80, 70, 70, 70)
        for column, label, width in zip(columns, labels, widths):
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, anchor="center" if column != "name" else "w")
        self.tree.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, pady=12, sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, columnspan=2, padx=12, pady=(0, 12), sticky="ew")
        for text, command in (("新增技能", self._add), ("编辑", self._edit), ("启用/禁用", self._toggle), ("关闭", self.destroy)):
            ctk.CTkButton(bar, text=text, width=105, command=command).pack(side="left", padx=4)
        self.tree.bind("<Double-1>", lambda _event: self._edit())
        self.refresh()

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for row in self.service.counts():
            self.tree.insert("", "end", iid=str(row["id"]), values=(row["id"], row["name"], row["category"] or "",
                             "启用" if row["enabled"] else "禁用", row["available"], row["reserved"], row["consumed"]))

    def _selected(self) -> dict[str, object] | None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个技能", parent=self)
            return None
        skill_id = int(selected[0])
        return next(row for row in self.service.counts() if int(row["id"]) == skill_id)

    def _add(self) -> None:
        name = simpledialog.askstring("新增技能", "技能名称：", parent=self)
        if name is None:
            return
        category = simpledialog.askstring("新增技能", "分类（可留空）：", parent=self)
        try:
            self.service.create(name, category)
            self.refresh(); self.on_changed()
        except Exception as exc:
            LOGGER.exception("新增技能失败")
            messagebox.showerror("新增失败", str(exc), parent=self)

    def _edit(self) -> None:
        row = self._selected()
        if not row:
            return
        name = simpledialog.askstring("编辑技能", "技能名称：", initialvalue=str(row["name"]), parent=self)
        if name is None:
            return
        category = simpledialog.askstring("编辑技能", "分类（可留空）：", initialvalue=str(row["category"] or ""), parent=self)
        try:
            self.service.update(int(row["id"]), name, category, bool(row["enabled"]))
            self.refresh(); self.on_changed()
        except Exception as exc:
            LOGGER.exception("编辑技能失败")
            messagebox.showerror("编辑失败", str(exc), parent=self)

    def _toggle(self) -> None:
        row = self._selected()
        if not row:
            return
        try:
            self.service.update(int(row["id"]), str(row["name"]), str(row["category"] or ""), not bool(row["enabled"]))
            self.refresh(); self.on_changed()
        except Exception as exc:
            LOGGER.exception("切换技能状态失败")
            messagebox.showerror("操作失败", str(exc), parent=self)
