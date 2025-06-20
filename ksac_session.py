from telethon.sync import TelegramClient

api_id = 25554948
api_hash = 'd0ef27a9bd3c7001c4605c40ee1303ff'
phone = '+85510734840'

client = TelegramClient('ksac_session', api_id, api_hash)
client.start(phone=phone)