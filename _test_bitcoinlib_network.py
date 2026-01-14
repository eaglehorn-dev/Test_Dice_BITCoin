"""
Test bitcoinlib network names and address generation
"""
from bitcoinlib.keys import Key

print("=" * 60)
print("TESTING BITCOINLIB NETWORK NAMES")
print("=" * 60)

# Test different network names
networks_to_test = ['bitcoin', 'testnet', 'testnet3', 'litecoin', 'dash']

for network_name in networks_to_test:
    try:
        print(f"\n[TEST] Network: {network_name}")
        key = Key(network=network_name)
        
        # Check if address is callable
        if callable(key.address):
            address = key.address()
        else:
            address = key.address
        
        print(f"   Address: {address}")
        print(f"   First char: {address[0] if address else 'N/A'}")
        
        # Testnet addresses should start with 'm', 'n', or 'tb1'
        if network_name in ['testnet', 'testnet3']:
            if address.startswith('tb1'):
                print(f"   [OK] Native SegWit testnet address (tb1)")
            elif address[0] in ['m', 'n']:
                print(f"   [OK] Legacy testnet address ({address[0]})")
            else:
                print(f"   [WARNING] Unexpected testnet address format!")
        
        # Mainnet addresses should start with '1', '3', or 'bc1'
        if network_name == 'bitcoin':
            if address.startswith('bc1'):
                print(f"   [OK] Native SegWit mainnet address (bc1)")
            elif address[0] in ['1', '3']:
                print(f"   [OK] Legacy mainnet address ({address[0]})")
            else:
                print(f"   [WARNING] Unexpected mainnet address format!")
                
    except Exception as e:
        print(f"   [ERROR] {e}")

print("\n" + "=" * 60)
print("NETWORK INFORMATION")
print("=" * 60)

# Show available networks
try:
    from bitcoinlib.networks import Network
    print("\nAvailable networks in bitcoinlib:")
    
    # Try to list networks
    import bitcoinlib.networks as networks_module
    if hasattr(networks_module, 'NETWORK_DEFINITIONS'):
        for net_name in networks_module.NETWORK_DEFINITIONS.keys():
            print(f"   - {net_name}")
    else:
        print("   (Could not list all networks)")
        
except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "=" * 60)
print("RECOMMENDATION:")
print("=" * 60)
print("\nFor testnet, use: 'testnet' (generates 'm' or 'n' addresses)")
print("For mainnet, use: 'bitcoin' (generates '1' or '3' addresses)")
print("\nNote: 'tb1' and 'bc1' are SegWit formats (more modern)")
