import tkinter as tk
from tkinter import scrolledtext

def send_message(event=None):
    # Shiftキーが押されている場合は改行を許可
    if event and event.state == 0x0001:  # Shiftキーの状態は state == 0x0001
        return
    
    message = message_entry.get("1.0", tk.END).strip()  # 入力されたメッセージを取得
    if message:  # メッセージが空でない場合
        display_area.configure(state='normal')  # テキストエリアを編集可能に
        display_area.insert(tk.END, message + "\n")  # メッセージを表示エリアに追加
        display_area.configure(state='disabled')  # テキストエリアを編集不可に
        message_entry.delete("1.0", tk.END)  # 入力欄をクリア
    return 'break'

# Tkinterウィンドウの初期化
root = tk.Tk()
root.title("メッセージアプリ")
# ウィンドウのサイズと位置を設定
root.geometry("600x700") # 横幅x高さ+X座標+Y座標


# スクロール可能なテキストエリア（表示エリア）
display_area = scrolledtext.ScrolledText(root, state='disabled', height=30)
display_area.pack(padx=10, pady=5)

# メッセージ入力欄
message_entry = tk.Text(root, height=3)
message_entry.pack(padx=10, pady=5)
message_entry.bind("<Return>", send_message)  # エンターキーにsend_messageをバインド

# 送信ボタン
send_button = tk.Button(root, text="送信", command=send_message)
send_button.pack(pady=5)

# Tkinterイベントループの開始
root.mainloop()