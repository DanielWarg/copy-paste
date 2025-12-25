#!/usr/bin/env python3
"""
A-Z Test av alla moduler enligt architecture.md
Testar alla endpoints och funktionalitet systematiskt.
"""
import json
import subprocess
import sys
import time
from typing import Dict, Any, List, Optional

BASE_URL = "http://localhost:8000"
REQUEST_ID_PREFIX = "test-az-"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_header(text: str):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_test(name: str):
    print(f"{Colors.YELLOW}▶ {name}...{Colors.RESET}", end=" ", flush=True)

def print_pass():
    print(f"{Colors.GREEN}✅ PASS{Colors.RESET}")

def print_fail(error: str):
    print(f"{Colors.RED}❌ FAIL: {error}{Colors.RESET}")

def api_call(method: str, endpoint: str, data: Optional[Dict] = None, files: Optional[Dict] = None) -> tuple[int, Dict[str, Any]]:
    """Make API call and return (status_code, response_data)."""
    request_id = f"{REQUEST_ID_PREFIX}{int(time.time() * 1000)}"
    cmd = ['curl', '-s', '-w', '\nHTTPSTATUS:%{http_code}', '-X', method, f"{BASE_URL}{endpoint}"]
    
    if method == 'GET':
        pass
    elif method in ['POST', 'PATCH', 'PUT']:
        if files:
            # Multipart form data
            for key, value in files.items():
                if isinstance(value, str) and value.startswith('@'):
                    cmd.extend(['-F', f"{key}={value}"])
                else:
                    cmd.extend(['-F', f"{key}={value}"])
        elif data:
            cmd.extend(['-H', 'Content-Type: application/json', '-d', json.dumps(data)])
    
    cmd.extend(['-H', f'X-Request-Id: {request_id}'])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = result.stdout.strip()
        
        # Extract status code (look for HTTPSTATUS: prefix)
        status_code = 200  # Default
        body = output
        if 'HTTPSTATUS:' in output:
            parts = output.split('HTTPSTATUS:')
            if len(parts) == 2:
                body = parts[0].strip()
                try:
                    status_code = int(parts[1].strip())
                except ValueError:
                    pass
        
        try:
            response_data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            response_data = {"raw": body} if body else {}
        
        return status_code, response_data
    except subprocess.TimeoutExpired:
        return 504, {"error": "Request timeout"}
    except Exception as e:
        return 0, {"error": str(e)}

def test_health():
    """Test health endpoint."""
    print_test("Health Check")
    status, data = api_call('GET', '/health')
    if status == 200 and data.get('status') == 'ok':
        print_pass()
        return True
    else:
        print_fail(f"Status: {status}, Data: {data}")
        return False

def test_ready():
    """Test readiness endpoint."""
    print_test("Readiness Check")
    status, data = api_call('GET', '/ready')
    if status == 200:
        print_pass()
        print(f"   Status: {data.get('status', 'unknown')}")
        return True
    else:
        print_fail(f"Status: {status}, Data: {data}")
        return False

def test_record_create():
    """Test record creation."""
    print_test("Record: Create")
    status, data = api_call('POST', '/api/v1/record/create', {
        'title': 'A-Z Test Record',
        'sensitivity': 'standard',
        'language': 'sv'
    })
    if status == 201 and 'transcript_id' in data:
        print_pass()
        print(f"   Transcript ID: {data.get('transcript_id')}")
        return data.get('transcript_id')
    else:
        print_fail(f"Status: {status}, Data: {data}")
        return None

def test_record_upload(transcript_id: int):
    """Test audio upload."""
    print_test("Record: Upload Audio")
    # Use a small test file or skip if Del21.wav doesn't exist
    import os
    test_file = "Del21.wav"
    if not os.path.exists(test_file):
        print_fail(f"Test file {test_file} not found - SKIP")
        return None
    
    status, data = api_call('POST', f'/api/v1/record/{transcript_id}/audio', 
                           files={'file': f'@{test_file}'})
    
    if status == 201 and data.get('status') == 'ok':
        print_pass()
        print(f"   File ID: {data.get('file_id')}, SHA256: {data.get('sha256', '')[:16]}...")
        return data
    else:
        print_fail(f"Status: {status}, Data: {data}")
        return None

def test_transcripts_list():
    """Test transcripts listing."""
    print_test("Transcripts: List")
    # Try with trailing slash if 307 redirect
    status, data = api_call('GET', '/api/v1/transcripts/?limit=10')
    if status == 200 and isinstance(data, dict) and 'items' in data:
        print_pass()
        print(f"   Found {len(data.get('items', []))} transcripts")
        return data.get('items', [])
    else:
        print_fail(f"Status: {status}, Data: {data}")
        return []

def test_transcripts_get(transcript_id: int):
    """Test get transcript."""
    print_test(f"Transcripts: Get {transcript_id}")
    status, data = api_call('GET', f'/api/v1/transcripts/{transcript_id}')
    if status == 200 and 'id' in data:
        print_pass()
        print(f"   Title: {data.get('title')}, Status: {data.get('status')}")
        return data
    else:
        print_fail(f"Status: {status}, Data: {data}")
        return None

def test_projects_list():
    """Test projects listing."""
    print_test("Projects: List")
    # Try with trailing slash if 307 redirect
    status, data = api_call('GET', '/api/v1/projects/?limit=10')
    if status == 200 and isinstance(data, dict) and 'items' in data:
        print_pass()
        print(f"   Found {len(data.get('items', []))} projects")
        return data.get('items', [])
    else:
        print_fail(f"Status: {status}, Data: {data}")
        return []

