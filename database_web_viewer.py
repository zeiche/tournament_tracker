#!/usr/bin/env python3
"""
Database Web Viewer - Interactive SQLite Database Explorer
"""
import sqlite3
import json
from urllib.parse import parse_qs, urlparse

def get_database_schema():
    """Get complete database schema information"""
    conn = sqlite3.connect('tournament_tracker.db')
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    schema = {}
    for table in tables:
        # Get column info for each table
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]

        schema[table] = {
            'columns': [{'name': col[1], 'type': col[2], 'notnull': col[3], 'pk': col[5]} for col in columns],
            'row_count': row_count
        }

    conn.close()
    return schema

def execute_query(query, limit=50):
    """Execute a SQL query safely"""
    try:
        conn = sqlite3.connect('tournament_tracker.db')
        cursor = conn.cursor()

        # Only allow SELECT statements for safety
        if not query.strip().upper().startswith('SELECT'):
            return {'error': 'Only SELECT queries are allowed'}

        cursor.execute(f"{query} LIMIT {limit}")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        conn.close()
        return {
            'columns': columns,
            'rows': rows,
            'count': len(rows)
        }
    except Exception as e:
        return {'error': str(e)}

def get_table_data(table_name, limit=50, offset=0):
    """Get data from a specific table"""
    try:
        conn = sqlite3.connect('tournament_tracker.db')
        cursor = conn.cursor()

        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_count = cursor.fetchone()[0]

        # Get data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        conn.close()
        return {
            'table': table_name,
            'columns': columns,
            'rows': rows,
            'total_count': total_count,
            'showing': len(rows),
            'offset': offset
        }
    except Exception as e:
        return {'error': str(e)}

