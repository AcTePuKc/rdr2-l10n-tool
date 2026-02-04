from __future__ import annotations
from pathlib import Path
from core.version import VERSION

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QTextEdit, QSpinBox, QCheckBox, QComboBox, QGroupBox
)

from core.pipeline import (build_master, merge_many_chunks, export_output, 
                           compute_stats_from_master, compute_stats_from_input)
from core.chunking import chunk_entries, write_chunks, write_chunks_index
from core.io_tsv import read_master_tsv
from core.settings import load_settings, save_settings, AppSettings


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.cfg: AppSettings = load_settings()
        self.setWindowTitle(f"RDR2 L10N Tool v{VERSION}")

        self.resize(900, 600)

        self.input_dir = Path(self.cfg.input_dir)
        self.master_path = Path(self.cfg.master_path)
        self.chunks_dir = Path(self.cfg.chunks_dir)
        self.output_dir = Path(self.cfg.output_dir)

        layout = QVBoxLayout(self)

        # Scan / Stats
        scan_row = QHBoxLayout()
        self.btn_scan = QPushButton("Scan & show stats")
        self.btn_scan.clicked.connect(self.on_scan)
        scan_row.addWidget(self.btn_scan)

        self.lbl_scan = QLabel("No scan yet.")
        scan_row.addWidget(self.lbl_scan, 1)
        layout.addLayout(scan_row)

        stats_box = QGroupBox("Stats")
        stats_layout = QVBoxLayout(stats_box)

        self.txt_stats = QTextEdit()
        self.txt_stats.setReadOnly(True)
        self.txt_stats.setMinimumHeight(140)
        stats_layout.addWidget(self.txt_stats)

        layout.addWidget(stats_box)


        # Paths row
        row = QHBoxLayout()
        self.btn_input = QPushButton("Select input folder")
        self.lbl_input = QLabel(str(self.input_dir))
        self.btn_input.clicked.connect(self.pick_input)
        row.addWidget(self.btn_input)
        row.addWidget(self.lbl_input, 1)
        layout.addLayout(row)

        # Build master
        self.btn_build = QPushButton("Build master.tsv")
        self.btn_build.clicked.connect(self.on_build)
        layout.addWidget(self.btn_build)

        # Chunk controls
        chunk_row = QHBoxLayout()
        chunk_row.addWidget(QLabel("Chunk size:"))
        self.spin_chunk = QSpinBox()
        self.spin_chunk.setRange(100, 20000)
        self.spin_chunk.setValue(self.cfg.chunk_size)
        chunk_row.addWidget(self.spin_chunk)
        self.chk_global = QCheckBox("Separate global.txt")
        self.chk_global.setChecked(self.cfg.separate_global)
        chunk_row.addWidget(self.chk_global)
        self.btn_chunk = QPushButton("Create chunks")
        self.btn_chunk.clicked.connect(self.on_chunk)
        chunk_row.addWidget(self.btn_chunk)
        layout.addLayout(chunk_row)

        # Apply chunks
        self.btn_apply = QPushButton("Apply chunks to master")
        self.btn_apply.clicked.connect(self.on_apply)
        layout.addWidget(self.btn_apply)

        # Export
        export_row = QHBoxLayout()

        export_row.addWidget(QLabel("Normalization:"))

        self.cmb_norm = QComboBox()
        self.cmb_norm.addItems(["off", "safe", "strict"])
        self.cmb_norm.setCurrentText(self.cfg.norm_mode)
        export_row.addWidget(self.cmb_norm)

        self.chk_sanity = QCheckBox("Run sanity checks")
        self.chk_sanity.setChecked(self.cfg.run_sanity)
        export_row.addWidget(self.chk_sanity)

        self.chk_partial = QCheckBox("Export only affected files (from selected chunks)")
        self.chk_partial.setToolTip(
                "If enabled, only files referenced by the selected chunk TSV files will be exported."
            )
        export_row.addWidget(self.chk_partial)

        self.btn_export = QPushButton("Export output txt")
        self.btn_export.clicked.connect(self.on_export)
        export_row.addWidget(self.btn_export)

        layout.addLayout(export_row)


        # Log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log, 1)

        self._log("Ready.")
    
    def _save_cfg(self):
        self.cfg.input_dir = str(self.input_dir)
        self.cfg.master_path = str(self.master_path)
        self.cfg.chunks_dir = str(self.chunks_dir)
        self.cfg.output_dir = str(self.output_dir)
        self.cfg.chunk_size = int(self.spin_chunk.value())
        self.cfg.separate_global = bool(self.chk_global.isChecked())
        self.cfg.run_sanity = bool(self.chk_sanity.isChecked())
        self.cfg.norm_mode = str(self.cmb_norm.currentText())
        save_settings(self.cfg)

    def _log(self, msg: str) -> None:
        self.log.append(msg)

    def on_scan(self):
        # Приоритет: ако има master.tsv -> stats от master.
        # Ако няма -> stats от input folder (raw)
        try:
            if self.master_path.exists():
                st = compute_stats_from_master(self.master_path)
                self.lbl_scan.setText("Scanned master.tsv")
            else:
                st = compute_stats_from_input(self.input_dir)
                self.lbl_scan.setText("Scanned input folder (no master.tsv yet)")

            lines = []
            lines.append(st.source_hint)
            lines.append(f"Unique files: {st.unique_files}")
            lines.append(f"Entries: {st.entries}")

            if self.master_path.exists():
                lines.append(f"Translated: {st.translated}")
                lines.append(f"Untranslated (todo): {st.todo}")

            if st.flags_top:
                lines.append("")
                lines.append("Top flags:")
                for k, v in st.flags_top:
                    lines.append(f"  {k}: {v}")

            self.txt_stats.setPlainText("\n".join(lines))
            self._log("Scan complete.")
            self._save_cfg()

        except Exception as e:
            self._log(f"Scan failed: {e}")

    def pick_input(self):
        d = QFileDialog.getExistingDirectory(self, "Select input folder", str(self.input_dir))
        if d:
            self.input_dir = Path(d)
            self.lbl_input.setText(str(self.input_dir))
        self._save_cfg()


    def on_build(self):
        n_entries, n_ignored = build_master(self.input_dir, self.master_path)
        self._log(f"Built master: {n_entries} entries. Ignored files: {n_ignored}.")
        self._log(f"Master path: {self.master_path}")
        self._save_cfg()


    def on_chunk(self):
        entries = read_master_tsv(self.master_path)
        chunks = chunk_entries(entries, self.spin_chunk.value(), separate_global=self.chk_global.isChecked())
        paths = write_chunks(self.chunks_dir, chunks)

        index_path = self.chunks_dir / "chunks_index.tsv"
        write_chunks_index(self.chunks_dir, index_path)

        self._log(f"Chunks created: {len(paths)} in {self.chunks_dir}")
        self._log(f"Chunks index written: {index_path}")
        self._save_cfg()

    def on_apply(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select chunk TSV files",
            str(self.chunks_dir),
            "TSV Files (*.tsv)"
        )
        if not files:
            return

        updated, total, backup_path = merge_many_chunks(
            self.master_path,
            [Path(f) for f in files],
            backup_dir=Path("02_master")  # backup-ите да стоят до мастъра
        )

        self._log(f"Applied chunks: updated {updated} rows out of {total} chunk rows.")
        if backup_path:
            self._log(f"Backup created: {backup_path}")
        self._log(f"Master updated in-place: {self.master_path}")

        self._save_cfg()


    def on_export(self):
        # 1) Избор на output папка
        d = QFileDialog.getExistingDirectory(
            self,
            "Select output folder",
            str(self.output_dir)
        )
        if not d:
            return

        self.output_dir = Path(d)

        # 2) Нормализация режим
        norm = self.cmb_norm.currentText()

        # 3) Partial export (само засегнатите файлове от chunk)
        affected = None
        if self.chk_partial.isChecked():
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select chunk TSV files (for affected-only export)",
                str(self.chunks_dir),
                "TSV Files (*.tsv)"
            )
            if not files:
                self._log("Partial export cancelled: no chunk files selected.")
                return
            affected = [Path(f) for f in files]
            self._log(f"Partial export enabled: using {len(affected)} chunk file(s) to determine affected files.")

        # 4) Реален export
        written, issues = export_output(
            self.master_path,
            self.output_dir,
            normalization_mode=norm,
            use_crlf=True,
            run_sanity=self.chk_sanity.isChecked(),
            affected_only_from_chunks=affected
        )

        # 5) Ако export е блокиран от QA (critical) – казваме ясно и спираме
        if written == 0 and issues and self.chk_sanity.isChecked():
            self._log("Export blocked due to critical QA issues. See 05_reports/qa_report.tsv")
            # показваме само първите 10
            for it in issues[:10]:
                self._log(f"{it.issue_type}: {it.file} {it.key} - {it.details}")
            self._save_cfg()
            return

        # 6) Лог за нормален export
        self._log(f"Exported files: {written} to {self.output_dir}")

        if issues:
            self._log(f"Sanity issues: {len(issues)} (QA report generated)")
            for it in issues[:10]:
                self._log(f"{it.issue_type}: {it.file} {it.key} - {it.details}")

        self._save_cfg()



if __name__ == "__main__":
    app = QApplication([])
    w = App()
    w.show()
    app.exec()
