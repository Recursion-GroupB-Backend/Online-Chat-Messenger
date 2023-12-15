# Online-Chat-Messenger
Online-Chat-Messengerは、リアルタイムでの通信を可能にするCLIで動くシンプルなチャットアプリケーションです。</br>
ユーザーはチャットルームを作成し、他のユーザーはチャットルームに参加してメッセージを交換することができます。


https://github.com/Recursion-GroupB-Backend/Online-Chat-Messenger/assets/69625901/988e47ef-3431-405d-a736-8e8efc375228



TCPとUDP通信の役割

- TCP通信ではチャットの参加・作成に使います
- UDP通信はユーザー間のメッセージ交換に使われます

# Features
Online-Chat-Messengerは、以下の機能を備えています：

- チャットルームの作成と管理：ユーザーは自分自身でチャットルームを作成・参加ができます
- リアルタイムチャット：ユーザーはリアルタイムでメッセージを交換することができます
- 複数ユーザー対応：複数のユーザーが同時にチャットルームに参加し、コミュニケーションをとることができます。
- セキュアな通信：TCPとUDPを使用した安全な通信で、ユーザー間のメッセージは暗号化されています。
- ユーザー認証：チャットルームへのアクセスにはユーザー名、チャットルーム名、パスワードが必要です。

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

[wiki](https://github.com/Recursion-Group-B/card-game/wiki](https://github.com/Recursion-GroupB-Backend/Online-Chat-Messenger/wiki))

[アクティビティ図](https://github.com/Recursion-GroupB-Backend/Online-Chat-Messenger/wiki#%E3%82%A2%E3%82%AF%E3%83%86%E3%82%A3%E3%83%93%E3%83%86%E3%82%A3%E5%9B%B3)

[シーケンス図](https://github.com/Recursion-GroupB-Backend/Online-Chat-Messenger/wiki#%E3%82%B7%E3%83%BC%E3%82%B1%E3%83%B3%E3%82%B9%E5%9B%B3)

[クラス図](https://github.com/Recursion-GroupB-Backend/Online-Chat-Messenger/wiki#%E3%82%AF%E3%83%A9%E3%82%B9%E5%9B%B3)

[議事録](https://github.com/Recursion-GroupB-Backend/dev-log)



# Contributors
<a href="https://github.com/Recursion-GroupB-Backend/Online-Chat-Messenger/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Recursion-GroupB-Backend/Online-Chat-Messenger" />
</a>
