try:
    with open('march2_probe_results.txt', 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    for line in lines:
        if "--- Checking" in line or "MATCH:" in line or "Slots:" in line or "RESULT:" in line:
            print(line.strip())
except Exception as e:
    print(f"Error: {e}")
