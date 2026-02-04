# RDR2 L10N Tool

Инструмент за превод на извлечени RDR2 текстови файлове (`.txt`) към един `master.tsv`, работа на чънкове и връщане обратно към `.txt` файлове за мод/loader.

## Какво прави
- Събира всички входни `.txt` (формат `KEY = value`) в `02_master/master.tsv`
- Прави чънкове в `03_chunks/` + `03_chunks/chunks_index.tsv`
- Прилага преводите от чънковете обратно в master (с backup)
- Експортира `.txt` файловете обратно със същите имена (CRLF), с sanity checks и QA report

## Папки
- `01_input_raw_txt/` – тук слагаш извлечените `.txt`
- `02_master/` – `master.tsv` + backups
- `03_chunks/` – `chunk_####.tsv` + `chunks_index.tsv`
- `04_output_txt/` – готови `.txt` за мод
- `05_reports/` – `qa_report.tsv`

## Формат на master/chunk TSV
TSV с 6 колони (разделител TAB):
`file | key | source | translated | note | flags`

Идентификатор за merge/restore: `(file + key)`.

## Правила за превод (важно)
- Не пипай таговете: `~COLOR_RED~`, `~n~`, `~sl:...~`, `~1~` и всякакви `~...~`
- Превеждай само човешкия текст.
- Ако `translated` е празно, при export ще се използва `source`.

## Ползване (EXE)
1) Сложи `.txt` файловете в `01_input_raw_txt/`
2) Стартирай `RDR2_L10N_Tool.exe`
3) Натисни:
   - `Build master.tsv`
   - `Create chunks`
4) Преведи в `03_chunks/chunk_####.tsv` (редактираш колоната `translated`)
5) Натисни `Apply chunks to master`
6) Натисни `Export output txt`

Ако export е блокиран, отвори `05_reports/qa_report.tsv` и оправи редовете с:
- `tag_mismatch`
- `placeholder_mismatch`
- `sl_mismatch`

## Ползване (локално с uv)
- Инсталирай `uv`
- Стартирай `Run.bat`

## Build (GitHub Actions)
Repo-то е настроено да билдва Windows `.exe` автоматично при push/tag.
Готовият файл се намира в Actions Artifacts.
