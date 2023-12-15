# Online-Chat-Messenger
Online-Chat-Messengerは、リアルタイムでの通信を可能にするCLIで動くシンプルなチャットアプリケーションです。</br>
ユーザーはチャットルームを作成し、他のユーザーはチャットルームに参加してメッセージを交換することができます。


https://github.com/Recursion-GroupB-Backend/Online-Chat-Messenger/assets/69625901/988e47ef-3431-405d-a736-8e8efc375228



TCPとUDP通信の役割

- TCP通信ではチャットの参加・作成に使います
- UDP通信はユーザー間のメッセージ交換に使われます

# **Install**

リポジトリをクローンします：

```bash
git clone https://github.com/Recursion-GroupB-Backend/Online-Chat-Messenger.git
cd Online-Chat-Messenger
```

必要なライブラリをインストールします：

```bash
pip install -r requirements.txt
```

# Usage

## サーバーの起動：

```bash
python3 -m server.server
```

## クライアントの起動：

```bash
python -m client.client
```

## チャットの開始
チャットルームに参加するか、新しいルームを作成します。

ルームに参加するには、ルーム名とパスワードを入力します。</br>
新しいルームを作成するには、ルーム名とパスワード（任意）を設定します。</br>
チャットルーム内でメッセージを送受信します。他のユーザーも同じルームに参加していれば、リアルタイムでメッセージのやり取りが可能です。
通信は暗号化されているので安心してチャットが楽しめます。

# Documents

[wiki](https://github.com/Recursion-Group-B/card-game/wiki)

[要件定義](https://github.com/Recursion-Group-B/card-game/wiki/%E8%A6%81%E4%BB%B6%E5%AE%9A%E7%BE%A9)

[規約](https://github.com/Recursion-Group-B/card-game/wiki/%E8%A6%8F%E7%B4%84)

[設計](https://github.com/Recursion-Group-B/card-game/wiki/%E8%A8%AD%E8%A8%88)

[議事録](https://github.com/Recursion-Group-B/card-game/wiki/%E8%AD%B0%E4%BA%8B%E9%8C%B2)



# Contributors
<a href="https://github.com/Recursion-GroupB-Backend/Online-Chat-Messenger/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Recursion-GroupB-Backend/Online-Chat-Messenger" />
</a>
