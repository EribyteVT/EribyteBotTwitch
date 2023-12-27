from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.helper import first
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
import asyncio
from CrudWrapper import CrudWrapper
import random
from Secrets import * 

crudWrapper = CrudWrapper("LOCAL")
twitch = None

async def on_ready(ready_event: EventData):
    await ready_event.chat.join_room("EribyteVT")
    # you can do other bot initialization things in here

async def on_message(msg: ChatMessage):
    id = msg.user.id

    data = crudWrapper.getAssociatedFromTwitch(id)

    #not in db at all
    if(data == None or data == [] or data[0] == None):
        data = [crudWrapper.getDataFromTwitchdId(id)]

    twitch = None

    total_xp = 0

    for account in data:
        if(account['serviceName'] == 'twitch'):
            twitch = account
        total_xp += account['xp']    

    levelBefore = crudWrapper.getLevelFromXp(total_xp)

    #if new account or time between messages is enuf, add xp
    if(twitch['lastMessageXp']==None or crudWrapper.enoughTime(twitch['lastMessageXp'])):
        xp_awarded_amount = random.randint(1,5)
        data = crudWrapper.addXpbyTwitchId(xp_awarded_amount,id,True)
        total_xp += xp_awarded_amount

    levelAfter = crudWrapper.getLevelFromXp(total_xp)
        
    if(levelAfter > levelBefore):
        await msg.chat.send_message("eribytevt",f"Congratulations to @{msg.user.name} for reaching level {levelAfter}!!!!")

async def ping(cmd: ChatCommand):
    await cmd.reply("!discord")

async def getLevel(cmd: ChatCommand):
    id = cmd.user.id

    data = crudWrapper.getAssociatedFromTwitch(id)

    total_xp = 0

    for account in data:
        total_xp += account['xp']    

    level = crudWrapper.getLevelFromXp(total_xp)

    await cmd.reply(f"Level: {level}    XP: {total_xp}")

async def raid_shoutout(raid_event: dict):
    print(dict)
    user_id = raid_event['tags']['user-id']
    print(user_id)
    
    await twitch.send_a_shoutout("946740776",user_id,"1004092875")

async def run():
    global twitch
    TARGET_SCOPES = [AuthScope.MODERATOR_READ_FOLLOWERS,AuthScope.CHANNEL_MANAGE_REDEMPTIONS,AuthScope.USER_READ_SUBSCRIPTIONS,AuthScope.MODERATOR_READ_CHATTERS,AuthScope.MODERATOR_MANAGE_SHOUTOUTS,AuthScope.CHAT_READ,AuthScope.CHANNEL_MANAGE_RAIDS,AuthScope.MODERATOR_MANAGE_SHOUTOUTS,
                     AuthScope.CHAT_EDIT,AuthScope.MODERATOR_MANAGE_SHOUTOUTS]

    twitch = await Twitch(APP_ID, APP_SECRET)
    helper = UserAuthenticationStorageHelper(twitch, TARGET_SCOPES)
    await helper.bind()

    chat = await Chat(twitch)

    chat.register_event(ChatEvent.MESSAGE, on_message)
    chat.register_event(ChatEvent.READY, on_ready)
    chat.register_event(ChatEvent.RAID,raid_shoutout)

    chat.register_command('ping', ping)
    chat.register_command('getLevel', getLevel)

    chat.start()

    

asyncio.run(run())