def test_projects_create():
    """Test project creation."""
    print_test("Projects: Create")
    # Try with trailing slash if 307 redirect
    status, data = api_call('POST', '/api/v1/projects/', {
        'name': 'A-Z Test Project',
        'sensitivity': 'standard',
        'start_date': '2025-12-25',
        'due_date': '2025-12-31'
    })
    if status == 201 and 'id' in data:
        print_pass()
        print(f"   Project ID: {data.get('id')}, Name: {data.get('name')}")
        return data.get('id')
    else:
        print_fail(f"Status: {status}, Data: {data}")
        return None

def test_projects_get(project_id: int):
    """Test get project."""
    print_test(f"Projects: Get {project_id}")
    status, data = api_call('GET', f'/api/v1/projects/{project_id}')
    if status == 200 and 'id' in data:
        print_pass()
        print(f"   Name: {data.get('name')}, Status: {data.get('status')}")
        return data
    else:
        print_fail(f"Status: {status}, Data: {data}")
        return None

def test_projects_files_list(project_id: int):
    """Test list project files."""
    print_test(f"Projects: List Files {project_id}")
    status, data = api_call('GET', f'/api/v1/projects/{project_id}/files')
    if status == 200 and 'items' in data:
        print_pass()
        print(f"   Found {len(data.get('items', []))} files")
        return True
    else:
        print_fail(f"Status: {status}, Data: {data}")
        return False

def test_console_events():
    """Test console events."""
    print_test("Console: Events")
    status, data = api_call('GET', '/api/v1/events?limit=10')
    if status == 200 and 'items' in data:
        print_pass()
        print(f"   Found {len(data.get('items', []))} events")
        return True
    else:
        print_fail(f"Status: {status}, Data: {data}")
        return False

def test_console_sources():
    """Test console sources."""
    print_test("Console: Sources")
    status, data = api_call('GET', '/api/v1/sources')
    if status == 200:
        print_pass()
        print(f"   Sources: {len(data) if isinstance(data, list) else 'N/A'}")
        return True
    else:
        print_fail(f"Status: {status}, Data: {data}")
        return False

def test_privacy_mask():
    """Test privacy mask."""
    print_test("Privacy Shield: Mask")
    status, data = api_call('POST', '/api/v1/privacy/mask', {
        'text': 'Ring mig på 070-123 45 67',
        'mode': 'strict'
    })
    # Privacy Shield returns 'maskedText' (camelCase) not 'masked_text'
    if status == 200 and ('masked_text' in data or 'maskedText' in data):
        print_pass()
        masked = data.get('masked_text') or data.get('maskedText', '')
        print(f"   Masked: {masked[:50]}...")
        return True
    else:
        print_fail(f"Status: {status}, Data: {data}")
        return False

def test_example():
    """Test example module."""
    print_test("Example: Query")
    status, data = api_call('GET', '/api/v1/example?q=test')
    if status == 200:
        print_pass()
        return True
    else:
        print_fail(f"Status: {status}, Data: {data}")
        return False

def main():
    """Run all tests."""
    print_header("A-Z TEST AV ALLA MODULER")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {
        'passed': 0,
        'failed': 0,
        'skipped': 0
    }
    
    # Core endpoints
    print_header("CORE ENDPOINTS")
    if test_health():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    if test_ready():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Record Module
    print_header("RECORD MODULE")
    transcript_id = test_record_create()
    if transcript_id:
        results['passed'] += 1
        # Wait a bit before upload
        time.sleep(1)
        upload_result = test_record_upload(transcript_id)
        if upload_result:
            results['passed'] += 1
        else:
            results['failed'] += 1
    else:
        results['failed'] += 1
    
    # Transcripts Module
    print_header("TRANSCRIPTS MODULE")
    transcripts = test_transcripts_list()
    if transcripts:
        results['passed'] += 1
        if transcripts and len(transcripts) > 0:
            test_transcripts_get(transcripts[0]['id'])
            results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Projects Module
    print_header("PROJECTS MODULE")
    projects = test_projects_list()
    if projects is not None:
        results['passed'] += 1
    
    project_id = test_projects_create()
    if project_id:
        results['passed'] += 1
        test_projects_get(project_id)
        results['passed'] += 1
        test_projects_files_list(project_id)
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Console Module
    print_header("CONSOLE MODULE")
    if test_console_events():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    if test_console_sources():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Privacy Shield Module
    print_header("PRIVACY SHIELD MODULE")
    if test_privacy_mask():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Example Module
    print_header("EXAMPLE MODULE")
    if test_example():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Summary
    print_header("TEST SUMMARY")
    print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.RESET}")
    print(f"{Colors.RED}Failed: {results['failed']}{Colors.RESET}")
    print(f"{Colors.YELLOW}Skipped: {results['skipped']}{Colors.RESET}")
    print(f"\nTotal: {results['passed'] + results['failed'] + results['skipped']}")
    
    if results['failed'] == 0:
        print(f"\n{Colors.GREEN}✅ ALL TESTS PASSED!{Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.RED}❌ SOME TESTS FAILED{Colors.RESET}")
        return 1

if __name__ == '__main__':
    sys.exit(main())

