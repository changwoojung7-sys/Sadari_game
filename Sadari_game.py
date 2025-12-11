from flask import Flask, render_template, request
import random
import sys, os

def resource_path(relative_path):
    """ PyInstaller 빌드 후 리소스 경로 찾아주는 함수 """
    try:
        # PyInstaller가 임시폴더에 풀어놓는 경로
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static")
)

# ----------------------------------------------------
# 1) 정통 아미다쿠지 사다리 생성
# ----------------------------------------------------
def generate_amidakuji(num_players, num_rows=18):
    """
    정통 아미다쿠지 생성: 각 row마다 swapping pair가 0~1개 배치됨.
    절대 병합되지 않는 완전한 permutation 구조.
    """
    ladder = [[False] * (num_players - 1) for _ in range(num_rows)]

    for r in range(num_rows):
        # 각 row에서 만들 수 있는 swap 위치를 랜덤 생성
        cols = list(range(num_players - 1))
        random.shuffle(cols)

        used = set()
        for c in cols:
            # 이전 행과 겹치면 안됨
            if r > 0 and ladder[r - 1][c]:
                continue
            # 같은 row에서 인접 swap 금지
            if c in used or (c - 1) in used or (c + 1) in used:
                continue

            # 30% 확률로 swap 생성
            if random.random() < 0.3:
                ladder[r][c] = True
                used.add(c)

    return ladder


# ----------------------------------------------------
# 2) 특정 플레이어의 도착 열 계산
# ----------------------------------------------------
def traverse(ladder, start_col):
    col = start_col
    num_players = len(ladder[0]) + 1

    for r in range(len(ladder)):
        if col > 0 and ladder[r][col - 1]:
            col -= 1
        elif col < num_players - 1 and ladder[r][col]:
            col += 1

    return col


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        num_players = int(request.form.get("num_players", "0"))
        if num_players < 2 or num_players > 10:
            return render_template("index.html", error="플레이어 수는 2~10명이어야 합니다.")

        # 이름
        names = []
        for i in range(num_players):
            nm = request.form.get(f"name_{i}", "").strip()
            if not nm:
                nm = f"플레이어{i+1}"
            names.append(nm)

        # 벌칙 목록
        rewards_raw = [
            r.strip() for r in request.form.get("rewards", "").split(",") if r.strip()
        ]
        M = len(rewards_raw)

        if M == 0:
            return render_template("index.html", error="벌칙/상품을 최소 1개 입력해야 합니다.")
        if M > num_players:
            return render_template(
                "index.html",
                error=f"벌칙 개수({M})가 플레이어 수({num_players})보다 많습니다."
            )

        # ----------------------------------------------------
        # 정통 아미다쿠지 생성
        # ----------------------------------------------------
        ladder = generate_amidakuji(num_players)
        ladder_rows = len(ladder)

        # 도착 열 계산 → 이는 permutation 구조이므로 반드시 0~N-1 서로 다름
        end_cols = [traverse(ladder, i) for i in range(num_players)]

        # end_cols 는 permutation. ex) [2,0,3,1]
        # 따라서 bottom_rewards 는 해당 위치에 따라 매핑 가능
        bottom_rewards = ["꽝"] * num_players

        # 벌칙은 M개 → 도착 배열의 앞쪽 M명을 당첨
        # 예: end_cols = [2,0,3,1], M=1 → 도착=0 번째 플레이어가 당첨
        indexed = list(enumerate(end_cols))
        indexed.sort(key=lambda x: x[1])  # 도착 지점을 기준으로 정렬

        winners = [idx for idx, _ in indexed[:M]]

        # bottom_rewards 에 벌칙 표시
        for reward_index, (player_idx, end_col) in enumerate(indexed[:M]):
            bottom_rewards[end_col] = rewards_raw[reward_index]

        # 결과 구조
        results = []
        for i in range(num_players):
            results.append({
                "name": names[i],
                "start_col": i,
                "end_col": end_cols[i],
                "reward": rewards_raw[winners.index(i)] if i in winners else "꽝"
            })

        return render_template(
            "result.html",
            names=names,
            num_players=num_players,
            ladder=ladder,
            ladder_rows=ladder_rows,
            bottom_rewards=bottom_rewards,
            results=results,
        )

    return render_template("index.html")

if __name__ == "__main__":
    import threading
    import webbrowser
    from time import sleep

    # 0.5초 후 브라우저 자동 오픈
    def open_browser():
        sleep(0.5)
        webbrowser.open("http://127.0.0.1:5000")

    threading.Thread(target=open_browser).start()

    # Flask 실행
    app.run(debug=False)
