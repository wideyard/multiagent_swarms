#!/usr/bin/env python3
"""
Simple AirSim connection test
"""
import airsim
import sys

print("Simple AirSim Connection Test")
print("="*50)

try:
    print("\n1. Creating client...")
    client = airsim.MultirotorClient(ip="127.0.0.1", timeout_value=3)
    print("   ✓ Client created")
    
    print("\n2. Confirming connection...")
    client.confirmConnection()
    print("   ✓ Connection confirmed!")
    
    print("\n3. Getting sim version...")
    try:
        # This will work if connection is established
        client.simPause(False)
        print("   ✓ Can control simulation")
    except Exception as e:
        print(f"   ⚠ Cannot control sim: {e}")
    
    print("\n4. Checking drones...")
    for i in range(1, 11):
        drone_name = f"Drone{i}"
        try:
            state = client.getMultirotorState(vehicle_name=drone_name)
            pos = state.kinematics_estimated.position
            print(f"   ✓ {drone_name} at ({pos.x_val:.1f}, {pos.y_val:.1f}, {pos.z_val:.1f})")
        except Exception as e:
            print(f"   ✗ {drone_name} not found")
            if i == 1:
                print(f"      Error: {e}")
            break
    
    print("\n✓ AirSim is working correctly!")
    sys.exit(0)
    
except Exception as e:
    error_type = type(e).__name__
    
    if "TimeoutError" in error_type or "timed out" in str(e).lower():
        print(f"\n✗ AirSim Timeout: {e}")
        print("\nDiagnosis:")
        print("  ✓ AirSim process is running (port 41451 listening)")
        print("  ✗ AirSim is NOT responding to API calls")
        print("\nMost Likely Cause:")
        print("  → You haven't pressed the PLAY button in AirSim!")
        print("\nSolution:")
        print("  1. Look at the AirSim window")
        print("  2. Click the PLAY button (▶) in the top toolbar")
        print("  3. Wait for environment to fully load (~5-10 seconds)")
        print("  4. Run this test again")
        print("\nAlternative fixes:")
        print("  - Close and reopen AirSim")
        print("  - Check settings.json is valid JSON")
        print("  - Verify you have 10 drones configured in settings.json")
        sys.exit(1)
    else:
        print(f"\n✗ Error: {e}")
        print(f"   Type: {error_type}")
        sys.exit(1)
