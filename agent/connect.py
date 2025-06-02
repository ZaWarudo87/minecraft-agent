import json
import os
# import time

from minecraft.authentication import AuthenticationToken
from minecraft.networking.connection import Connection
from minecraft.networking.packets import Packet, DisconnectPacket

from .login import login
from .agent import start
from . import global_var as gv

now_dir = os.path.dirname(__file__)

def connect() -> None:
    token = AuthenticationToken(gv.info["username"], gv.info["access_token"], " ")
    token.profile.name = gv.info["username"]
    token.profile.id_ = gv.info["id"]
    if not token.authenticated:
        print("You haven't logged in yet, please login first.")
        relogin()
        return
    gv.conn = Connection(gv.info["server"], gv.info["port"], username=gv.info["username"], auth_token=token)
    gv.conn.connect()
    gv.conn.register_packet_listener(handle_disconnect, DisconnectPacket)
    gv.conn.exception_handler = handle_exception
    print(f"Connecting to server {gv.info['server']}:{gv.info['port']} as {gv.info['username']}...")

    try:
        start()
        # while True:
        #     time.sleep(1)
    except KeyboardInterrupt:
        print("KeyboardInterrupt(ctrl+c) received, shutting down...")
        gv.conn.disconnect()
    except Exception as e:
        print(f"Error during connection: {e}")
        gv.conn.disconnect()
        relogin()

def relogin() -> None:
    if input("Do you want to re-login? (y/n): ").strip().lower() == 'y':
        login.main()
        gv.load_info()
        connect()

def handle_disconnect(pkt: Packet) -> None:
    print(f"Disconnected from server: {pkt.reason}")
    relogin()

def handle_exception(pkt: Packet) -> None:
    print(f"Exception occurred: {pkt.exception}")
    relogin()

if __name__ == "__main__":
    try:
        connect()
    except KeyboardInterrupt:
        print("KeyboardInterrupt(ctrl+c) received, shutting down...")
    except Exception as e:
        print(f"Error connecting to server: {e}")
        relogin()