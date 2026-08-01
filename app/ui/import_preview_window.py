from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tkinter import ttk

import customtkinter as ctk


class ImportPreviewWindow(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk, source: Path, rows: list[dict[str, str]], on_confirm: Callable[[], None]) -> None:
        super().__init__(master)
        self.title("CSV 导入预览")
        self.geometry("920x520")
        self.transient(master)
        self.grab_set()
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=f"文件：{source.name}　共 {len(rows)} 行（下表最多显示前 100 行）").grid(
            row=0, column=0, padx=12, pady=10, sticky="w")
        columns = list(rows[0]) if rows else ["player_name", "skill_name", "status"]
        tree = ttk.Treeview(self, columns=columns, show="headings")
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=130, anchor="w")
        for row in rows[:100]:
            tree.insert("", "end", values=[row.get(column, "") for column in columns])
        tree.grid(row=1, column=0, padx=12, sticky="nsew")
        xscroll = ttk.Scrollbar(self, orient="horizontal", command=tree.xview)
        xscroll.grid(row=2, column=0, padx=12, sticky="ew")
        tree.configure(xscrollcommand=xscroll.set)
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=3, column=0, padx=12, pady=12, sticky="e")
        ctk.CTkButton(bar, text="取消", command=self.destroy, width=90).pack(side="right", padx=4)
        ctk.CTkButton(bar, text="确认导入", width=110, command=lambda: (self.destroy(), on_confirm())).pack(side="right", padx=4)

