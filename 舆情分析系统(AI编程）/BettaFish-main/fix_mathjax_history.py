import re
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'report_cache.db')


def fix_html(html: str) -> tuple:
    if not html:
        return html, False
    original = html
    changed = False

    if 'processEscapes' in html:
        html = re.sub(r',?\s*processEscapes\s*:\s*true', '', html)
        html = re.sub(r'\{\s*,', '{', html)
        html = re.sub(r',\s*\}', '}', html)
        html = re.sub(r',\s*,', ',', html)

    if '<body>' in html and 'dark-mode' not in html.split('<body')[1].split('>')[0]:
        html = html.replace('<body>', '<body class="dark-mode">', 1)

    theme_toggle_pattern = re.compile(
        r'<button[^>]*id="theme-toggle-btn"[^>]*>.*?</button>',
        re.DOTALL
    )
    html = theme_toggle_pattern.sub('', html)

    print_btn_pattern = re.compile(
        r'<button[^>]*id="print-btn"[^>]*>.*?</button>',
        re.DOTALL
    )
    html = print_btn_pattern.sub('', html)

    if html != original:
        changed = True

    return html, changed


def fix_db_records():
    if not os.path.exists(DB_PATH):
        print(f"[跳过] 数据库不存在: {DB_PATH}")
        return 0

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        'SELECT rowid, html_content, report_filepath FROM report_cache WHERE html_content IS NOT NULL'
    ).fetchall()

    fixed_count = 0
    for row in rows:
        html = row['html_content']
        rowid = row['rowid'] if 'rowid' in row.keys() else row[0]
        fixed_html, changed = fix_html(html)
        if changed:
            conn.execute(
                'UPDATE report_cache SET html_content = ? WHERE rowid = ?',
                (fixed_html, rowid)
            )
            fixed_count += 1
            print(f"  [DB] 修复 rowid={rowid}")

    conn.commit()
    conn.close()
    return fixed_count


def fix_html_files():
    fixed_count = 0
    for root, dirs, files in os.walk(BASE_DIR):
        for fname in files:
            if not fname.endswith('.html'):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read()
                fixed_content, changed = fix_html(content)
                if changed:
                    with open(fpath, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    fixed_count += 1
                    print(f"  [文件] 修复 {fpath}")
            except Exception as e:
                print(f"  [错误] {fpath}: {e}")
    return fixed_count


def main():
    print("=" * 50)
    print("批量修复历史报告")
    print("修复项：")
    print("  1. 删除 processEscapes: true")
    print("  2. body 添加 dark-mode 类")
    print("  3. 删除旧版切换模式/打印页面按钮")
    print("=" * 50)

    print("\n[1/2] 修复数据库中的 html_content ...")
    db_count = fix_db_records()
    print(f"  数据库修复完成: {db_count} 条记录")

    print("\n[2/2] 修复磁盘上的 .html 文件 ...")
    file_count = fix_html_files()
    print(f"  文件修复完成: {file_count} 个文件")

    print(f"\n总计修复: 数据库 {db_count} 条 + 文件 {file_count} 个")
    print("完成！")


if __name__ == '__main__':
    main()
