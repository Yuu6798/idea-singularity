#!/usr/bin/env python3
"""
auto_repair_runner.py
────────────────────
実行 → エラー検出 → 自己修正 → 再実行 という最小ループ。
「PoR スパイク」の代わりに stderr 出力をトリガにしている。
"""

import subprocess
import re
import pathlib
import datetime

SRC_PATH    = pathlib.Path("target.py")       # 監視対象コード
BACKUP_DIR  = pathlib.Path("repair_backups")  # バックアップ保存先
MAX_ATTEMPT = 2                               # 自動修正の再試行回数


def run_code(path: pathlib.Path):
    """対象スクリプトをサブプロセスで実行し、終了コード・stdout・stderr を返す"""
    proc = subprocess.run(
        ["python", str(path)],
        capture_output=True,
        text=True
    )
    return proc.returncode, proc.stdout, proc.stderr


def extract_error(stderr: str):
    """
    Traceback から (行番号, エラータイプ, メッセージ) を抽出。
    取得できなければ None を返す。
    """
    m = re.search(r'File ".*", line (\d+).*?\n(.+?): (.*)', stderr, re.S)
    if not m:
        return None
    return int(m.group(1)), m.group(2).strip(), m.group(3).strip()


def self_repair(src_text: str, err_line: int, err_type: str, msg: str):
    """
    きわめて素朴な自己修正アルゴリズム：
      - SyntaxError : 該当行をコメントアウト
      - NameError   : 未定義識別子を 'None' に置換
      - その他      : 行末に '# TODO auto-fix' を付与
    """
    lines = src_text.splitlines()

    if err_type == "SyntaxError":
        lines[err_line - 1] = "# ⬇️ 自動コメントアウト\n#" + lines[err_line - 1]

    elif err_type == "NameError":
        undef = re.search(r"name '(\w+)' is not defined", msg)
        if undef:
            target = undef.group(1)
            pattern = re.compile(rf"\b{target}\b")
            for i, l in enumerate(lines):
                if pattern.search(l) and "def " not in l:
                    lines[i] = pattern.sub("None", l) + "  # auto None"
                    break
    else:
        lines[err_line - 1] += "  # TODO auto-fix"

    return "\n".join(lines)


def backup(src: str):
    """修正前コードをタイムスタンプ付きで保存"""
    BACKUP_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    p = BACKUP_DIR / f"{SRC_PATH.stem}_{ts}.bak.py"
    p.write_text(src)


def main():
    attempt = 0

    while attempt < MAX_ATTEMPT:
        code, out, err = run_code(SRC_PATH)

        if code == 0:
            print(out)
            print(f"✅ Success on attempt {attempt + 1}")
            break

        # エラー検出
        print("⚠️  Error detected:\n", err)
        info = extract_error(err)
        if not info:
            print("解析不能なエラー。手動介入が必要です。")
            break

        line_no, e_type, msg = info
        print(f"→ 自動修正を試行 (line {line_no}, {e_type})")

        # バックアップ & 修正
        backup(SRC_PATH.read_text())
        patched = self_repair(SRC_PATH.read_text(), line_no, e_type, msg)
        SRC_PATH.write_text(patched)

        attempt += 1
    else:
        print("❌ 自動修正上限に達しました。バックアップを確認してください。")


if __name__ == "__main__":
    main()