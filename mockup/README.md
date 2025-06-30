# Frontend Mockup

## 프로젝트 소개

이 저장소는 프론트엔드 목업(Mockup) 프로젝트입니다.
여러 페이지 전환 구조를 테스트하거나, 디자인/기능 시연을 위한 데모 목적의 코드입니다.

## 주요 기능

* 로그인/회원가입/비밀번호 찾기
* 대시보드, 마이페이지, 프로필 수정 등 다양한 화면 목업
* Flask 라우팅을 통한 다중 HTML 페이지 렌더링

## 폴더/파일 구조

```
.
├── app.py                # Flask 서버 실행 파일
├── requirements.txt      # 의존성 패키지 목록
├── /templates            # HTML 파일 폴더 
├── /static               # 정적 파일(CSS, 이미지)
└── README.md
```

## 설치 및 실행 방법

1. **Python 환경 준비**
   Python 3.7 이상이 필요합니다.

2. **필요 라이브러리 설치**

   ```bash
   pip install -r requirements.txt
   ```

3. **서버 실행**

   ```bash
   python app.py
   ```

   서버가 실행되면, 브라우저에서 [http://localhost:5000](http://localhost:5000) 으로 접속하세요.

4. **주요 페이지 라우팅**

   * `/` : 로그인 페이지
   * `/signup` : 회원가입
   * `/findpwd` : 비밀번호 찾기
   * `/index` : 대시보드
   * `/dday` : D-Day 리포트
   * `/dplus1` : D+1 리포트
   * `/detail` : 상세 보기
   * `/mypage` : 마이페이지
   * `/profile_edit` : 프로필 수정

## 사용 기술

* Python 3.x
* Flask
* HTML, CSS, JS

## 참고 및 주의사항

* 본 프로젝트는 화면 목업용으로, 실제 DB나 인증 기능은 구현되어 있지 않습니다.
* zip 파일 압축을 해제한 후, `templates` 폴더가 `app.py`와 같은 경로에 있어야 정상 실행됩니다.
