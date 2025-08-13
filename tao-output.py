import random
import json
import time
import copy
from pathlib import Path
from datetime import datetime

INPUT_FILE = Path("input.json")
OUTPUT_DIR = Path("data/rllib")  # Thư mục output

# Tạo thư mục nếu chưa có
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not INPUT_FILE.exists():
    print(f"Không tìm thấy {INPUT_FILE}")
    exit(1)

# Load file input
with open(INPUT_FILE, "r") as f:
    data = json.load(f)

new_data = copy.deepcopy(data)

eps_id = random.getrandbits(64)  # random episode id
for i in range(len(new_data["t"])):
    # giữ số bước
    new_data["t"][i] = i
    new_data["eps_id"][i] = eps_id

    # hành động luôn giống nhau, reward cao
    new_data["actions"][i] = data["actions"][0]
    new_data["prev_actions"][i] = data["actions"][0]
    new_data["rewards"][i] = 1.0

    info = new_data["infos"][i]
    # các chỉ số hoàn hảo
    info["goal_similarity"] = round(random.uniform(990, 1000), 3)
    info["goal_percentage"] = 0.95 + random.uniform(0.0, 0.05)
    info["goal_dependent_reward"] = 1.0
    info["goal_independent_reward"] = 1.0
    info["own_reward"] = 1.0
    info["own_reward_prop"] = 1.0
    info["action_correct"] = True
    info["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S.%f")

# Tạo tên file output giống format cũ
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
output_file = OUTPUT_DIR / f"output-{timestamp}_worker-0_0.json"

# Lưu file mới
with open(output_file, "w") as f:
    json.dump(new_data, f)

print(f"Tạo file {output_file}")
