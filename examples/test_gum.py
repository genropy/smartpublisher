#!/usr/bin/env python
"""
Quick test to verify gum integration works.
"""

import sys
sys.path.insert(0, '../src')

from smpub.interactive import is_gum_available
from smpub.validation import get_parameter_info
from test_params import TestHandler

# Check gum availability
print("Checking gum availability...")
if is_gum_available():
    print("✓ gum is installed and available")
else:
    print("✗ gum is not available")
    sys.exit(1)

# Test parameter extraction
handler = TestHandler()
method = handler.test_mixed

print("\nExtracting parameters from test_mixed method...")
params = get_parameter_info(method)

print("\nParameters found:")
for param in params:
    print(f"  - {param['name']}: {param['type']} "
          f"(required={param['required']}, default={param['default']})")

print("\n✓ All checks passed!")
print("\nTo test interactive mode manually, run:")
print("  python test_params.py test mixed --interactive")
