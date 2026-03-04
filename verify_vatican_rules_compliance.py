#!/usr/bin/env python3
"""
Vatican Bot Rules Compliance Checker
=====================================
Verifies that all Vatican bot code follows the mandatory rules from
.kiro/steering/VATICAN_BOT_RULES.md

Run: python verify_vatican_rules_compliance.py
"""

import os
import re
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def check_file(filepath, checks):
    """Run compliance checks on a file"""
    results = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for check_name, pattern, should_exist, message in checks:
            found = bool(re.search(pattern, content, re.MULTILINE | re.IGNORECASE))
            
            if should_exist:
                if found:
                    results.append(("✅", check_name, message))
                else:
                    results.append(("❌", check_name, f"MISSING: {message}"))
            else:
                if found:
                    results.append(("❌", check_name, f"FORBIDDEN: {message}"))
                else:
                    results.append(("✅", check_name, message))
                    
    except Exception as e:
        results.append(("⚠️", "File Read", f"Error reading file: {e}"))
    
    return results

def main():
    print("=" * 80)
    print(f"{Colors.BLUE}VATICAN BOT RULES COMPLIANCE CHECKER{Colors.RESET}")
    print("=" * 80)
    print()
    
    all_passed = True
    
    # ========================================
    # CHECK 1: backend/monitors/tasks.py
    # ========================================
    print(f"{Colors.BLUE}[1/3] Checking backend/monitors/tasks.py{Colors.RESET}")
    print("-" * 80)
    
    tasks_checks = [
        # MUST use HydraBot for dynamic resolution
        ("HydraBot Import", r"from worker_vatican\.hydra_monitor import HydraBot", True, 
         "Imports HydraBot for dynamic ID resolution"),
        
        # MUST call resolve_all_dynamic_ids
        ("Dynamic ID Resolution", r"await bot\.resolve_all_dynamic_ids\(", True,
         "Calls resolve_all_dynamic_ids() to get fresh IDs"),
        
        # MUST pass visitors parameter
        ("Visitors Parameter", r"resolve_all_dynamic_ids\([^)]*visitors\s*=", True,
         "Passes visitors parameter to resolve_all_dynamic_ids()"),
        
        # MUST use 3-tier matching
        ("Keyword Matching", r"keywords.*=.*\[.*musei|biglietti|ingresso", True,
         "Implements keyword-based ticket matching"),
        
        # MUST NOT use hardcoded IDs directly
        ("No Hardcoded IDs", r"visitTypeId\s*=\s*['\"]?\d{10}['\"]?", False,
         "Does not use hardcoded ticket IDs"),
        
        # MUST use fresh_id from resolution
        ("Fresh ID Usage", r"fresh_id\s*=.*item\[.id.\]", True,
         "Uses fresh_id from dynamic resolution"),
        
        # MUST handle visitLang correctly
        ("visitLang Logic", r"if.*ticket_type.*==.*1.*visitLang", True,
         "Only adds visitLang for guided tours (ticket_type == 1)"),
    ]
    
    results = check_file("backend/monitors/tasks.py", tasks_checks)
    for icon, name, msg in results:
        color = Colors.GREEN if icon == "✅" else (Colors.RED if icon == "❌" else Colors.YELLOW)
        print(f"{color}{icon} {name}: {msg}{Colors.RESET}")
        if icon == "❌":
            all_passed = False
    
    print()
    
    # ========================================
    # CHECK 2: worker_vatican/hydra_monitor.py
    # ========================================
    print(f"{Colors.BLUE}[2/3] Checking worker_vatican/hydra_monitor.py{Colors.RESET}")
    print("-" * 80)
    
    hydra_checks = [
        # MUST use Rome timezone
        ("Rome Timezone", r"ZoneInfo\(['\"]Europe/Rome['\"]\)", True,
         "Uses Europe/Rome timezone for timestamp calculation"),
        
        # MUST build correct deep link
        ("Deep Link Format", r"fromtag/\{.*visitors.*\}/\{.*ts.*\}/\{.*slug.*\}/1", True,
         "Builds deep link with correct format: /fromtag/{visitors}/{ts}/{slug}/1"),
        
        # MUST extract from data-cy attributes
        ("Data-cy Extraction", r"data-cy.*bookTicket_", True,
         "Extracts ticket IDs from data-cy='bookTicket_' attributes"),
        
        # MUST accept visitors parameter
        ("Visitors Parameter", r"def resolve_all_dynamic_ids\(.*visitors\s*=", True,
         "resolve_all_dynamic_ids() accepts visitors parameter"),
        
        # MUST cache with JSESSIONID
        ("JSESSIONID Caching", r"jsessionid.*=.*cookie\[.value.\]", True,
         "Caches IDs together with JSESSIONID"),
        
        # MUST NOT use hardcoded constants
        ("No Hardcoded Constants", r"GUIDED_TOUR_ID\s*=|STANDARD_TICKET_ID\s*=", False,
         "Does not use GUIDED_TOUR_ID or STANDARD_TICKET_ID constants in logic"),
    ]
    
    results = check_file("worker_vatican/hydra_monitor.py", hydra_checks)
    for icon, name, msg in results:
        color = Colors.GREEN if icon == "✅" else (Colors.RED if icon == "❌" else Colors.YELLOW)
        print(f"{color}{icon} {name}: {msg}{Colors.RESET}")
        if icon == "❌":
            all_passed = False
    
    print()
    
    # ========================================
    # CHECK 3: worker_vatican/god_tier_monitor.py
    # ========================================
    print(f"{Colors.BLUE}[3/3] Checking worker_vatican/god_tier_monitor.py{Colors.RESET}")
    print("-" * 80)
    
    god_tier_checks = [
        # MUST validate session
        ("Session Validation", r"async def validate_session\(", True,
         "Implements session validation before API calls"),
        
        # MUST refresh with browser
        ("Browser Refresh", r"async def refresh_session_with_browser\(", True,
         "Implements browser-based session refresh"),
        
        # MUST accept visitors parameter
        ("Visitors Parameter", r"refresh_session_with_browser\(.*visitors", True,
         "refresh_session_with_browser() accepts visitors parameter"),
        
        # MUST use visitors in deep link
        ("Deep Link Visitors", r"fromtag/\{visitors\}", True,
         "Uses visitors parameter in deep link construction"),
        
        # MUST include JSESSIONID in requests
        ("JSESSIONID Cookie", r"cookies.*JSESSIONID|session\.cookies\.update", True,
         "Includes JSESSIONID cookie in API requests"),
        
        # MUST use Rome timezone
        ("Rome Timezone", r"ZoneInfo\(['\"]Europe/Rome['\"]\)", True,
         "Uses Europe/Rome timezone for timestamp calculation"),
    ]
    
    results = check_file("worker_vatican/god_tier_monitor.py", god_tier_checks)
    for icon, name, msg in results:
        color = Colors.GREEN if icon == "✅" else (Colors.RED if icon == "❌" else Colors.YELLOW)
        print(f"{color}{icon} {name}: {msg}{Colors.RESET}")
        if icon == "❌":
            all_passed = False
    
    print()
    print("=" * 80)
    
    # ========================================
    # SUMMARY
    # ========================================
    if all_passed:
        print(f"{Colors.GREEN}✅ ALL CHECKS PASSED - Code follows Vatican Bot Rules!{Colors.RESET}")
        print()
        print("Next steps:")
        print("  1. Restart worker: docker-compose restart worker_vatican")
        print("  2. Monitor logs: docker-compose logs -f worker_vatican")
        print("  3. Look for: '✅ Keyword Match' or '✅ Exact Match'")
    else:
        print(f"{Colors.RED}❌ COMPLIANCE ISSUES FOUND - Review failures above{Colors.RESET}")
        print()
        print("Action required:")
        print("  1. Fix the issues marked with ❌")
        print("  2. Re-run this script to verify")
        print("  3. Refer to .kiro/steering/VATICAN_BOT_RULES.md for details")
    
    print("=" * 80)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
