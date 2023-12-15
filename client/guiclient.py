import threading
import tkinter as tk
from tkinter import scrolledtext
from constants.operation import Operation
from .client import Client
import struct

class GuiClient(Client):
    NAME_SIZE = 255
    ROOM_NAME_SIZE = 255
    HEADER_SIZE = 32
    BUFFER_SIZE = 4096

    def __init__(self, server_address = '127.0.0.1'):
        super().__init__(server_address)
        
        # 最初のウィンドウのセットアップ
        self.root = tk.Tk()
        self.root.title("Chat App")
        self.root.geometry("500x500") # 横幅x高さ+X座標+Y座標

        # ユーザー名入力フィールド
        tk.Label(self.root, text="User Name").pack(padx=10, pady=5)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack(padx=10, pady=5)

        # チャットルーム名入力フィールド
        tk.Label(self.root, text="Chat Room Name").pack(padx=10, pady=5)
        self.room_name_entry = tk.Entry(self.root)
        self.room_name_entry.pack(padx=10, pady=5)
        
        # パスワード
        tk.Label(self.root, text="Chat Room PassWord").pack(padx=10, pady=5)
        self.room_password_entry = tk.Entry(self.root)
        self.room_password_entry.pack(padx=10, pady=5)
        
        # チャットルーム入力確認ボタン
        enter_room_button = tk.Button(self.root, text="'CREATE' Chat Room", command=lambda: self.show_chat_window(Operation.CREATE_ROOM.value))
        enter_room_button.pack(pady=20)

        # チャットルーム入力確認ボタン
        enter_room_button = tk.Button(self.root, text="'JOIN' Chat Room", command=lambda: self.show_chat_window(Operation.JOIN_ROOM.value))
        enter_room_button.pack(pady=20)
    
    def create_tcp_request(self):
        # 必要に応じてパスワードや公開鍵などを追加        
        operation_payload = {
            "user_name":self.user_name,
            "ip": self.udp_client_address[0],
            "port": self.udp_client_address[1],
            "password": self.password,
            "public_key": self.encode_pem(self.client_public_key)
        }
        return self.create_tcp_protocol(operation_payload)

    def udp_send_message_tkinter(self,event=None):
        # Shiftキーが押されている場合は改行を許可
        if event and event.state == 0x0001:  # Shiftキーの状態は state == 0x0001
            return
        message = self.message_entry.get("1.0", tk.END).strip()  # 入力されたメッセージを取得

        encrypted_message = self.encrypt_message(message)
        if (2 + len(self.room_name) + len(self.token) + len(encrypted_message) > GuiClient.BUFFER_SIZE):
            print(f'Messeges must be equal to or less than {GuiClient.BUFFER_SIZE} bytes')
        try:
            encrypted_message_byte = self.udp_message_encode(encrypted_message)
            self.udp_client_sock.sendto(encrypted_message_byte, (self.server_address, self.udp_server_port))
        except Exception as e:
            print(f"Error sending message: {e}")
        if message:  # メッセージが空でない場合
            self.display_area.configure(state='normal')  # テキストエリアを編集可能に
            self.display_area.insert(tk.END,self.user_name + ":"+ message + "\n", "own_text")  # メッセージを表示エリアに追加
            self.display_area.configure(state='disabled')  # テキストエリアを編集不可に
            self.message_entry.delete("1.0", tk.END)  # 入力欄をクリア
        return 'break'

    def show_chat_window(self,operation):
        self.user_name = self.username_entry.get()
        self.room_name = self.room_name_entry.get()
        self.password = self.room_password_entry.get()
        self.operation_code = operation
        self.tcp_connect_server()
        
        # UDP受信スレッドを開始        
        thread_receive_message = threading.Thread(target=self.udp_receive_message, daemon=True)
        thread_receive_message.start()
        
        # 最初のウィンドウを隠す
        self.root.withdraw()
        
        # チャットウィンドウのセットアップ
        self.chat_window = tk.Toplevel(self.root)
        self.chat_window.title(f"'{self.user_name}' in Chat room - '{self.room_name}' ")
        # ウィンドウのサイズと位置を設定        
        self.chat_window.geometry("600x800") # 横幅x高さ+X座標+Y座標
        
        # スクロール可能なテキストエリア（表示エリア）
        self.display_area = scrolledtext.ScrolledText(self.chat_window, state='disabled', height=30)
        self.display_area.pack(padx=10, pady=5)
        # 赤色のテキスト用のタグを定義
        self.display_area.tag_configure("own_text", foreground="#505050")
        
        # メッセージ入力欄
        self.message_entry = tk.Text(self.chat_window, height=3)
        self.message_entry.pack(padx=10, pady=5)
        self.message_entry.bind("<Return>", self.udp_send_message_tkinter)  # エンターキーにudp_send_message_tkinterをバインド
        
        # 送信ボタン
        send_button = tk.Button(self.chat_window, text="send", command=self.udp_send_message_tkinter)
        send_button.pack(pady=5) 
        
        # チャットウィンドウが閉じられた際の処理
        self.chat_window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def udp_receive_message(self):
        try:
            while True:
                data, _ = self.udp_client_sock.recvfrom(4096)

                user_name_size, message_size = struct.unpack('!HH', data[:4])
                encrypted_user_name = data[4: 4 + user_name_size]
                # 暗号化されたユーザー名とメッセージを復号化
                encrypted_message = data[4 + user_name_size: 4 + user_name_size + message_size]

                try:
                    decrypted_user_name = self.decrypt_message(encrypted_user_name).decode('utf-8')
                    decrypted_message = self.decrypt_message(encrypted_message).decode('utf-8')
                    if (decrypted_message) and (decrypted_user_name != self.user_name):
                        self.display_area.configure(state='normal')                                                   # テキストエリアを編集可能に
                        self.display_area.insert(tk.END, decrypted_user_name + ":" + decrypted_message + "\n")        # メッセージを表示エリアに追加
                        self.display_area.configure(state='disabled')                                                 # テキストエリアを編集不可に
                    if "exit" == decrypted_message:
                        print("The host has closed the chat room.")
                        self.chat_window.destroy()
                        self.root.destroy()
                        self.shutdown()
                    if decrypted_user_name != self.user_name:
                        print(f"{decrypted_user_name}：{decrypted_message}")
                except Exception as e:
                    print(f"Error decrypting message: {e}")
                    continue

        except OSError:
            self.chat_window.destroy()
            self.root.destroy()
            self.shutdown()
        finally:
            print('socket closing')
            self.udp_client_sock.close()
    
    def on_closing(self):
        self.shutdown()

if __name__ == "__main__":
    gui_client = GuiClient()
    gui_client.root.mainloop()