from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.request import Request, urlopen
from urllib.error import URLError

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        data = json.loads(body)

        # Validate required fields
        first_name = data.get('firstName', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()

        if not first_name or not email or not phone:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'All fields are required'}).encode())
            return

        # Submit to Jtek/GHL API
        api_key = os.environ.get('JTEK_API_KEY', '')
        location_id = os.environ.get('JTEK_LOCATION_ID', '')

        contact_data = json.dumps({
            'firstName': first_name,
            'email': email,
            'phone': phone,
            'locationId': location_id,
            'source': '5 Mistakes Guide Lead Magnet',
            'tags': ['lead-magnet', '5-mistakes-guide']
        }).encode()

        req = Request(
            'https://services.leadconnectorhq.com/contacts/',
            data=contact_data,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'Version': '2021-04-15',
                'User-Agent': 'JesseTek-LeadMagnet/1.0'
            },
            method='POST'
        )

        try:
            response = urlopen(req)
            result = json.loads(response.read())
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'contactId': result.get('contact', {}).get('id', '')}).encode())
        except URLError as e:
            error_body = e.read().decode() if hasattr(e, 'read') else str(e)
            # Handle duplicate contact - still a success
            if 'duplicated' in error_body.lower() or 'duplicate' in error_body.lower():
                try:
                    err_data = json.loads(error_body)
                    contact_id = err_data.get('meta', {}).get('contactId', '')
                    # Add tags to existing contact via upsert
                    upsert_data = json.dumps({
                        'firstName': first_name,
                        'email': email,
                        'phone': phone,
                        'locationId': location_id,
                        'source': '5 Mistakes Guide Lead Magnet',
                        'tags': ['lead-magnet', '5-mistakes-guide']
                    }).encode()
                    upsert_req = Request(
                        'https://services.leadconnectorhq.com/contacts/upsert',
                        data=upsert_data,
                        headers={
                            'Authorization': f'Bearer {api_key}',
                            'Content-Type': 'application/json',
                            'Version': '2021-04-15',
                            'User-Agent': 'JesseTek-LeadMagnet/1.0'
                        },
                        method='POST'
                    )
                    upsert_resp = urlopen(upsert_req)
                    upsert_result = json.loads(upsert_resp.read())
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': True, 'contactId': upsert_result.get('contact', {}).get('id', contact_id)}).encode())
                    return
                except:
                    pass
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True, 'contactId': '', 'note': 'existing contact'}).encode())
            else:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Failed to create contact', 'details': error_body}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
