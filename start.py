import json
import subprocess

from agent import run

if __name__ == "__main__":
    print("This agent can only play in Minecraft Java Edition v1.18.1 or 1.18.")

    if input("Do you want to build a new Minecraft server here? (y/n): ").strip().lower() == 'y':
        subprocess.Popen(["cmd.exe", "/c", "start", "start_server.bat"], cwd="server")
        print("Minecraft server started.")

    with open("agent/login/info.json", "r", encoding="utf-8") as f:
        info = json.load(f)
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
    with open("agent/login/info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, indent=4)

    print("Starting the agent...")
    run.main()