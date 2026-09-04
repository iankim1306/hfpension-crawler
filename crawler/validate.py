# -*- coding: utf-8 -*-
"""수집 결과 검증. 실패하면 발행을 막는다 — 낡은 데이터가 틀린 데이터보다 낫다.

호출: python crawler/validate.py data/pension.json [직전파일]
"""
import json, re, sys, datetime

AGES_MIN = 6          # 55~80세, 5세 단위
PRICES = 12           # 1~12억
SANE_MIN, SANE_MAX = 50, 12000     # 천원. 5만원 ~ 1200만원 밖이면 이상하다
JUMP = 0.20           # 직전 대비 20% 이상 튀면 실패

fails = []
def bad(m): fails.append(m); print("  [FAIL]", m)
def ok(m):  print("  [ok]  ", m)


def check(path, prev_path=None):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)

    if not re.fullmatch(r"20\d\d-\d\d-\d\d", d.get("effective_date", "")):
        bad("기준일자 형식이 이상하다: %r" % d.get("effective_date"))
    else:
        ok("기준일자 %s" % d["effective_date"])

    if d.get("unit") != "천원":
        bad("단위가 천원이 아니다: %r" % d.get("unit"))

    tables = d.get("tables") or {}
    for kind in ("general", "welfare", "officetel"):
        if kind not in tables:
            bad("%s 표가 없다" % kind); continue
        rows = tables[kind]
        if len(rows) < AGES_MIN:
            bad("%s: 나이 %d개 (기대 %d개 이상)" % (kind, len(rows), AGES_MIN))

        ages = sorted(int(a) for a in rows)
        for a in ages:
            vals = rows[str(a)]
            if len(vals) != PRICES:
                bad("%s %d세: 값 %d개 (기대 %d개)" % (kind, a, len(vals), PRICES)); continue
            if any(not (SANE_MIN <= v <= SANE_MAX) for v in vals):
                bad("%s %d세: 범위 밖 값 %s" % (kind, a, vals))
            # 집값이 오르면 수령액은 늘거나 같아야 한다(상한 구간에서 같아진다)
            if any(vals[i] > vals[i+1] for i in range(PRICES-1)):
                bad("%s %d세: 집값이 오르는데 수령액이 줄었다 %s" % (kind, a, vals))

        # 나이가 많을수록 수령액은 늘거나 같아야 한다
        for i in range(len(ages)-1):
            lo, hi = rows[str(ages[i])], rows[str(ages[i+1])]
            if len(lo) == len(hi) == PRICES and any(lo[j] > hi[j] for j in range(PRICES)):
                bad("%s: %d세가 %d세보다 많이 받는다" % (kind, ages[i], ages[i+1]))
        ok("%s 표 %d개 나이 x %d개 집값, 단조성 통과" % (kind, len(rows), PRICES))

    # 직전 발행분 대비 급변 감지 — 페이지가 깨졌는데 형식만 맞는 경우를 잡는다
    if prev_path:
        try:
            with open(prev_path, encoding="utf-8") as f:
                p = json.load(f)
        except Exception:
            print("  [skip] 직전 파일 없음 — 급변 검사 생략"); p = None
        if p:
            same_date = p.get("effective_date") == d.get("effective_date")
            moved = 0
            for kind, rows in tables.items():
                prev = (p.get("tables") or {}).get(kind, {})
                for a, vals in rows.items():
                    if a not in prev or len(prev[a]) != len(vals):
                        continue
                    for x, y in zip(prev[a], vals):
                        if x and abs(y - x) / x > JUMP:
                            moved += 1
            if moved and same_date:
                bad("기준일자가 그대로인데 값이 %d칸이나 20%% 넘게 변했다 — 파싱 오류 의심" % moved)
            elif moved:
                ok("기준일자가 %s -> %s 로 바뀌며 %d칸 변동 (제도 개편으로 보임)"
                   % (p.get("effective_date"), d.get("effective_date"), moved))
            else:
                ok("직전 발행분 대비 급변 없음")

    print()
    print("실패 %d 건" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(check(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
