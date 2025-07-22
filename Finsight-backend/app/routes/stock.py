from flask import Blueprint, jsonify
from app.services.stock_service import *

stock_bp = Blueprint('stock', __name__, url_prefix='/stocks')

@stock_bp.route('/', methods=['GET'])
def list_stocks():
    """
    GET /stocks
    finsight-database.stock 테이블의 모든 레코드를 JSON 배열로 반환
    """
    data = get_all_stocks()
    return jsonify(data), 200

@stock_bp.route('/<string:stock_code>', methods=['GET'])
def get_stock(stock_code):
    """
    GET /stocks/<stock_code>
    stock_code로 finsight-database.stock 테이블의 레코드를 조회하여 JSON으로 반환
    """
    stock = get_stock_by_code(stock_code)
    if stock:
        return jsonify(stock), 200
    else:
        return jsonify({'error': 'Stock not found'}), 404