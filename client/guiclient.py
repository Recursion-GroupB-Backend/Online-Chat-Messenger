import threading
import tkinter as tk
from tkinter import scrolledtext
from constants.operation import Operation
from .client import Client

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
        self.root.geometry("500x500+500+50") # 横幅x高さ+X座標+Y座標

        # ユーザー名入力フィールド
        tk.Label(self.root, text="User Name").pack(padx=10, pady=5)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack(padx=10, pady=5)

        # チャットルーム名入力フィールド
        tk.Label(self.root, text="Chat Room Name").pack(padx=10, pady=5)
        self.room_name_entry = tk.Entry(self.root)
        self.room_name_entry.pack(padx=10, pady=5)

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
            "port": self.udp_client_address[1]
        }
        return self.create_tcp_protocol(operation_payload)

    def udp_send_message_tkinter(self,event=None):
        # トークンを使ったUDPでの送信処理
        # Shiftキーが押されている場合は改行を許可
        if event and event.state == 0x0001:  # Shiftキーの状態は state == 0x0001
            return
        message = self.message_entry.get("1.0", tk.END).strip()  # 入力されたメッセージを取得
        if (2 + len(self.room_name) + len(self.token) + len(message.encode()) > GuiClient.BUFFER_SIZE):
            print(f'Messeges must be equal to or less than {GuiClient.BUFFER_SIZE} bytes')
        try:
            message_byte = self.udp_message_encode(message)
            self.udp_client_sock.sendto(message_byte, (self.server_address, self.udp_server_port))
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
        self.operation_code = operation
        self.tcp_connect_server()
        
        # UDP受信スレッドを開始        
        thread_receive_message = threading.Thread(target=self.udp_receive_message, daemon=True)
        thread_receive_message.start()
        
        # 最初のウィンドウを隠す
        self.root.withdraw()
        
        # チャットウィンドウのセットアップ
        self.chat_window = tk.Toplevel(self.root)
        self.chat_window.title(f"Chat room - '{self.room_name}'")
        # ウィンドウのサイズと位置を設定        
        self.chat_window.geometry("600x800+500+50") # 横幅x高さ+X座標+Y座標
        
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
        send_button = tk.Button(self.chat_window, text="送信", command=self.udp_send_message_tkinter)
        send_button.pack(pady=5) 
        
        # チャットウィンドウが閉じられた際の処理
        self.chat_window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def udp_receive_message(self):
        try:
            while True:
                data, _ = self.udp_client_sock.recvfrom(4096)
                user_name_size = data[0]
                message_size = data[1]
                user_name = data[2: 2 + user_name_size]
                message = data[2 + user_name_size:]
                
                if (message) and (user_name.decode('utf-8') != self.user_name):
                    self.display_area.configure(state='normal')                             # テキストエリアを編集可能に
                    self.display_area.insert(tk.END, user_name.decode('utf-8') + ":" + message.decode('utf-8') + "\n")        # メッセージを表示エリアに追加
                    self.display_area.configure(state='disabled')                           # テキストエリアを編集不可に
                    
                    print(f"{user_name.decode('utf-8')}：{message.decode('utf-8')}")
        finally:
            print('socket closing')
            self.udp_client_sock.close()
    
    def on_closing(self):
        # 最初のウィンドウを再表示
        self.root.deiconify()
        self.chat_window.destroy()

    def shutdown(self):
        print("Client is shutting down.")
        self.tcp_client_sock.close()
        self.udp_client_sock.close()
        self.chat_window.destroy()
        self.chat_window.destroy()
        self.root.destroy()

if __name__ == "__main__":
    gui_client = GuiClient()
    gui_client.root.mainloop()