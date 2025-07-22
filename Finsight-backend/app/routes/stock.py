from flask import Blueprint, jsonify
from app.services.stock_service import *

stock_bp = Blueprint('stock', __name__, url_prefix='/api/stocks')

@stock_bp.route('/', methods=['GET'])
def list_stocks():
    """
    List all stocks
    ---
    tags:
      - Stocks
    responses:
      200:
        description: A list of stocks
        schema:
          type: array
          items:
            type: object
            properties:
              stock_id:
                type: string
                example: "d290f1ee-6c54-4b01-90e6-d701748f0851"
              stock_code:
                type: string
                example: "005930"
              stock_name:
                type: string
                example: "Samsung Electronics"
              created_at:
                type: string
                format: date-time
    """
    data = get_all_stocks()
    return jsonify(data), 200

@stock_bp.route('/<string:stock_code>', methods=['GET'])
def get_stock(stock_code):
    """
    Get one stock by code
    ---
    tags:
      - Stocks
    parameters:
      - in: path
        name: stock_code
        type: string
        required: true
        description: Stock code to lookup
        example: "000660"
    responses:
      200:
        description: Stock found
        schema:
          type: object
          properties:
            stock_id:
              type: string
            stock_code:
              type: string
            stock_name:
              type: string
            created_at:
              type: string
              format: date-time
      404:
        description: Stock not found
    """
    stock = get_stock_by_code(stock_code)
    if stock:
        return jsonify(stock), 200
    else:
        return jsonify({'error': 'Stock not found'}), 404