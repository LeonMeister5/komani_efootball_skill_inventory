from __future__ import annotations

from tkinter import ttk

import customtkinter as ctk

from app.services.history_service import HistoryService


class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk, service: HistoryService) -> None:
        super().__init__(master)
        self.title("操作历史")
        self.geometry("950x560")
        self.transient(master)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        columns = ("id", "created_at", "action", "player_item_id", "detail")
        tree = ttk.Treeview(self, columns=columns, show="headings")
        for column, label, width in zip(columns, ("ID", "时间", "操作", "载体 ID", "详情"), (60, 210, 160, 90, 380)):
            tree.heading(column, text=label)
            tree.column(column, width=width, anchor="w")
        for row in service.list_recent():
            tree.insert("", "end", values=[row[column] or "" for column in columns])
        tree.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
        scroll = ttk.Scrollbar(self, orient="vertical", command=tree.yview)
        scroll.grid(row=0, column=1, pady=12, sticky="ns")
        tree.configure(yscrollcommand=scroll.set)

