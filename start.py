import subprocess

if __name__ == "__main__":
    print("This agent can only play in Minecraft Java Edition v1.18.1 or 1.18.")

    if input("Do you want to build a new Minecraft server here? (y/n): ").strip().lower() == 'y':
        subprocess.Popen(["cmd.exe", "/c", "start", "start_server.bat"], cwd="server")
        print("Minecraft server started.")