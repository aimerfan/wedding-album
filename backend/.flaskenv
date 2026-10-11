# flask 指令（flask run、flask seed…）啟動時自動讀這個檔，只用在開發。
# 正式環境由 WSGI 伺服器直接呼叫 create_app()，不會讀到這裡。
# 這裡只放可以公開的設定；機密（正式的 EVENT_CODE 等）不要寫進來。
FLASK_APP=app
FLASK_DEBUG=1
