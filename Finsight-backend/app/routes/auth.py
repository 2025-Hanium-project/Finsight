from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from ..models.login_model import User
from ..extensions import db, bcrypt
import uuid
from flasgger import swag_from

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
@swag_from({
    'tags': ['Auth'],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'user_name': {'type': 'string'},
                    'login_id': {'type': 'string'}, # 로그인 ID 추가
                    'password': {'type': 'string'},
                    'email': {'type': 'string'}
                },
                'required': ['login_id', 'password']
            }
        }
    ],
    'responses': {
        201: {'description': '회원가입 성공'},
        409: {'description': '이미 존재하는 사용자'}
    }
})
def register():
    data = request.get_json()
    if User.query.filter_by(login_id=data['login_id']).first():
        return jsonify({'message': 'User already exists'}), 409

    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(
        user_id=str(uuid.uuid4()),
        user_name=data['user_name'],
        login_id=data['login_id'],
        password=hashed_pw,
        email=data.get('email')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created'}), 201


@auth_bp.route('/login', methods=['POST'])
@swag_from({
    'tags': ['Auth'],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'login_id': {'type': 'string'},
                    'password': {'type': 'string'}
                },
                'required': ['login_id', 'password']
            }
        }
    ],
    'responses': {
        200: {'description': '로그인 성공'},
        401: {'description': '로그인 실패 (아이디 또는 비밀번호 불일치)'}
    }
})
def login():
    data = request.get_json()
    user = User.query.filter_by(login_id=data['login_id']).first()
    if user and user.check_password(data['password']):
        login_user(user)
        return jsonify({'message': 'Login successful', 'login_id': user.login_id}), 200
    return jsonify({'message': 'Invalid credentials'}), 401


@auth_bp.route('/logout', methods=['POST'])
@swag_from({
    'tags': ['Auth'],
    'security': [{'cookieAuth': []}],
    'responses': {
        200: {'description': '로그아웃 성공'}
    }
})
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out'}), 200


@auth_bp.route('/me', methods=['GET'])
@swag_from({
    'tags': ['Auth'],
    'security': [{'cookieAuth': []}],
    'responses': {
        200: {
            'description': '로그인된 사용자 정보 반환',
            'schema': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string'},
                    'user_name': {'type': 'string'},
                    'login_id': {'type': 'string'},
                    'email': {'type': 'string'}
                }
            }
        }
    }
})
@login_required # 로그인된 사용자만 접근 가능한 메서드 데코레이터
def me():
    return jsonify({
        'user_id': current_user.user_id,
        'user_name': current_user.user_name,
        'login_id': current_user.login_id, 
        'email': current_user.email
    })

# 로그인 ID 중복 확인 엔드포인트 추가(signupPage.js에서 사용)
@auth_bp.route('/check-login-id', methods=['GET'])
@swag_from({
    'tags': ['Auth'],
    'parameters': [
        {
            'name': 'login_id',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': '중복 확인할 로그인 ID'
        }
    ],
    'responses': {
        200: {
            'description': '사용 가능 여부 반환',
            'schema': {
                'type': 'object',
                'properties': {
                    'available': {'type': 'boolean'}
                }
            }
        }
    }
})
def check_login_id():
    login_id = request.args.get('login_id')
    if not login_id:
        return jsonify({'available': False}), 400

    user = User.query.filter_by(login_id=login_id).first()
    return jsonify({'available': user is None}), 200

# 로그인 세션 상태 확인 엔드포인트 추가 (LoginPage.js에서 사용)
@auth_bp.route('/check-session', methods=['GET'])
@swag_from({
    'tags': ['Auth'],
    'responses': {
        200: {
            'description': '세션이 존재함 (로그인 상태)',
            'schema': {
                'type': 'object',
                'properties': {
                    'logged_in': {'type': 'boolean', 'example': True},
                    'login_id': {'type': 'string'}
                }
            }
        },
        401: {
            'description': '세션 없음 (비로그인 상태)',
            'schema': {
                'type': 'object',
                'properties': {
                    'logged_in': {'type': 'boolean', 'example': False}  # ✅ 여기 수정
                }
            }
        }
    }
})
def check_session():
    if current_user.is_authenticated:
        return jsonify({'logged_in': True, 'login_id': current_user.login_id}), 200
    else:
        return jsonify({'logged_in': False}), 401