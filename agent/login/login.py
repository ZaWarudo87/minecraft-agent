import json
import os
import requests

from msal import PublicClientApplication

def main():
    xbox_client_id = "00000000402b5328"  # Xbox Live client ID
    authority = "https://login.microsoftonline.com/consumers"
    app = PublicClientApplication(xbox_client_id, authority=authority)
    links = app.initiate_device_flow(scopes=["user.read"])
    print(f"flow: {links}")
    print(f"Please visit {links['verification_uri']} and enter the code: {links['user_code']}")
    result = app.acquire_token_by_device_flow(links)
    MOAuth_token = result["access_token"]

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
    username = mc_auth_response["username"]

    print(f"Login successful!\n\tAccess Token: {access_token}\n\tUsername: {username}\nThis will be saved to info.json.")

    now_dir = os.path.dirname(__file__)
    info_path = os.path.join(now_dir, "info.json")
    with open(info_path, "r", encoding="utf-8") as f:
        info = json.load(f)
    info["auth_token"] = access_token
    info["username"] = username

    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=4)

if __name__ == "__main__":
    main()