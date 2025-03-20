# 基于 `迭代 + 候选集 + 集合运算` 的 `子图匹配系统` - `前端` (计划生成)

## 构建方法

1. 安装 `uv`
   - MacOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
   - Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - pip: `pip install uv`
   - pipx: `pipx install uv`

2. 安装 `SQLite3`
    - Ubuntu: `sudo apt install sqlite3 libsqlite3-dev`
    - MacOS: `brew install sqlite3`
    - Windows:
      - winget: `winget install -e --id SQLite.SQLite`
      - scoop: `scoop install sqlite`

3. `clone` 本工程

4. 工程根目录下执行: `uv sync`

5. 运行: `uv run main.py`
