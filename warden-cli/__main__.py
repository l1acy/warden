import sys
import json
import os

args = sys.argv[1:]

def set_browser_proxy():
    supports_browsers = ['chromium']

    for index, b in enumerate(supports_browsers):
        print(str(index) + '.', b)

    selected = input('Which browser set proxy?: ')

    def set_proxy_to_chromium_browser(name: str):
        policy_dir = "/etc/chromium/policies/managed"
        policy_path = os.path.join(policy_dir, "proxy.json")

        proxy = input("Proxy (host:port): ").strip()
        if not proxy:
            print("Empty proxy, cancelled")
            return
        if "://" in proxy:
            proxy = proxy.split("://", 1)[1]

        bypass = input("Bypass list [localhost,127.0.0.1]: ").strip() or "localhost,127.0.0.1"

        policy = {
            "ProxySettings": {
                "ProxyMode": "fixed_servers",
                "ProxyServer": proxy,
                "ProxyBypassList": bypass,
            }
        }

        try:
            os.makedirs(policy_dir, exist_ok=True)
            with open(policy_path, "w", encoding="utf-8") as f:
                json.dump(policy, f, indent=2)
            os.chmod(policy_path, 0o644)
        except PermissionError:
            print(f"Permission denied: {policy_path}")
            print("Run this script with sudo, or set the policy manually.")
            return
        except OSError as e:
            print(f"Failed to write policy: {e}")
            return

        print(f"Written: {policy_path}")
        print("Restart the browser to apply.")

    try:
        idx = int(selected)
    except ValueError:
        print("Enter a number")
        return

    if idx < 0 or idx >= len(supports_browsers):
        print("Invalid choice")
        return

    name = supports_browsers[idx]

    if name == "chromium":
        set_proxy_to_chromium_browser(name)
    else:
        print(f"No handler for {name}")
    
commands = {
    'set-browser-proxy': set_browser_proxy
}
    
if len(args) < 1:
    print('Help:')
    print('set-browser-proxy: Set proxy for selected browser')
else:
    commands.get(args[0], lambda: print('Command not found'))()