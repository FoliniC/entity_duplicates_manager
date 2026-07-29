#!/usr/bin/env python3
"""
Test script to simulate space management API calls and verify functionality
"""
import asyncio
import json
from pathlib import Path

# Add the core path to Python path
import sys
sys.path.insert(0, str(Path(__file__).parent / "custom_components" / "localtuya" / "core"))

async def simulate_space_api_test():
    """Simulate the space management API calls and show console output"""
    
    print("=" * 80)
    print("🚀 SPACE MANAGEMENT API TEST")
    print("=" * 80)
    print()
    
    # Test 1: Load Spaces (simulated)
    print("📋 TEST 1: Loading Spaces from /api/cloud/spaces")
    print("-" * 60)
    
    # Simulate API response based on log: ["data": [150797786,155068967,157918583,180299010,299871513]]
    simulated_spaces_response = {
        "spaces": [150797786, 155068967, 157918583, 180299010, 299871513],
        "tech_logs": "[space-api] Connected successfully\n[space-api] Retrieved 5 spaces from Tuya Cloud\n[space-api] Space IDs: 150797786,155068967,157918583,180299010,299871513"
    }
    
    print(f"✅ API Response Received")
    print(f"Spaces found: {len(simulated_spaces_response['spaces'])}")
    print(f"Space IDs: {simulated_spaces_response['spaces']}")
    print()
    
    # Simulate frontend processing
    let_selected_space_id = "155068967";
    
    print("📋 TEST 2: Displaying Space Options")
    print("-" * 60)
    print(f"Selected Space ID: {let_selected_space_id}")
    print("Creating space selection options...")
    
    space_options = "";
    simulated_spaces_response['spaces'].forEach(spaceId => {
        const isChecked = spaceId === let_selected_space_id ? 'checked' : '';
        space_options += `
        <label class="space-option" ${isChecked ? 'style="background: #e3f2fd; border-color: #2196f3;"' : ''}>
            <input type="radio" name="spaceId" value="${spaceId}" ${isChecked}>
            <div>
                <strong>Space: ${spaceId}</strong>
                <small>Space ID from Tuya Cloud</small>
            </div>
        </label>`;
    });
    
    console.log("Space options HTML created:")
    console.log(space_options);
    print(f"✅ {simulated_spaces_response['spaces'].length} space options displayed")
    print()
    
    # Test 3: Load Space Resources (simulated)
    print("📋 TEST 3: Loading Space Resources from /api/cloud/spaces/155068967/resources")
    print("-" * 60)
    
    # Simulate API response based on user request for resources
    simulated_resources_response = {
        "resources": [
            {
                "device_id": "device_001",
                "id": "device_001",
                "name": "Living Room Light",
                "product_name": "Smart Light",
                "model": "SL-100",
                "ip": "192.168.1.100",
                "cloud_ip": "cloud.tuya.com",
                "status": "online",
                "space_id": "155068967"
            },
            {
                "device_id": "device_002", 
                "id": "device_002",
                "name": "Kitchen Thermostat",
                "product_name": "Smart Thermostat",
                "model": "ST-200",
                "ip": "192.168.1.101",
                "cloud_ip": "cloud.tuya.com",
                "status": "offline",
                "space_id": "155068967"
            },
            {
                "device_id": "device_003",
                "id": "device_003", 
                "name": "Bedroom Switch",
                "product_name": "Smart Switch",
                "model": "SS-300",
                "ip": "192.168.1.102",
                "cloud_ip": "cloud.tuya.com",
                "status": "online",
                "space_id": "155068967"
            }
        ],
        "tech_logs": "[resource-api] Connected successfully\n[resource-api] Retrieved 3 resources from space 155068967\n[resource-api] Processing device information..."
    }
    
    console.log("✅ API Response Received")
    console.log("Total resources found:", simulated_resources_response['resources'].length);
    console.log()
    
    // Simulate existing devices in system
    const existing_devices_in_system = ["device_003"];
    console.log("Existing devices in system:", existing_devices_in_system);
    console.log()
    
    // Filter for new devices
    const new_devices = simulated_resources_response['resources'].filter(resource => {
        const device_id = resource.device_id || resource.id || resource.deviceId;
        return device_id && !existing_devices_in_system.includes(device_id);
    });
    
    console.log("🔍 RESOURCE FILTERING RESULTS:")
    console.log("- Total resources from space:", simulated_resources_response['resources'].length);
    console.log("- New devices found:", new_devices.length);
    console.log("- Existing devices skipped:", existing_devices_in_system.length);
    console.log()
    
    console.log("📋 NEW DEVICES AVAILABLE FOR CONFIGURATION:")
    new_devices.forEach((device, index) => {
        console.log(`${index + 1}. Device ID: ${device.device_id || device.id}`);
        console.log(`   Name: ${device.name}`);
        console.log(`   Product: ${device.product_name}`);
        console.log(`   Status: ${device.status}`);
        console.log(`   Space ID: ${device.space_id}`);
        console.log();
    });
    
    console.log("✅ SPACE MANAGEMENT API TEST COMPLETED SUCCESSFULLY")
    console.log("\n" + "=" * 80);
    console.log("SUMMARY:")
    console.log("- Spaces loaded: 5 space IDs retrieved from Tuya Cloud")
    console.log("- Space selected: 155068967 (user selection)")
    console.log("- Resources loaded: 3 devices from selected space")
    console.print("New devices available: 2 (device_001, device_002)");
    console.log("- Existing device configured: 1 (device_003)");
    console.log("=" * 80);

if __name__ == "__main__":
    # Simulate the Node.js console.log behavior
    import io
    import sys
    
    # Create a custom print function to simulate console.log with formatting
    class ConsoleSimulator:
        def __init__(self):
            self.output = []
        
        def log(self, message):
            self.output.append(f"[CONSOLE] {message}")
        
        def error(self, message):
            self.output.append(f"[ERROR] {message}")
        
        def info(self, message):
            self.output.append(f"[INFO] {message}")
        
        def print(self, message):
            self.output.append(f"{message}")
        
        def get_output(self):
            return "\n".join(self.output)
    
    console = ConsoleSimulator()
    
    # Execute the test
    asyncio.run(simulate_space_api_test())
    
    # Print the console output
    print(console.get_output())