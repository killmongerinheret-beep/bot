import os

path = r'd:\bot\travelagenntbot\worker_vatican\god_tier_monitor_v2.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

output_lines = []
in_broken_block = False

for i, line in enumerate(lines):
    # Detect the specific broken lines based on content
    if 'try:' in line and i > 0 and 'Use env override or default to 2 visitors' in lines[i-1]:
        output_lines.append('                try:\n')
        in_broken_block = True
    elif in_broken_block and 'env_visitors = int(os.getenv("VATICAN_VISITORS"' in line:
        output_lines.append('                    env_visitors = int(os.getenv("VATICAN_VISITORS", "").strip())\n')
    elif in_broken_block and 'except Exception:' in line:
        output_lines.append('                except Exception:\n')
    elif in_broken_block and 'env_visitors = 0' in line:
        output_lines.append('                    env_visitors = 0\n')
    elif in_broken_block and 'eff_visitors = visitors if' in line:
        output_lines.append('                eff_visitors = visitors if (isinstance(visitors, int) and visitors > 0) else (env_visitors if env_visitors > 0 else 2)\n')
        in_broken_block = False # End of broken block
    else:
        output_lines.append(line)

with open(path + '.fixed', 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

print(f"Fixed file written to {path}.fixed")
