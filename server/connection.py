"""Build independent client copies and share a local endpoint with the launcher."""
import argparse
import datetime
import ipaddress
import json
import os
import subprocess
import sys
import time
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, ProxyHandler
import uuid
from pathlib import Path
from .library import ROOT
from .configuration import LOCAL_SHOP_VERSION
from .paths import validate_save_path

CONFIG = ROOT / "local-client/connection.json"
SERVER_CONFIG = ROOT / "server_config.json"


def read_server_config(path=SERVER_CONFIG, *, require_state=True):
    """Server-only settings; never rewrite client packages or player data."""
    path = Path(path)
    if not path.is_file(): raise ValueError(f'server config missing: {path}')
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    allowed = {'bind_host', 'public_origin', 'state', 'log', 'rules', 'startup_timeout_seconds'}
    if not isinstance(data, dict) or data.keys() - allowed:
        raise ValueError('invalid server config keys; see README_SERVER_CONFIG.md')
    origin = data.get('public_origin')
    if origin is None:
        selected = read_config()
    else:
        if not isinstance(origin, str): raise ValueError('public_origin must be an HTTP URL or null')
        parsed = urlsplit(origin)
        if (parsed.scheme != 'http' or not parsed.hostname or parsed.username or parsed.password
                or parsed.path not in ('', '/') or parsed.query or parsed.fragment):
            raise ValueError('public_origin must be http://private-IPv4:port')
        selected = endpoint(parsed.hostname, parsed.port or 80)
    bind = data.get('bind_host', '0.0.0.0')
    if not isinstance(bind, str): raise ValueError('bind_host must be an IPv4 address')
    address = ipaddress.ip_address(bind)
    if address.version != 4 or (bind != '0.0.0.0' and not address.is_loopback
                               and not any(address in ipaddress.ip_network(n) for n in
                                           ('10.0.0.0/8','172.16.0.0/12','192.168.0.0/16'))):
        raise ValueError('bind_host must be 0.0.0.0 or a private/loopback IPv4')
    selected['bind'] = str(address)
    for key, default in [('state', 'server/state/tutorial-compatible/accounts.sqlite3')]:
        value = data.get(key, default)
        if not isinstance(value, str) or not value.strip(): raise ValueError(f'{key} must be a file path')
        target = (ROOT / value).resolve()
        target=validate_save_path(target)
        if (key!='state' or require_state) and not target.is_file(): raise ValueError(f'{key} file missing: {target}; no save was created or reset')
        selected[key] = str(target)
    # Accept explicit legacy rule files for development tooling. Release launchers
    # omit the field and use current definitions directly.
    if 'rules' in data:
        value=data['rules']
        if not isinstance(value,str) or not value.strip():raise ValueError('rules must be a file path')
        target=(ROOT/value).resolve()
        if not target.is_file():raise ValueError(f'rules file missing: {target}')
        selected['rules']=str(target)
    value=data.get('log',str(Path(selected['state']).parent/'server.log'))
    if not isinstance(value,str) or not value.strip():raise ValueError('log must be a file path')
    log=(ROOT/value).resolve()
    if not log.is_relative_to(ROOT.resolve()) or log.suffix.lower()!='.log' or log==Path(selected['state']):
        raise ValueError('log must be a .log file inside the server folder')
    selected['log']=str(log)
    timeout = data.get('startup_timeout_seconds', 60)
    if type(timeout) not in (int, float) or not 5 <= timeout <= 300:
        raise ValueError('startup_timeout_seconds must be 5..300')
    selected['startup_timeout_seconds'] = timeout
    return selected


