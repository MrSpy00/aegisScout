"""
Kanban Board View & Centered Modal Dialog Manager for aegisScout GUI.
Provides a modern draggable/actionable multi-column pipeline board.
"""
import customtkinter as ctk
from typing import List, Dict, Callable, Optional, Any
from aegisScout.core.models import Lead


PIPELINE_STAGES = [
    ("new", "Yeni Liderler"),
    ("enriched", "Zenginleştirildi"),
    ("qualified", "Nitelikli"),
    ("contacted", "İletişimde"),
    ("won", "Kazanıldı"),
]


def center_window(window: ctk.CTkToplevel, parent: Optional[ctk.CTk] = None, width: int = 650, height: int = 500):
    """Dynamically center a CTkToplevel modal relative to parent or screen."""
    window.update_idletasks()
    if parent:
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + max(0, (parent_w - width) // 2)
        y = parent_y + max(0, (parent_h - height) // 2)
    else:
        screen_w = window.winfo_screenwidth()
        screen_h = window.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


class KanbanBoardView(ctk.CTkFrame):
    """Kanban Pipeline View for aegisScout."""

    def __init__(
        self,
        master: Any,
        on_status_change_callback: Optional[Callable[[int, str], None]] = None,
        on_lead_click_callback: Optional[Callable[[Lead], None]] = None,
        **kwargs: Any,
    ):
        super().__init__(master, **kwargs)
        self.on_status_change_callback = on_status_change_callback
        self.on_lead_click_callback = on_lead_click_callback
        self.columns: Dict[str, ctk.CTkScrollableFrame] = {}
        self._build_board()

    def _build_board(self):
        self.grid_rowconfigure(1, weight=1)
        
        # Header title
        title_label = ctk.CTkLabel(
            self,
            text="📋 Pipeline Kanban Görünümü",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("gray10", "gray90"),
        )
        title_label.grid(row=0, column=0, columnspan=len(PIPELINE_STAGES), pady=(10, 5), sticky="w", px=10 if hasattr(self, "px") else 10)

        # Create 5 columns
        for idx, (stage_key, stage_title) in enumerate(PIPELINE_STAGES):
            self.grid_columnconfigure(idx, weight=1, uniform="kanban_col")

            # Header box
            hdr_frame = ctk.CTkFrame(self, fg_color=("gray85", "gray25"), corner_radius=8)
            hdr_frame.grid(row=1, column=idx, padx=4, pady=(0, 5), sticky="ew")

            hdr_lbl = ctk.CTkLabel(
                hdr_frame,
                text=stage_title,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=("gray20", "gray80"),
            )
            hdr_lbl.pack(pady=6)

            # Scrollable column content
            col_scroll = ctk.CTkScrollableFrame(self, fg_color=("gray92", "gray18"), corner_radius=8)
            col_scroll.grid(row=2, column=idx, padx=4, pady=4, sticky="nsew")
            self.columns[stage_key] = col_scroll

    def load_leads(self, leads: List[Lead]):
        """Render leads into their corresponding stage column."""
        for col_frame in self.columns.values():
            for child in col_frame.winfo_children():
                child.destroy()

        for lead in leads:
            status = (lead.status or "new").lower().strip()
            # Match status or fallback to 'new'
            target_col_key = status if status in self.columns else "new"
            target_col = self.columns[target_col_key]

            # Lead Card Frame
            card = ctk.CTkFrame(
                target_col,
                fg_color=("white", "gray28"),
                border_color=("gray75", "gray40"),
                border_width=1,
                corner_radius=8,
            )
            card.pack(fill="x", padx=4, pady=4)

            # Business Name
            name_lbl = ctk.CTkLabel(
                card,
                text=lead.business_name or "İsimsiz Lider",
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w",
            )
            name_lbl.pack(fill="x", padx=8, pady=(6, 2))

            # Category / Domain
            info_text = f"🌐 {lead.domain or lead.category or 'Detay yok'}"
            info_lbl = ctk.CTkLabel(
                card,
                text=info_text,
                font=ctk.CTkFont(size=11),
                text_color=("gray40", "gray70"),
                anchor="w",
            )
            info_lbl.pack(fill="x", padx=8, pady=(0, 4))

            # Score & Actions Frame
            bottom_frame = ctk.CTkFrame(card, fg_color="transparent")
            bottom_frame.pack(fill="x", padx=8, pady=(2, 6))

            score = int(lead.score or 0)
            score_color = "#2ef07a" if score >= 75 else "#f39c12" if score >= 50 else "#e74c3c"
            
            score_badge = ctk.CTkLabel(
                bottom_frame,
                text=f"★ {score}",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=score_color,
            )
            score_badge.pack(side="left")

            # Stage Move Buttons
            stage_keys = [s[0] for s in PIPELINE_STAGES]
            curr_idx = stage_keys.index(target_col_key)

            if curr_idx > 0:
                prev_stage = stage_keys[curr_idx - 1]
                btn_prev = ctk.CTkButton(
                    bottom_frame,
                    text="◄",
                    width=22,
                    height=20,
                    fg_color=("gray75", "gray40"),
                    hover_color=("gray60", "gray50"),
                    command=lambda l_id=lead.id, s=prev_stage: self._on_move(l_id, s),
                )
                btn_prev.pack(side="right", padx=2)

            if curr_idx < len(stage_keys) - 1:
                next_stage = stage_keys[curr_idx + 1]
                btn_next = ctk.CTkButton(
                    bottom_frame,
                    text="►",
                    width=22,
                    height=20,
                    fg_color=("#2563eb", "#3b82f6"),
                    hover_color=("#1d4ed8", "#2563eb"),
                    command=lambda l_id=lead.id, s=next_stage: self._on_move(l_id, s),
                )
                btn_next.pack(side="right", padx=2)

    def _on_move(self, lead_id: Optional[int], new_status: str):
        if lead_id and self.on_status_change_callback:
            self.on_status_change_callback(lead_id, new_status)
