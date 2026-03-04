#!/usr/bin/env python3
"""
Test running backend and get URL for dashboard
"""

import subprocess
import json

def test_docker_backend():
    """Test the backend running in Docker"""
    
    print("\n" + "="*80)
    print("TESTING DOCKER BACKEND")
    print("="*80)
    
    # Check if Docker is running
    print("\n1. Checking Docker status...")
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker is running")
            print("\nRunning containers:")
            print(result.stdout)
        else:
            print("❌ Docker is not running")
            return
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")
        return
    
    # Find backend container
    print("\n2. Finding backend container...")
    try:
        result = subprocess.run(
            ['docker', 'ps', '--format', '{{.Names}}'],
            capture_output=True,
            text=True
        )
        containers = result.stdout.strip().split('\n')
        
        backend_container = None
        for container in containers:
            if 'backend' in container.lower() or 'django' in container.lower() or 'web' in container.lower():
                backend_container = container
                break
        
        if backend_container:
            print(f"✅ Found backend container: {backend_container}")
        else:
            print("⚠️ No backend container found")
            print("Available containers:", containers)
            backend_container = input("\nEnter backend container name: ").strip()
    except Exception as e:
        print(f"❌ Error finding container: {e}")
        return
    
    # Get container port mapping
    print("\n3. Checking port mapping...")
    try:
        result = subprocess.run(
            ['docker', 'port', backend_container],
            capture_output=True,
            text=True
        )
        print("Port mappings:")
        print(result.stdout)
        
        # Try to extract port
        if '8000' in result.stdout:
            # Parse port mapping (e.g., "8000/tcp -> 0.0.0.0:8000")
            for line in result.stdout.split('\n'):
                if '8000' in line:
                    if '0.0.0.0' in line or '127.0.0.1' in line:
                        parts = line.split('->')
                        if len(parts) > 1:
                            port_info = parts[1].strip()
                            port = port_info.split(':')[-1]
                            print(f"\n✅ Backend is exposed on port: {port}")
    except Exception as e:
        print(f"⚠️ Could not get port info: {e}")
    
    # Test API endpoints
    print("\n4. Testing API endpoints...")
    
    # Try common URLs with correct API path
    test_urls = [
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]
    
    working_url = None
    
    for base_url in test_urls:
        print(f"\nTrying {base_url}...")
        try:
            # Test with /api/v1/tasks/ endpoint
            result = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', f'{base_url}/api/v1/tasks/'],
                capture_output=True,
                text=True,
                timeout=5
            )
            status_code = result.stdout.strip()
            
            if status_code == '200':
                print(f"✅ {base_url} is working!")
                working_url = base_url
                break
            else:
                print(f"❌ {base_url} returned {status_code}")
        except Exception as e:
            print(f"❌ {base_url} failed: {e}")
    
    if not working_url:
        print("\n⚠️ Could not connect to backend")
        print("\nTry these commands manually:")
        print("  docker ps")
        print("  docker port <container-name>")
        print("  curl http://localhost:8000/api/v1/tasks/")
        return
    
    # Test specific endpoints
    print(f"\n5. Testing endpoints on {working_url}...")
    
    endpoints = [
        '/api/v1/tasks/',
        '/api/v1/agencies/',
        '/api/v1/results/',
    ]
    
    for endpoint in endpoints:
        try:
            result = subprocess.run(
                ['curl', '-s', f'{working_url}{endpoint}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    if isinstance(data, list):
                        print(f"✅ {endpoint} - {len(data)} items")
                    else:
                        print(f"✅ {endpoint} - OK")
                except:
                    print(f"✅ {endpoint} - Response received")
            else:
                print(f"❌ {endpoint} - Failed")
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
    
    # Get public URL if available
    print("\n6. Checking for public URL...")
    
    # Check if there's a tunnel or ngrok
    try:
        result = subprocess.run(
            ['docker', 'logs', '--tail', '50', backend_container],
            capture_output=True,
            text=True
        )
        
        logs = result.stdout
        
        # Look for URLs in logs
        if 'http://' in logs or 'https://' in logs:
            print("\nFound URLs in logs:")
            for line in logs.split('\n'):
                if 'http://' in line or 'https://' in line:
                    print(f"  {line.strip()}")
    except:
        pass
    
    # Final summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if working_url:
        print(f"\n✅ Backend is running at: {working_url}")
        print(f"\n📋 API Endpoints:")
        print(f"  Tasks: {working_url}/api/v1/tasks/")
        print(f"  Agencies: {working_url}/api/v1/agencies/")
        print(f"  Results: {working_url}/api/v1/results/")
        
        print(f"\n🌐 For Vercel Dashboard:")
        print(f"  ⚠️ IMPORTANT: Localhost is NOT accessible from Vercel!")
        print(f"")
        print(f"  You need to expose your backend publicly:")
        print(f"")
        print(f"  Option 1 - ngrok (Fastest for testing):")
        print(f"    1. Install: https://ngrok.com/download")
        print(f"    2. Run: ngrok http 8000")
        print(f"    3. Copy the HTTPS URL (e.g., https://abc123.ngrok.io)")
        print(f"    4. In Vercel: Set NEXT_PUBLIC_API_URL=https://abc123.ngrok.io/api/v1")
        print(f"")
        print(f"  Option 2 - Cloudflare Tunnel (Free):")
        print(f"    1. Install: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/")
        print(f"    2. Run: cloudflared tunnel --url http://localhost:8000")
        print(f"    3. Copy the URL (e.g., https://xyz.trycloudflare.com)")
        print(f"    4. In Vercel: Set NEXT_PUBLIC_API_URL=https://xyz.trycloudflare.com/api/v1")
        print(f"")
        print(f"  Option 3 - Deploy to Production (Recommended):")
        print(f"    - Railway: railway up")
        print(f"    - Render: Connect GitHub repo")
        print(f"    - DigitalOcean/AWS: Deploy Docker container")
        print(f"    - In Vercel: Set NEXT_PUBLIC_API_URL=https://your-backend.com/api/v1")
        
        print(f"\n📝 After getting public URL:")
        print(f"  1. Go to Vercel Dashboard → Your Project")
        print(f"  2. Settings → Environment Variables")
        print(f"  3. Add: NEXT_PUBLIC_API_URL = <your-public-url>/api/v1")
        print(f"  4. Redeploy your frontend")
        print(f"  5. Dashboard should show correct status!")
        
        print(f"\n📖 Full guide: See VERCEL_DASHBOARD_SETUP.md")
    else:
        print("\n❌ Could not connect to backend")
        print("\nTroubleshooting:")
        print("  1. Check if container is running: docker ps")
        print("  2. Check container logs: docker logs <container-name>")
        print("  3. Check port mapping: docker port <container-name>")
        print("  4. Try accessing: curl http://localhost:8000/api/health/")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    test_docker_backend()
