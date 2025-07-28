from app.models.stock_model import Stock

def get_all_stocks():
    """
    모든 Stock 레코드를 조회해서 리스트(dict)로 반환
    """
    stocks = Stock.query.all()
    return [s.to_dict() for s in stocks]
def get_stock_by_code(stock_code):
    """
    stock_code로 Stock 레코드 조회
    """
    stock = Stock.query.filter_by(stock_code=stock_code).first()
    return stock.to_dict() if stock else None

def fetch_stock_by_name(stock_name):
    """
    stock_name으로 Stock 레코드 조회
    """
    stock = Stock.query.filter_by(stock_name=stock_name).first()
    return stock.to_dict() if stock else None