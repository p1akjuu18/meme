from flask import Flask, render_template, request, jsonify
from database import init_db, get_db
import sqlite3
from datetime import datetime

app = Flask(__name__)

# 初始化数据库
with app.app_context():
    init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/trades', methods=['GET'])
def get_trades():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM trades ORDER BY trade_date DESC')
    trades = cursor.fetchall()
    return jsonify([dict(trade) for trade in trades])

@app.route('/api/trades', methods=['POST'])
def add_trade():
    data = request.json
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        INSERT INTO trades (
            symbol, entry_price, stop_loss, take_profit,
            exit_price, quantity, trade_date, profit_loss,
            notes, status, trader
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['symbol'],
        data['entry_price'],
        data['stop_loss'],
        data['take_profit'],
        data['exit_price'],
        data['quantity'],
        data['trade_date'],
        data['profit_loss'],
        data['notes'],
        data['status'],
        data['trader']
    ))
    
    db.commit()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, port=5001) 