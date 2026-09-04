# -*- coding: utf-8 -*-
"""한국주택금융공사 주택연금 월지급금 수집.

평범한 HTML 한 장이다. API 키도, JS 렌더링도 필요 없다.
하루 1회, 페이지 하나만 받는다.

출력: data/pension.json (원본 천원 단위 그대로. 만원 변환은 앱이 한다)
"""
import json, os, re, sys, datetime, urllib.request

URL = "https://www.hf.go.kr/ko/sub03/sub03_01_01_02.do"
UA = "Mozilla/5.0 (compatible; hfpension-crawler/1.0; +https://github.com/iankim1306/hfpension-crawler)"

# 🔴 함정: 세 표의 <caption> 이 전부 "일반주택"으로 똑같이 박혀 있다.
#    caption 으로 구분하면 세 번 다 일반주택을 집는다. 반드시 등장 순서로 구분할 것.
KINDS = ["general", "welfare", "officetel"]   # 일반주택 / 노인복지주택 / 주거목적 오피스텔
PRICES = list(range(1, 13))                   # 1억 ~ 12억


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")


def parse(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    m = re.search(r"(20\d\d)\.\s*(\d{1,2})\.\s*(\d{1,2})\.?\s*기준", soup.get_text(" ", strip=True))
    if not m:
        raise RuntimeError("기준일자를 못 찾았다 — 페이지 구조가 바뀌었을 수 있다")
    effective = "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3)))

    tables = soup.find_all("table")
    if len(tables) < 3:
        raise RuntimeError("표가 3개가 아니다 (%d개) — 페이지 구조가 바뀌었다" % len(tables))

    out = {}
    for kind, table in zip(KINDS, tables[:3]):
        body = table.find("tbody")
        if body is None:
            raise RuntimeError("%s: tbody 가 없다" % kind)
        rows = {}
        for tr in body.find_all("tr"):
            cells = [c.get_text(strip=True) for c in tr.find_all(["th", "td"])]
            if not cells:
                continue
            age = re.sub(r"\D", "", cells[0])
            if not age:
                raise RuntimeError("%s: 연령을 못 읽었다 (%r)" % (kind, cells[0]))
            vals = [int(v.replace(",", "")) for v in cells[1:] if re.fullmatch(r"[\d,]+", v)]
            if len(vals) != len(PRICES):
                raise RuntimeError("%s %s세: 값이 %d개다 (기대 %d개)"
                                   % (kind, age, len(vals), len(PRICES)))
            rows[age] = vals
        if not rows:
            raise RuntimeError("%s: 행이 하나도 없다" % kind)
        out[kind] = rows

    return {
        "source": URL,
        "effective_date": effective,
        "unit": "천원",
        "prices_billion": PRICES,
        "payout_type": "종신지급방식 정액형",
        "crawled_at": datetime.datetime.now(datetime.timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tables": out,
    }


def main():
    dest = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    os.makedirs(dest, exist_ok=True)
    data = parse(fetch(URL))

    n = sum(len(v) for v in data["tables"].values())
    print("기준일자 %s, 표 %d개, 행 %d개" % (data["effective_date"], len(data["tables"]), n))

    path = os.path.join(dest, "pension.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
    print("wrote", path)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[FAIL]", e, file=sys.stderr)
        sys.exit(1)
