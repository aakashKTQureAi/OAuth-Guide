import base64, hashlib, http.server, json, os, secrets, ssl, sys, threading, time, urllib.parse, urllib.request
from pathlib import Path
ROOT=Path('/tmp/github-oauth-validation')
os.umask(0o077)
CALLBACK='http://127.0.0.1:8765/callback'
state=secrets.token_urlsafe(32)
verifier=secrets.token_urlsafe(48)
challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
if '--self-check' in sys.argv:
    known='dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk'
    assert base64.urlsafe_b64encode(hashlib.sha256(known.encode()).digest()).rstrip(b'=').decode()=='E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM'
    assert len(challenge)==43 and len(verifier)>=43
    assert urllib.parse.urlsplit(CALLBACK).hostname=='127.0.0.1'
    assert secrets.compare_digest(state,state) and not secrets.compare_digest(state,'wrong')
    print('SELF_CHECK_PASSED');sys.exit(0)
done=threading.Event()
result={'callback_received':False,'state_valid':False,'pkce_used':True,'requested_scopes':[],'token_exchange_succeeded':False,'authenticated_api_read':False,'refresh_tested':False}
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError('redirect_blocked')
opener=urllib.request.build_opener(NoRedirect,urllib.request.HTTPSHandler(context=ssl.create_default_context(cafile="/etc/ssl/cert.pem")))
def request_json(url, data=None, headers=None):
    assert (url,data is not None) in {('https://github.com/login/oauth/access_token',True),('https://api.github.com/user',False)}
    req=urllib.request.Request(url,data=data,headers=headers or {})
    with opener.open(req,timeout=20) as response:
        return response.status, response.headers, json.load(response)
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        parsed=urllib.parse.urlsplit(self.path)
        if parsed.path=='/callback' and not done.is_set():
            result['callback_received']=True
            q=urllib.parse.parse_qs(parsed.query)
            result['state_valid']=secrets.compare_digest(q.get('state',[''])[0],state)
            try:
                if not result['state_valid']:raise ValueError('state')
                if 'error' in q:raise ValueError('consent')
                code=q.get('code',[''])[0]
                if not code:raise ValueError('code')
                status,headers,token=request_json('https://github.com/login/oauth/access_token',urllib.parse.urlencode({'client_id':credentials['client_id'],'client_secret':credentials['client_secret'],'code':code,'redirect_uri':CALLBACK,'code_verifier':verifier}).encode(),{'Accept':'application/json','User-Agent':'OAuth-Guide-local-validation'})
                result['token_exchange_http_status']=status
                if not token.get('access_token'):raise ValueError('exchange')
                result['token_exchange_succeeded']=True
                if not isinstance(token.get('scope'),str):raise ValueError('missing_scope')
                granted=[s for s in token['scope'].replace(',',' ').split() if s!='offline_access']
                result['granted_scopes_empty']=not granted
                result['expiring_access_token']=isinstance(token.get('expires_in'),int)
                result['refresh_token_returned']=bool(token.get('refresh_token'))
                if granted:raise ValueError('unexpected_scope')
                status,headers,profile=request_json('https://api.github.com/user',headers={'Authorization':'Bearer '+token['access_token'],'Accept':'application/vnd.github+json','User-Agent':'OAuth-Guide-local-validation'})
                result['api_method']='GET';result['api_path']='/user';result['api_http_status']=status
                result['authenticated_api_read']=status==200 and isinstance(profile.get('id'),int)
                result['response_has_account_identity']=isinstance(profile.get('id'),int)
                result['api_scope_header_empty']=not bool(headers.get('X-OAuth-Scopes','').strip())
                # The token stays in process memory only and is discarded at exit.
                token.clear();profile.clear()
            except Exception as exc:
                result['failed_stage']='oauth_or_api'
                result['error_class']=type(exc).__name__
            finally:
                credentials.clear()
                (ROOT/'result.json').write_text(json.dumps(result,indent=2))
                done.set()
            self.send_response(303);self.send_header('Location','/done');self.end_headers()
        elif parsed.path=='/done':
            self.send_response(200);self.send_header('Content-Type','text/plain');self.end_headers();self.wfile.write(b'OAuth validation finished. Sensitive values were not logged. You may close this tab.')
        else:self.send_error(404)
server=http.server.HTTPServer(('127.0.0.1',8765),Handler)
server.timeout=1
# Bind the port before consuming credentials, so a busy port does not burn the secret.
credentials=json.loads((ROOT/'credentials.json').read_text())
(ROOT/'credentials.json').unlink()
url='https://github.com/login/oauth/authorize?'+urllib.parse.urlencode({'client_id':credentials['client_id'],'redirect_uri':CALLBACK,'state':state,'code_challenge':challenge,'code_challenge_method':'S256','allow_signup':'false'})
(ROOT/'authorize-url.txt').write_text(url)
print('LOCAL_LISTENER_READY',flush=True)
deadline=time.monotonic()+300
while time.monotonic()<deadline:
    server.handle_request()
    if done.is_set():
        # One final request serves /done following the query-free redirect.
        server.handle_request();break
server.server_close()
(ROOT/'authorize-url.txt').unlink(missing_ok=True)
if not done.is_set():
    result['failed_stage']='callback_timeout';(ROOT/'result.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)