def endpoint(host, port):
    address = ipaddress.ip_address(host)
    private = any(address in network for network in (
        ipaddress.ip_network("10.0.0.0/8"), ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"), ipaddress.ip_network("127.0.0.0/8"))) if address.version == 4 else False
    if not private or address.is_unspecified or not 1 <= port <= 65535:
        raise ValueError("use a private/loopback IPv4 address and port 1..65535")
    host = str(address)
    # Emulator host alias is not an address assigned to a Windows adapter.
    bind = "0.0.0.0" if host == "10.0.2.2" else host
    return {"host": host, "port": port, "bind": bind, "origin": f"http://{host}:{port}"}


def isolation_script(host, port):
    endpoint(host, port)
    text = (ROOT / "server/tools/restrict_emulator_network.sh").read_text(encoding="utf-8")
    begin = text.index('pc_host="${1:-}"')
    end = text.index("# MuMu's kernel", begin)
    text = text[:begin] + f'pc_host="{host}"\npc_port="{port}"\n' + text[end:]
    return text.replace("--dport 8080", '--dport "$pc_port"')


def change(host, port, config=CONFIG):
    from .prepare_client import prepare
    from .sign_client import sign
    selected = endpoint(host, port)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    prefix = ROOT / "local-client" / ("gudetama-" + host.replace(".", "_") + f"-{port}-{stamp}")
    unsigned = Path(str(prefix) + "-unsigned.apk")
    signed = Path(str(prefix) + "-signed.apk")
    isolation = Path(str(prefix) + "-restrict.sh")
    prepare(selected["origin"], unsigned)
    sign(unsigned, signed)
    isolation.write_text(isolation_script(host, port), encoding="utf-8", newline="\n")
    selected.update(apk=str(signed), isolation_script=str(isolation), device_verified=False)
    config.parent.mkdir(parents=True, exist_ok=True)
    temporary = config.with_suffix(".tmp-" + uuid.uuid4().hex)
    temporary.write_text(json.dumps(selected, indent=2), encoding="utf-8")
    os.replace(temporary, config)  # Activate only after APK build and signature succeed.
    print(f"\nAPK: {signed}\nServer: {selected['origin']}\nIsolation: {isolation}")
    print("Install the new APK yourself; no emulator/ADB was operated.")
    return selected


def read_config(path=CONFIG):
    if not path.exists():
        return endpoint("172.20.10.2", 8080)
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    selected = endpoint(data["host"], data["port"])
    if any(data.get(key) != value for key, value in selected.items()):
        raise ValueError("inconsistent endpoint configuration; run CHANGE_CONNECTION.bat")
    return selected


def command(selected, mode='unified', tutorial=True):
    if mode not in ("unified", "historical", "local_compatible"):
        raise ValueError("unknown mode")
    state = Path(selected.get('state', ROOT / "server/state/tutorial-compatible/accounts.sqlite3")).resolve()
    state=validate_save_path(state)
    if not state.is_file():
        raise ValueError(f"isolated test database missing: {state}")
    args = [sys.executable, "-B", "-m", "server.app", "--host", selected["bind"], "--port", str(selected["port"]),
            "--public-origin", selected["origin"], "--state", str(state), "--mode", 'unified']
    if 'rules' in selected:args += ['--rules',str(selected['rules'])]
    if 'log' in selected:args += ['--log',str(selected['log'])]
    return args


def health_url(selected):
    # 10.0.2.2 exists only inside the emulator; check the PC listener locally.
    host = "127.0.0.1" if selected["bind"] == '0.0.0.0' else selected["bind"]
    return f"http://{host}:{selected['port']}/health"


def health(selected):
    # A system/VPN HTTP proxy must not intercept private test-server traffic.
    opener = build_opener(ProxyHandler({}))
    with opener.open(Request(health_url(selected)),timeout=1) as response:
        result = json.loads(response.read(4096))
    expected = {'unified':LOCAL_SHOP_VERSION}
    if (not isinstance(result,dict) or result.get('status') != 'ok'
            or result.get('cooking_mode') not in expected
            or result.get('setting_version') != expected[result['cooking_mode']]):
        raise ValueError('port is serving something other than the Gudetama server')
    return result


def serve(selected, mode='unified', tutorial=True):
    cmd = command(selected,mode,tutorial)
    mode,tutorial='unified',True
    process = subprocess.Popen(cmd,cwd=ROOT)
    try:
        deadline = time.monotonic()+selected.get('startup_timeout_seconds',60)
        last_error = ''
        while time.monotonic() < deadline:
            if process.poll() is not None:
                print('Server exited before startup completed. See the error above.',flush=True)
                return process.returncode or 1
            try:
                result = health(selected)
                if process.poll() is not None:
                    return process.returncode or 1
                if result.get('cooking_mode') != mode:
                    raise ValueError('another server/mode is already using this port')
                if bool(result.get('tutorial_test',False)) != tutorial:
                    raise ValueError('another test database profile is already using this port')
                print(f"READY: {selected['origin']}\nMode: {mode}\n"
                      f"Install APK configured for {selected['origin']}. Keep this window open.\n"
                      'If PC health works but the emulator cannot connect, check its isolation whitelist and Windows firewall.',flush=True)
                return process.wait()
            except (OSError,ValueError) as error:
                last_error = str(error)
                time.sleep(0.25)
        print(f'Server did not become ready: {last_error}',flush=True)
        return 1
    except KeyboardInterrupt:
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait()


def check(selected):
    print(f"Configured client: {selected['origin']}\nPC check: {health_url(selected)}",flush=True)
    try:
        result = health(selected)
    except (OSError,ValueError) as error:
        print(f'PC CONNECTION FAILED: {error}\nStart START_GAME_SERVER.bat and keep its window open. '
              'If it exits, send the error shown in that window.',flush=True)
        return 1
    print(f"PC SERVER OK: mode={result.get('cooking_mode','unknown')}\n"
          f"Now manually open {selected['origin']}/health in the emulator browser.\n"
          'PC OK + emulator fails = network/isolation/firewall issue; '
          'both OK + game fails = send game error and latest server.log.',flush=True)
    return 0


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="operation", required=True)
    switch = sub.add_parser("change")
    switch.add_argument("--host")
    switch.add_argument("--port", type=int)
    serve_parser = sub.add_parser("serve")
    serve_parser.add_argument("--mode", choices=("unified", "historical", "local_compatible"), default="unified")
    serve_parser.add_argument('--tutorial',action='store_true')
    serve_parser.add_argument('--config', type=Path, default=SERVER_CONFIG)
    check_parser = sub.add_parser("check")
    check_parser.add_argument('--config', type=Path, default=SERVER_CONFIG)
    args = parser.parse_args()
    try:
        if args.operation == "change":
            previous = read_config()
            host = args.host or input(f"PC IPv4 [{previous['host']}]: ").strip() or previous["host"]
            port = args.port if args.port is not None else int(input(f"Port [{previous['port']}]: ").strip() or previous["port"])
            change(host, port)
        elif args.operation == 'check':
            raise SystemExit(check(read_server_config(args.config)))
        else:
            if not args.config.is_file(): raise ValueError(f'server config missing: {args.config}')
            selected = read_server_config(args.config)
            print(f"Config: {args.config}\nListen: {selected['bind']}:{selected['port']}\n"
                  f"Client address: {selected['origin']}\nDatabase: {selected['state']}\nCtrl+C to stop.", flush=True)
            print('Changing this address does not modify installed APK/IPA clients.',flush=True)
            raise SystemExit(serve(selected,args.mode,args.tutorial))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
