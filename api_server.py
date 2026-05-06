#!/usr/bin/env python3
"""
资产数据 API 服务
运行: python api_server.py
然后浏览器打开 http://localhost:5000
"""

from flask import Flask, jsonify, request, send_from_directory
import sqlite3
import os
import json

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'assets.db')
WEB_DIR = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')


@app.after_request
def cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ===== API 路由（必须放在静态路由之前）=====

@app.route('/api/assets')
def get_assets():
    """获取所有资产"""
    keyword = request.args.get('q', '')
    
    conn = get_db()
    if keyword:
        rows = conn.execute('''
            SELECT * FROM assets 
            WHERE ip LIKE ? OR domain LIKE ? OR web_title LIKE ? 
               OR company LIKE ? OR province LIKE ?
            ORDER BY found_date DESC
        ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%')).fetchall()
    else:
        rows = conn.execute('SELECT * FROM assets ORDER BY found_date DESC').fetchall()
    conn.close()
    
    return jsonify([dict(r) for r in rows])


@app.route('/api/stats')
def get_stats():
    """获取统计"""
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM assets').fetchone()[0]
    by_platform = conn.execute('''
        SELECT platform, COUNT(*) as cnt FROM assets GROUP BY platform
    ''').fetchall()
    by_province = conn.execute('''
        SELECT province, COUNT(*) as cnt FROM assets GROUP BY province ORDER BY cnt DESC
    ''').fetchall()
    conn.close()
    
    return jsonify({
        'total': total,
        'by_platform': [dict(r) for r in by_platform],
        'by_province': [dict(r) for r in by_province]
    })


@app.route('/api/export/csv')
def export_csv():
    """导出 CSV"""
    import csv
    from io import StringIO
    
    conn = get_db()
    rows = conn.execute('SELECT * FROM assets ORDER BY found_date DESC').fetchall()
    conn.close()
    
    output = StringIO()
    writer = csv.writer(output)
    if rows:
        writer.writerow(rows[0].keys())
        for r in rows:
            writer.writerow(r)
    
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=assets.csv'
    }


@app.route('/api/export/excel')
def export_excel():
    """导出 Excel"""
    import openpyxl
    from io import BytesIO
    
    conn = get_db()
    rows = conn.execute('SELECT * FROM assets ORDER BY found_date DESC').fetchall()
    conn.close()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "资产列表"
    
    # 表头
    headers = ['ID', 'IP', '端口', '域名', '标题', '协议', 'URL', '省份', '城市', '单位', '平台', '发现时间', '最后可见', '来源关键词', '来源页码']
    ws.append(headers)
    
    # 数据行
    for r in rows:
        ws.append([r['id'], r['ip'], r['port'], r['domain'], r['web_title'],
                   r['protocol'], r['url'], r['province'], r['city'], r['company'],
                   r['platform'], r['found_date'], r['last_seen'],
                   r['source_keyword'], r['source_page']])
    
    # 设置列宽
    col_widths = [6, 15, 8, 25, 40, 10, 50, 10, 12, 20, 10, 20, 20, 20, 10]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=assets.xlsx'}
    )


@app.route('/api/detect', methods=['POST'])
def run_detect():
    """触发检测任务"""
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        from core.detector import Detector
        detector = Detector(DB_PATH)
        result = detector.detect_batch(limit=100)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/collect', methods=['POST'])
def run_collect():
    """上传Excel关键词并执行采集"""
    import sys, os, tempfile
    sys.path.insert(0, os.path.dirname(__file__))

    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400

    file = request.files['file']
    if not file.filename.endswith('.xlsx'):
        return jsonify({'error': '只支持 .xlsx 格式'}), 400

    # 保存到临时文件
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename)
    file.save(tmp_path)

    try:
        from core.query_dispatcher import QueryDispatcher
        from core.deduplication import Deduplicator
        import yaml

        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        dispatcher = QueryDispatcher(config_path)
        tasks = dispatcher.load_tasks_from_excel(tmp_path)
        enabled_tasks = [t for t in tasks if t['enabled']]

        if not enabled_tasks:
            return jsonify({'msg': '没有启用的关键词任务', 'new_count': 0})

        deduplicator = Deduplicator(DB_PATH)
        new_total = 0

        for task in enabled_tasks:
            from platforms.hunter import HunterClient
            client = HunterClient(
                api_key=config['hunter']['api_keys'][0],
                page_size=config['scheduler']['page_size'],
                delay=config['scheduler']['delay_between_requests']
            )
            query = task['search_query']
            total = client.get_total(query)
            if total == 0:
                continue
            pages = config['scheduler']['max_pages_per_key']
            results = client.search_range(query, start_page=1, end_page=pages)
            new_assets = deduplicator.filter_new(results, platform='hunter',
                                                  source_keyword=task['keyword'],
                                                  source_page=1)
            new_total += len(new_assets)

        return jsonify({'msg': f'采集完成，共 {len(enabled_tasks)} 个任务', 'new_count': new_total})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        os.remove(tmp_path)
        os.rmdir(tmp_dir)


# ===== 静态文件路由（必须放在 API 路由之后）=====

@app.route('/')
def index():
    return send_from_directory(WEB_DIR, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """支持 Vue Router history 模式"""
    if path == '':
        return send_from_directory(WEB_DIR, 'index.html')
    file_path = os.path.join(WEB_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(WEB_DIR, path)
    return send_from_directory(WEB_DIR, 'index.html')


if __name__ == '__main__':
    print(f"API 服务启动: http://localhost:5000")
    print(f"数据接口: http://localhost:5000/api/assets")
    app.run(host='0.0.0.0', port=5000, debug=True)
