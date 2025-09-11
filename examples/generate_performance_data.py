import json
from datetime import datetime, timedelta, timezone


def generate(n=1000):
    now = datetime(2025, 9, 10, 11, 0, 0, tzinfo=timezone.utc)
    msgs = []
    for i in range(n):
        ts = (now - timedelta(minutes=(i % 30), seconds=(i % 5))).strftime("%Y-%m-%dT%H:%M:%SZ")
        msgs.append({
            "id": f"perf_{i:04d}",
            "content": "Adorei o novo produto!" if i % 4 != 0 else "ruim",
            "timestamp": ts,
            "user_id": f"user_{i%200:03d}",
            "hashtags": ["#produto", "#teste"] if i % 10 == 0 else ["#produto"],
            "reactions": (i % 7) + 1,
            "shares": (i % 3),
            "views": ((i % 25) + 1) * 10,
        })
    return {"messages": msgs, "time_window_minutes": 30}


if __name__ == "__main__":
    data = generate(1000)
    with open("performance_test_1000.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    print("Wrote examples/performance_test_1000.json")

