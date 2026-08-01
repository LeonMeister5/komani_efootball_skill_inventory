from __future__ import annotations

import logging
from collections.abc import Callable
from tkinter import messagebox

import customtkinter as ctk

from app.config import STATUS_LABELS, STATUS_VALUES
from app.models import PlayerItem, Skill
from app.services.player_service import PlayerService
from app.services.skill_service import SkillService

LOGGER = logging.getLogger(__name__)


class PlayerDialog(ctk.CTkToplevel):
    def __init__(self, master: ctk.CTk, players: PlayerService, skills: SkillService,
                 on_saved: Callable[[], None], item: PlayerItem | None = None) -> None:
        super().__init__(master)
        self.players = players
        self.skill_service = skills
        self.on_saved = on_saved
        self.item = item
        self.title("编辑球员载体" if item else "新增球员载体")
        self.geometry("520x520")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.grid_columnconfigure(1, weight=1)

        self.skills = self._load_skills()
        self.skill_by_label = {self._skill_label(skill): skill for skill in self.skills}
        self.player_entry = self._entry_row(0, "球员姓名")
        self.skill_box = self._combo_row(1, "技能", list(self.skill_by_label))
        self.status_box = self._combo_row(2, "状态", list(STATUS_VALUES))
        self.reserved_entry = self._entry_row(3, "预留目标")
        self.consumed_entry = self._entry_row(4, "消耗目标")
        ctk.CTkLabel(self, text="备注").grid(row=5, column=0, padx=16, pady=10, sticky="ne")
        self.note_text = ctk.CTkTextbox(self, height=100)
        self.note_text.grid(row=5, column=1, padx=(0, 16), pady=10, sticky="ew")

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=6, column=0, columnspan=2, padx=16, pady=18, sticky="e")
        ctk.CTkButton(button_frame, text="取消", width=90, command=self.destroy).pack(side="right", padx=4)
        if not item:
            ctk.CTkButton(button_frame, text="保存并继续录入", width=130,
                          command=lambda: self._save(True)).pack(side="right", padx=4)
        ctk.CTkButton(button_frame, text="保存", width=90, command=lambda: self._save(False)).pack(side="right", padx=4)
        self.status_box.configure(command=lambda _value: self._sync_fields())
        self._fill()
        self._sync_fields()
        self.after(100, self.player_entry.focus_set)

    def _load_skills(self) -> list[Skill]:
        skills = self.skill_service.list_skills(enabled_only=True)
        if self.item and all(skill.id != self.item.skill_id for skill in skills):
            all_skills = self.skill_service.list_skills()
            current = next((skill for skill in all_skills if skill.id == self.item.skill_id), None)
            if current:
                skills.append(current)
        return skills

    @staticmethod
    def _skill_label(skill: Skill) -> str:
        suffix = "（已禁用）" if not skill.enabled else ""
        return f"{skill.name}{suffix}"

    def _entry_row(self, row: int, label: str) -> ctk.CTkEntry:
        ctk.CTkLabel(self, text=label).grid(row=row, column=0, padx=16, pady=10, sticky="e")
        entry = ctk.CTkEntry(self)
        entry.grid(row=row, column=1, padx=(0, 16), pady=10, sticky="ew")
        return entry

    def _combo_row(self, row: int, label: str, values: list[str]) -> ctk.CTkComboBox:
        ctk.CTkLabel(self, text=label).grid(row=row, column=0, padx=16, pady=10, sticky="e")
        box = ctk.CTkComboBox(self, values=values, state="readonly")
        box.grid(row=row, column=1, padx=(0, 16), pady=10, sticky="ew")
        return box

    def _fill(self) -> None:
        if self.item:
            self.player_entry.insert(0, self.item.player_name)
            selected = next((label for label, skill in self.skill_by_label.items() if skill.id == self.item.skill_id), "")
            self.skill_box.set(selected)
            self.status_box.set(STATUS_LABELS[self.item.status])
            self.reserved_entry.insert(0, self.item.reserved_for or "")
            self.consumed_entry.insert(0, self.item.consumed_for or "")
            self.note_text.insert("1.0", self.item.note or "")
        else:
            if self.skills:
                self.skill_box.set(next(iter(self.skill_by_label)))
            self.status_box.set(STATUS_LABELS["available"])

    def _sync_fields(self) -> None:
        status = STATUS_VALUES.get(self.status_box.get(), "available")
        self.reserved_entry.configure(state="normal" if status == "reserved" else "disabled")
        self.consumed_entry.configure(state="normal" if status == "consumed" else "disabled")

    def _save(self, keep_open: bool) -> None:
        try:
            skill = self.skill_by_label.get(self.skill_box.get())
            if not skill:
                raise ValueError("请先在“技能管理”中添加并选择技能")
            values = dict(
                player_name=self.player_entry.get(), skill_id=skill.id,
                status=STATUS_VALUES.get(self.status_box.get(), "available"),
                reserved_for=self.reserved_entry.get(), consumed_for=self.consumed_entry.get(),
                note=self.note_text.get("1.0", "end").strip(),
            )
            if self.item:
                self.players.update(self.item.id, **values)
            else:
                self.players.create(**values)
            self.on_saved()
            if keep_open:
                self.player_entry.delete(0, "end")
                self.reserved_entry.configure(state="normal")
                self.reserved_entry.delete(0, "end")
                self.consumed_entry.configure(state="normal")
                self.consumed_entry.delete(0, "end")
                self.note_text.delete("1.0", "end")
                self.status_box.set(STATUS_LABELS["available"])
                self._sync_fields()
                self.player_entry.focus_set()
            else:
                self.destroy()
        except Exception as exc:
            LOGGER.exception("保存球员载体失败")
            messagebox.showerror("保存失败", str(exc), parent=self)

