# app/routes/stock_direct.py

from flask import Blueprint, jsonify, request
from pykrx import stock as krx
from datetime import datetime, timedelta
from app.services.market_extra import get_kor_treasury_3y, get_usdkrw_realtime


direct_bp = Blueprint('stock_direct', __name__, url_prefix='/api/direct')

@direct_bp.route('/<string:stock_code>/ohlcv', methods=['GET'])
def direct_ohlcv(stock_code):
    """
    종목 코드에 해당하는 종목 ohlcv 정보
    ---
    tags:
      - DirectStocks
    parameters:
      - in: path
        name: stock_code
        type: string
        required: true
        description: 조회할 종목 코드
        example: "005930"
      - in: query
        name: start_date
        type: string
        required: false
        description: 조회 시작일 (YYYYMMDD). 지정 없으면 1년 전부터.
        example: "20200101"
      - in: query
        name: end_date
        type: string
        required: false
        description: 조회 종료일 (YYYYMMDD). 지정 없으면 오늘까지.
        example: "20250722"
    responses:
      200:
        description: OHLCV 및 시가총액 데이터 배열
        schema:
          type: array
          items:
            type: object
            properties:
              date:
                type: string
                format: date
              open:
                type: number
              high:
                type: number
              low:
                type: number
              close:
                type: number
              volume:
                type: integer
              market_cap:
                type: number
                description: 시가총액
      404:
        description: 데이터 없음 또는 종목 코드 오류
      500:
        description: PyKRX 호출 오류
    """
    start = request.args.get('start_date')
    end   = request.args.get('end_date')

    # 기본 기간: 1년 전 ~ 오늘
    if not start:
        start = (datetime.today().replace(year=datetime.today().year - 1)
                 .strftime("%Y%m%d"))
    if not end:
        end = datetime.today().strftime("%Y%m%d")

    try:
        # OHLCV 조회
        df = krx.get_market_ohlcv_by_date(start, end, stock_code)
        # 시가총액 조회 (ALL 시장, 기간 동일)
        cap_df = krx.get_market_cap_by_date(start, end, stock_code)
    except Exception as e:
        return jsonify({"error": f"PyKRX 조회 실패: {e}"}), 500

    if df.empty:
        return jsonify({"error": "조회된 데이터가 없습니다."}), 404

    # DataFrame 전처리
    df.reset_index(inplace=True)
    df.rename(columns={
        "날짜": "date",
        "시가": "open",
        "고가": "high",
        "저가": "low",
        "종가": "close",
        "거래량": "volume"
    }, inplace=True)

    # 종목명 조회
    stock_name = krx.get_market_ticker_name(stock_code)


    ohlcv_list = []
    latest_market_cap = None
    for row in df.itertuples():
        date_str = row.date.strftime("%Y-%m-%d")
        market_cap = None
        try:
            market_cap = float(cap_df.at[date_str, '시가총액'])
        except Exception:
            market_cap = None
        # 최신 날짜의 market_cap 저장
        if latest_market_cap is None or row.date > latest_date:
            latest_market_cap = market_cap
            latest_date = row.date
        ohlcv_list.append({
            "date": date_str,
            "open": float(row.open),
            "high": float(row.high),
            "low":  float(row.low),
            "close":float(row.close),
            "volume": int(row.volume)
        })

    result = {
        "stock_name": stock_name,
        "market_cap": latest_market_cap,
        "ohlcv": ohlcv_list
    }
    return jsonify(result), 200


market_bp = Blueprint('market_direct', __name__, url_prefix='/api/direct/market')

@market_bp.route('/today', methods=['GET'])
def get_today_market_index():
    """
    오늘 코스피 / 코스닥 지수, 원/달러 환율, 국채 3년물 금리 정보 (전일 대비 등락률)
    ---
    tags:
      - DirectMarket
    responses:
      200:
        description: 오늘 주요 시장 지표 정보
        schema:
          type: object
          properties:
            date:
              type: string
              format: date
            kospi:
              type: object
              properties:
                close: { type: number, description: 종가 }
                change: { type: number, description: 전일 대비 절대 변화량 }
                change_rate: { type: number, description: 전일 대비 등락률(%) }
            kosdaq:
              type: object
              properties:
                close: { type: number, description: 종가 }
                change: { type: number, description: 전일 대비 절대 변화량 }
                change_rate: { type: number, description: 전일 대비 등락률(%) }
            usdkrw:
              type: object
              properties:
                today: { type: number, description: 현재 원/달러 환율 }
                change: { type: number, description: 전일 대비 절대 변화량 (원) }
                change_rate: { type: number, description: 전일 대비 등락률(%) }
            bond_3y:
              type: object
              properties:
                today: { type: number, description: 현재 국채 3년물 금리(%) }
                change: { type: number, description: 전일 대비 절대 변화량(bp) }
                change_rate: { type: number, description: 전일 대비 등락률(%) }
      404:
        description: 데이터 없음
      500:
        description: 조회 실패
    """

    try:
        today = datetime.today()
        # 전일 데이터까지 포함 (주말·공휴일 보정 위해 7일 전부터 조회)
        start_date = (today - timedelta(days=7)).strftime("%Y%m%d")
        end_date = today.strftime("%Y%m%d")

        # 코스피 / 코스닥 지수 조회
        kospi_df = krx.get_index_ohlcv_by_date(start_date, end_date, "1001")  # KOSPI
        kosdaq_df = krx.get_index_ohlcv_by_date(start_date, end_date, "2001") # KOSDAQ

        if kospi_df.empty or kosdaq_df.empty:
            return jsonify({"error": "지수 데이터가 없습니다."}), 404

        # 최신(오늘) & 전일 데이터
        kospi_today = kospi_df.iloc[-1]
        kospi_prev = kospi_df.iloc[-2]

        kosdaq_today = kosdaq_df.iloc[-1]
        kosdaq_prev = kosdaq_df.iloc[-2]

        # KOSPI
        kospi_close = float(kospi_today['종가'])
        kospi_change = kospi_close - float(kospi_prev['종가'])
        kospi_change_rate = round((kospi_change / float(kospi_prev['종가'])) * 100, 2)

        # KOSDAQ
        kosdaq_close = float(kosdaq_today['종가'])
        kosdaq_change = kosdaq_close - float(kosdaq_prev['종가'])
        kosdaq_change_rate = round((kosdaq_change / float(kosdaq_prev['종가'])) * 100, 2)

        usdkrw_info = get_usdkrw_realtime()
        bond3y_info = get_kor_treasury_3y()

        result = {
            "date": today.strftime("%Y-%m-%d"),
            "kospi": {
                "close": kospi_close,
                "change": kospi_change,
                "change_rate": kospi_change_rate
            },
            "kosdaq": {
                "close": kosdaq_close,
                "change": kosdaq_change,
                "change_rate": kosdaq_change_rate
            },
            "usdkrw" : usdkrw_info,
            "bond3y_info" : bond3y_info, 
        }
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": f"지수 조회 실패: {e}"}), 500

