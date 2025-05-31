import json
import subprocess

from agent import connect
from agent.login import login

if __name__ == "__main__":
    print("This agent can only play in Minecraft Java Edition v1.18.1 or 1.18.")

    with open("agent/login/info.json", "r", encoding="utf-8") as f:
        info = json.load(f)
    print("This is an account information:")
    print(f"\tUsername     : {info["username"]}")
    print(f"\tUUID         : {info["id"]}")
    print(f"\tAccess Token : {info["access_token"]}")
    print("This account is used to connect to the server and get world packets.")
    print("THIS ACCOUNT MUST **NOT** BE THE SAME AS THE ONE THE AGENT WILL USE LATER.")
    if input("Do you need to login for this account? (y/n): ").strip().lower() == 'y':
        login.main()

    if input("Do you want to build a new Minecraft server here? (y/n): ").strip().lower() == 'y':
        subprocess.Popen(["cmd.exe", "/c", "start", "start_server.bat"], cwd="server")
        print("Minecraft server started.")
    else:
        print(f"Remember to set 'op {info["username"]}' in the server.")

    server = input(f"Enter the server address (default: {info["server"]}): ").strip()
    if not server:
        server = info["server"]
    else:
        info["server"] = server
    port = input(f"Enter the server port (default: {info["port"]}): ").strip()
    if not port:
        port = info["port"]
    else:
        port = int(port)
        info["port"] = port

    agent_name = input(f"The account that will be controlled by the agent (default: {info["agent_name"]}): ").strip()
    if not agent_name:
        agent_name = info["agent_name"]
    else:
        info["agent_name"] = agent_name
    master_name = input(f"The player that the agent will follow (default: {info["master_name"]}): ").strip()
    if not master_name:
        master_name = info["master_name"]
    else:
        info["master_name"] = master_name
    with open("agent/login/info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=4)
    print(f"Please start Minecraft and connect to the server with the account '{agent_name}'. Ask '{master_name}' to join as well.")
    print("Starting the agent...")
    connect.connect()