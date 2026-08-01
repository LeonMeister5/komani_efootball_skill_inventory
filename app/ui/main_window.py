from __future__ import annotations

import logging
import threading
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

import customtkinter as ctk

from app.config import APP_NAME, STATUS_LABELS, STATUS_VALUES, WINDOW_SIZE
from app.db.connection import Database
from app.models import PlayerItem
from app.paths import AppPaths
from app.services.backup_service import BackupService
from app.services.history_service import HistoryService
from app.services.import_export_service import ImportExportService, ImportResult
from app.services.player_service import PlayerService
from app.services.settings_service import SettingsService
from app.services.skill_service import SkillService
from app.services.statistics_service import StatisticsService
from app.ui.history_window import HistoryWindow
from app.ui.import_preview_window import ImportPreviewWindow
from app.ui.player_dialog import PlayerDialog
from app.ui.skill_manager_window import SkillManagerWindow

LOGGER = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    COLUMNS = ("id", "player_name", "skill_name", "status", "reserved_for", "consumed_for", "created_at", "consumed_at", "note")

    def __init__(self, database: Database, paths: AppPaths) -> None:
        self.settings = SettingsService(database)
        ctk.set_appearance_mode(self.settings.get("theme", "System"))
        super().__init__()
        self.database = database
        self.paths = paths
        self.players = PlayerService(database)
        self.skills = SkillService(database)
        self.statistics = StatisticsService(database)
        self.backups = BackupService(database, paths.backups)
        self.csv_service = ImportExportService(database)
        self.history = HistoryService(database)
        self.title(APP_NAME)
        self.geometry(WINDOW_SIZE)
        self.minsize(900, 600)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._sort_column = "id"
        self._sort_reverse = True
        self._build_filters()
        self._build_actions()
        self._build_table()
        self._build_status()
        self.refresh_all()

    def _build_filters(self) -> None:
        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(frame, text="搜索").grid(row=0, column=0, padx=(12, 6), pady=10)
        self.search_entry = ctk.CTkEntry(frame, placeholder_text="输入球员姓名或技能名称")
        self.search_entry.grid(row=0, column=1, padx=6, pady=10, sticky="ew")
        self.search_entry.bind("<KeyRelease>", lambda _event: self.refresh_table())
        ctk.CTkLabel(frame, text="技能").grid(row=0, column=2, padx=(12, 4))
        self.skill_filter = ctk.CTkComboBox(frame, values=["全部技能"], state="readonly", width=170,
                                            command=lambda _value: self.refresh_table())
        self.skill_filter.grid(row=0, column=3, padx=6)
        self.skill_filter.set("全部技能")
        ctk.CTkLabel(frame, text="状态").grid(row=0, column=4, padx=(12, 4))
        self.status_filter = ctk.CTkComboBox(frame, values=["全部状态", *STATUS_VALUES], state="readonly", width=120,
                                             command=lambda _value: self.refresh_table())
        self.status_filter.grid(row=0, column=5, padx=6)
        self.status_filter.set("全部状态")
        self.theme_box = ctk.CTkComboBox(frame, values=["System", "Light", "Dark"], state="readonly", width=95,
                                         command=self._change_theme)
        self.theme_box.grid(row=0, column=6, padx=12)
        self.theme_box.set(self.settings.get("theme", "System"))

    def _build_actions(self) -> None:
        frame = ctk.CTkScrollableFrame(self, height=42, orientation="horizontal")
        frame.grid(row=1, column=0, padx=12, pady=6, sticky="ew")
        actions = (
            ("新增", self._add), ("编辑", self._edit), ("删除", self._delete),
            ("标记预留", self._reserve), ("标记已消耗", self._consume), ("恢复为可用", self._restore),
            ("技能管理", self._manage_skills), ("导入 CSV", self._import_csv), ("导出 CSV", self._export_csv),
            ("立即备份", self._backup), ("操作历史", self._history),
        )
        for text, command in actions:
            ctk.CTkButton(frame, text=text, width=100, command=command).pack(side="left", padx=3, pady=2)

    def _build_table(self) -> None:
        frame = ctk.CTkFrame(self)
        frame.grid(row=2, column=0, padx=12, pady=6, sticky="nsew")
        frame.grid_rowconfigure(0, weight=1); frame.grid_columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(frame, columns=self.COLUMNS, show="headings", selectmode="browse")
        labels = ("ID", "球员姓名", "技能", "状态", "预留目标", "消耗目标", "创建时间", "消耗时间", "备注")
        widths = (55, 140, 140, 80, 125, 125, 175, 175, 200)
        for column, label, width in zip(self.COLUMNS, labels, widths):
            self.tree.heading(column, text=label, command=lambda col=column: self._sort_by(col))
            self.tree.column(column, width=width, minwidth=50, anchor="center" if column in {"id", "status"} else "w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        vscroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        hscroll.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        self.tree.bind("<Double-1>", lambda _event: self._edit())

    def _build_status(self) -> None:
        self.status_label = ctk.CTkLabel(self, text="", anchor="w")
        self.status_label.grid(row=3, column=0, padx=14, pady=(2, 10), sticky="ew")

    def refresh_all(self) -> None:
        self._refresh_skill_filter()
        self.refresh_table()

    def _refresh_skill_filter(self) -> None:
        current = self.skill_filter.get()
        self.skill_map = {skill.name: skill.id for skill in self.skills.list_skills()}
        values = ["全部技能", *self.skill_map]
        self.skill_filter.configure(values=values)
        self.skill_filter.set(current if current in values else "全部技能")

    def refresh_table(self) -> None:
        try:
            skill_id = self.skill_map.get(self.skill_filter.get())
            status = STATUS_VALUES.get(self.status_filter.get())
            rows = self.players.search(self.search_entry.get(), skill_id, status)
            rows = sorted(rows, key=self._sort_key, reverse=self._sort_reverse)
            self.tree.delete(*self.tree.get_children())
            for item in rows:
                self.tree.insert("", "end", iid=str(item.id), values=(item.id, item.player_name, item.skill_name,
                                 STATUS_LABELS[item.status], item.reserved_for or "", item.consumed_for or "",
                                 item.created_at, item.consumed_at or "", item.note or ""))
            stats = self.statistics.calculate()
            low = self.statistics.low_stock_skills()
            low_text = "；低库存技能：" + "、".join(low[:8]) + ("…" if len(low) > 8 else "") if low else ""
            self.status_label.configure(text=(f"可用 {stats.available}　预留 {stats.reserved}　已消耗 {stats.consumed}　"
                f"技能 {stats.skill_count} 种　累计成本 {stats.total_cost_gp:,} GP　可用价值 {stats.available_value_gp:,} GP{low_text}"))
        except Exception as exc:
            self._show_error("刷新数据失败", exc)

    def _sort_key(self, item: PlayerItem) -> tuple[bool, object]:
        value = getattr(item, self._sort_column)
        return value is None, value or ""

    def _sort_by(self, column: str) -> None:
        if self._sort_column == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column, self._sort_reverse = column, False
        self.refresh_table()

    def _selected_id(self) -> int | None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一条球员载体记录", parent=self)
            return None
        return int(selected[0])

    def _add(self) -> None:
        if not self.skills.list_skills(enabled_only=True):
            messagebox.showinfo("请先添加技能", "新增球员载体前，请先在“技能管理”中添加技能。", parent=self)
            self._manage_skills(); return
        PlayerDialog(self, self.players, self.skills, self.refresh_all)

    def _edit(self) -> None:
        item_id = self._selected_id()
        if item_id is not None:
            item = self.players.get(item_id)
            if item:
                PlayerDialog(self, self.players, self.skills, self.refresh_all, item)

    def _delete(self) -> None:
        item_id = self._selected_id()
        if item_id is None or not messagebox.askyesno("确认删除", "确定永久删除所选记录吗？完整快照会保留在操作历史中。", parent=self):
            return
        try:
            self.players.delete(item_id); self.refresh_all()
        except Exception as exc:
            self._show_error("删除失败", exc)

    def _reserve(self) -> None:
        item_id = self._selected_id()
        if item_id is None: return
        target = simpledialog.askstring("标记预留", "预留目标（可留空）：", parent=self)
        if target is not None: self._change_status(item_id, "reserved", target)

    def _consume(self) -> None:
        item_id = self._selected_id()
        if item_id is None: return
        target = simpledialog.askstring("标记已消耗", "消耗目标（可留空）：", parent=self)
        if target is not None: self._change_status(item_id, "consumed", target)

    def _restore(self) -> None:
        item_id = self._selected_id()
        if item_id is not None: self._change_status(item_id, "available")

    def _change_status(self, item_id: int, status: str, target: str | None = None) -> None:
        try:
            self.players.change_status(item_id, status, target); self.refresh_all()
        except Exception as exc:
            self._show_error("状态更新失败", exc)

    def _manage_skills(self) -> None:
        SkillManagerWindow(self, self.skills, self.refresh_all)

    def _history(self) -> None:
        HistoryWindow(self, self.history)

    def _export_csv(self) -> None:
        default = self.paths.exports / "efootball_inventory.csv"
        target = filedialog.asksaveasfilename(parent=self, title="导出 CSV", initialdir=default.parent,
                                              initialfile=default.name, defaultextension=".csv", filetypes=[("CSV 文件", "*.csv")])
        if not target: return
        try:
            count = self.csv_service.export_csv(Path(target))
            messagebox.showinfo("导出完成", f"已导出 {count} 条记录。\n{target}", parent=self)
        except Exception as exc:
            self._show_error("导出失败", exc)

    def _import_csv(self) -> None:
        source = filedialog.askopenfilename(parent=self, title="选择 CSV", filetypes=[("CSV 文件", "*.csv")])
        if not source: return
        try:
            rows = self.csv_service.preview_csv(Path(source))
            ImportPreviewWindow(self, Path(source), rows, lambda: self._run_import(Path(source)))
        except Exception as exc:
            self._show_error("CSV 校验失败", exc)

    def _run_import(self, source: Path) -> None:
        try:
            self.backups.create_backup(self.settings.get_int("backup_keep_count", 20))
        except Exception as exc:
            self._show_error("导入前备份失败", exc); return
        self.status_label.configure(text="正在导入 CSV…")
        threading.Thread(target=self._import_worker, args=(source,), daemon=True).start()

    def _import_worker(self, source: Path) -> None:
        try:
            result = self.csv_service.import_csv(source)
            self.after(0, lambda: self._import_finished(result))
        except Exception as exc:
            LOGGER.exception("CSV 导入失败")
            self.after(0, lambda error=exc: self._show_error("导入失败", error))

    def _import_finished(self, result: ImportResult) -> None:
        self.refresh_all()
        details = "\n".join(f"第 {error.row_number} 行：{error.reason}" for error in result.errors[:20])
        messagebox.showinfo("导入完成", f"成功 {result.success_count} 条，失败 {len(result.errors)} 条。"
                            + (f"\n\n错误详情：\n{details}" if details else ""), parent=self)

    def _backup(self) -> None:
        try:
            path = self.backups.create_backup(self.settings.get_int("backup_keep_count", 20))
            messagebox.showinfo("备份完成", f"数据库已安全备份至：\n{path}", parent=self)
        except Exception as exc:
            self._show_error("备份失败", exc)

    def _change_theme(self, value: str) -> None:
        ctk.set_appearance_mode(value)
        self.settings.set("theme", value)

    def _show_error(self, title: str, error: Exception) -> None:
        LOGGER.error(title, exc_info=(type(error), error, error.__traceback__))
        messagebox.showerror(title, f"{error}\n\n详细信息已写入本地日志。", parent=self)
