# hfpension-crawler

한국주택금융공사 **주택연금 월지급금** 수집기. 주택연금 계산기 앱이 읽는 데이터를 만든다.

## 🔴 이 저장소는 PUBLIC 이어야 한다

PRIVATE 이면 GitHub Actions 실행 시간이 계정 무료 분에서 깎인다.
PUBLIC 이면 Actions 가 무제한 무료다. **비용 0을 지키는 조건이 이것 하나다.**
(같은 이유로 `finrate-crawler` 는 private 이라 과금되고 있다.)

공개돼도 문제 없다. 공사가 공시하는 공개 정보를 그대로 옮길 뿐이고, 키나 비밀값을 쓰지 않는다.

## 앱이 읽는 주소

```
https://raw.githubusercontent.com/iankim1306/hfpension-crawler/main/data/pension.json
```

## 데이터 형식

```jsonc
{
  "source": "https://www.hf.go.kr/ko/sub03/sub03_01_01_02.do",
  "effective_date": "2026-03-01",   // 공사 공시 기준일
  "unit": "천원",                    // 🔴 원본 그대로. 만원 변환은 앱이 한다 (값 // 10, 내림)
  "prices_billion": [1, 2, ..., 12], // 집값 1억~12억
  "payout_type": "종신지급방식 정액형",
  "crawled_at": "2026-09-04T...Z",
  "tables": {
    "general":   { "55": [12개], "60": [...], ... "80": [...] },  // 일반주택
    "welfare":   { ... },                                          // 노인복지주택
    "officetel": { ... }                                           // 주거목적 오피스텔
  }
}
```

`general["70"][8]` = 일반주택 70세 9억원 = `2770` 천원 = **월 277만원**.

## 함정

- **세 표의 `<caption>` 이 전부 "일반주택" 으로 똑같이 박혀 있다.**
  caption 으로 고르면 세 번 다 일반주택을 집는다. 반드시 **등장 순서**로 구분한다.
- 단위는 천원이다. 만원으로 바꿀 땐 `// 10` (내림). 468천원 → 46만원.
- 주택연금 표는 **1년에 한 번 정도만** 바뀐다. 커밋이 거의 안 생겨서
  60일 무활동 시 GitHub이 스케줄을 끄는 규칙에 걸리기 쉽다 → `Keepalive` 스텝이 그걸 막는다.

## 검증

`crawler/validate.py` 가 통과해야만 커밋한다. 잡는 것:

- 기준일자 형식, 단위 표기
- 표 3개 존재, 각 6개 나이 x 12개 집값
- 값이 상식 범위(5만원~1200만원) 안인지
- 집값이 오르는데 수령액이 줄지 않는지
- 나이가 많은데 수령액이 적지 않는지
- **기준일자는 그대로인데 값만 20% 넘게 튀면 실패** (페이지가 깨졌는데 형식만 맞는 경우)

검증 실패 = 발행 안 함. 낡은 데이터가 틀린 데이터보다 낫다.

## 수동 실행

```bash
pip install beautifulsoup4
python crawler/crawl.py
python crawler/validate.py data/pension.json
```
