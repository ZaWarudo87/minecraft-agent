from minecraft.authentication import AuthenticationToken
from minecraft.exceptions import YggdrasilError

def login_to_minecraft():
    print("=== Minecraft Login ===")
    username = input("Enter your Mojang account email/username: ")
    password = input("Enter your password: ")

    token = AuthenticationToken()

    # try:
    #     success = token.authenticate(username, password)
    #     if success:
    #         print(f"Login successful!")
    #         print(f"Username: {token.profile.name}")
    #         print(f"UUID: {token.profile.id_}")
    #         print(f"Access Token: {token.access_token}")
    #         print(f"Client Token: {token.client_token}")
    #     else:
    #         print("Login failed for unknown reasons.")
    # except YggdrasilError as e:
    #     print(f"Login failed with error: {e}")

if __name__ == "__main__":
    login_to_minecraft()