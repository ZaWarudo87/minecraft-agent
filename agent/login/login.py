import json
import os
import requests
import time
import urllib.parse
import webbrowser

def main():
    auth_url = "https://login.live.com/oauth20_authorize.srf?client_id=00000000402b5328&response_type=code&redirect_uri=https://login.live.com/oauth20_desktop.srf&scope=XboxLive.signin offline_access"
    webbrowser.open(auth_url)
    print("Please paste the full URL you were redirected to after logging in.")
    redirect_url = input("Redirect URL: ").strip()
    parsed_url = urllib.parse.urlparse(redirect_url)
    MOAuth_code = urllib.parse.parse_qs(parsed_url.query).get("code", [None])[0]

    token_url = "https://login.live.com/oauth20_token.srf"
    token_response = requests.post(token_url, data={
        "client_id": "00000000402b5328",
        "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
        "grant_type": "authorization_code",
        "code": MOAuth_code,
        "scope": "XboxLive.signin offline_access"
    }).json()
    MOAuth_token = token_response["access_token"]

    xbl_response = requests.post(
        "https://user.auth.xboxlive.com/user/authenticate",
        json={
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": f"d={MOAuth_token}"
            },
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT"
        },
        headers={"Content-Type": "application/json"}
    ).json()
    xbl_token = xbl_response["Token"]
    xbl_userhash = xbl_response["DisplayClaims"]["xui"][0]["uhs"]

    xsts_response = requests.post(
        "https://xsts.auth.xboxlive.com/xsts/authorize",
        json={
            "Properties": {
                "SandboxId": "RETAIL",
                "UserTokens": [xbl_token]
            },
            "RelyingParty": "rp://api.minecraftservices.com/",
            "TokenType": "JWT"
        },
        headers={"Content-Type": "application/json"}
    ).json()
    xsts_token = xsts_response["Token"]

    mc_auth_response = requests.post(
        "https://api.minecraftservices.com/authentication/login_with_xbox",
        json={
            "identityToken": f"XBL3.0 x={xbl_userhash};{xsts_token}"
        },
        headers={"Content-Type": "application/json"}
    ).json()
    access_token = mc_auth_response["access_token"]
    weird_username = mc_auth_response["username"]
    
    profile_response = requests.get(
        "https://api.minecraftservices.com/minecraft/profile",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()
    username = profile_response["name"]
    user_id = profile_response["id"]
    if not access_token or not username:
        print("Login failed. Please check your credentials and try again.")
        return

    print(f"Login successful!\nUsername: {username}\nThis will be saved to info.json.")

    now_dir = os.path.dirname(__file__)
    info_path = os.path.join(now_dir, "info.json")
    with open(info_path, "r", encoding="utf-8") as f:
        info = json.load(f)
    info["access_token"] = access_token
    info["username"] = username
    info["id"] = user_id
    info["weird_username"] = weird_username

    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=4)
    time.sleep(1)

if __name__ == "__main__":
    main()