def generate_database_explorer_html(table_name=None, query=None, offset=0):
    """Generate the database explorer HTML interface"""
    schema = get_database_schema()

    # Handle table viewing or query execution
    result_data = None
    if table_name:
        result_data = get_table_data(table_name, offset=offset)
    elif query:
        result_data = execute_query(query)

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🗄️ Database Explorer - ZiLogo</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }}
        .container {{ max-width: 1600px; margin: 0 auto; }}
        .header {{ background: linear-gradient(45deg, #28a745, #20c997); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .main-content {{ display: grid; grid-template-columns: 300px 1fr; gap: 20px; }}
        .sidebar {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); height: fit-content; }}
        .content {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .table-item {{ padding: 10px; margin: 5px 0; background: #f8f9fa; border-left: 4px solid #28a745; cursor: pointer; border-radius: 4px; }}
        .table-item:hover {{ background: #e9ecef; }}
        .table-item.active {{ background: #d4edda; border-left-color: #155724; }}
        .query-box {{ width: 100%; height: 100px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-family: monospace; }}
        .btn {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }}
        .btn:hover {{ background: #0056b3; }}
        .btn-success {{ background: #28a745; }}
        .btn-success:hover {{ background: #218838; }}
        .table-responsive {{ overflow-x: auto; margin: 20px 0; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: bold; }}
        tr:hover {{ background: #f5f5f5; }}
        .table-meta {{ background: #e9ecef; padding: 10px; border-radius: 4px; margin-bottom: 20px; }}
        .pagination {{ display: flex; gap: 10px; margin: 20px 0; }}
        .error {{ background: #f8d7da; color: #721c24; padding: 15px; border-radius: 4px; margin: 10px 0; }}
        .nav-links {{ text-align: center; margin: 20px 0; }}
        .nav-links a {{ margin: 0 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }}
        .column-type {{ color: #666; font-size: 0.8em; }}
    </style>
    <script>
        function executeQuery() {{
            const query = document.getElementById('queryInput').value;
            if (!query.trim()) return;
            window.location.href = `?query=${{encodeURIComponent(query)}}`;
        }}

        function viewTable(tableName) {{
            window.location.href = `?table=${{tableName}}`;
        }}

        function changePage(table, offset) {{
            window.location.href = `?table=${{table}}&offset=${{offset}}`;
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🗄️ Database Explorer</h1>
            <p>Interactive SQLite database browser for tournament_tracker.db</p>
        </div>

        <div class="main-content">
            <div class="sidebar">
                <h3>📊 Tables ({len(schema)})</h3>"""

    # Sidebar with tables
    for table, info in schema.items():
        active_class = 'active' if table_name == table else ''
        html += f"""
                <div class="table-item {active_class}" onclick="viewTable('{table}')">
                    <strong>{table}</strong><br>
                    <small>{info['row_count']} rows • {len(info['columns'])} columns</small>
                </div>"""

    html += f"""
            </div>

            <div class="content">
                <div style="margin-bottom: 20px;">
                    <h3>🔍 Custom Query</h3>
                    <textarea id="queryInput" class="query-box" placeholder="SELECT * FROM tournaments WHERE...">{query or ''}</textarea><br>
                    <button class="btn btn-success" onclick="executeQuery()">▶️ Execute Query</button>
                </div>"""

    # Display results
    if result_data:
        if 'error' in result_data:
            html += f'<div class="error">❌ Error: {result_data["error"]}</div>'
        else:
            # Table metadata
            if 'table' in result_data:
                table_info = schema[result_data['table']]
                html += f"""
                <div class="table-meta">
                    <strong>📋 Table: {result_data['table']}</strong> |
                    Total rows: {result_data['total_count']} |
                    Showing: {result_data['showing']} |
                    Offset: {result_data['offset']}
                </div>"""

                # Pagination
                if result_data['total_count'] > 50:
                    html += '<div class="pagination">'
                    if result_data['offset'] > 0:
                        html += f'<button class="btn" onclick="changePage(\'{result_data["table"]}\', {result_data["offset"] - 50})">← Previous</button>'
                    if result_data['offset'] + 50 < result_data['total_count']:
                        html += f'<button class="btn" onclick="changePage(\'{result_data["table"]}\', {result_data["offset"] + 50})">Next →</button>'
                    html += '</div>'

            # Data table
            if result_data['columns']:
                html += '<div class="table-responsive"><table>'

                # Headers with column types if available
                html += '<tr>'
                for i, col in enumerate(result_data['columns']):
                    col_type = ''
                    if 'table' in result_data and result_data['table'] in schema:
                        table_cols = schema[result_data['table']]['columns']
                        matching_col = next((tc for tc in table_cols if tc['name'] == col), None)
                        if matching_col:
                            col_type = f'<br><span class="column-type">{matching_col["type"]}</span>'
                    html += f'<th>{col}{col_type}</th>'
                html += '</tr>'

                # Data rows
                for row in result_data['rows']:
                    html += '<tr>'
                    for cell in row:
                        cell_value = str(cell) if cell is not None else '<em>NULL</em>'
                        if len(cell_value) > 100:
                            cell_value = cell_value[:100] + '...'
                        html += f'<td>{cell_value}</td>'
                    html += '</tr>'

                html += '</table></div>'

            html += f'<p><em>📈 Query returned {result_data.get("count", len(result_data.get("rows", [])))} rows</em></p>'

    # Default welcome message
    if not result_data:
        html += f"""
                <div style="text-align: center; padding: 40px; color: #666;">
                    <h3>👋 Welcome to Database Explorer</h3>
                    <p>Select a table from the sidebar or write a custom SQL query to explore the tournament database.</p>
                    <p><strong>Available tables:</strong> {', '.join(schema.keys())}</p>
                </div>"""

    html += f"""
            </div>
        </div>

        <div class="nav-links">
            <a href="https://players.zilogo.com">🏆 Players</a>
            <a href="https://tournaments.zilogo.com">🎯 Tournaments</a>
            <a href="https://orgs.zilogo.com">🏢 Organizations</a>
            <a href="https://editor.zilogo.com">✏️ Editor</a>
            <a href="https://bonjour.zilogo.com">🔍 Services</a>
        </div>

        <div style="text-align: center; margin-top: 30px; color: #666;">
            <p>🗄️ Database Explorer • Interactive SQLite Browser • Read-only access</p>
        </div>
    </div>
</body>
</html>"""

    return html

if __name__ == "__main__":
    # Test the database explorer
    print("🗄️ Testing Database Explorer...")
    html = generate_database_explorer_html()

    with open('database_explorer_test.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("✅ Database explorer generated!")
    print("📊 Schema loaded with all tables")
    print("🔍 Ready for integration")