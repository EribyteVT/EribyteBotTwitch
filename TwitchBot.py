from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.type import AuthScope, ChatEvent
from twitchAPI.helper import first
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
from twitchAPI.object.eventsub import ChannelPointsCustomRewardRedemptionAddEvent
from twitchAPI.eventsub.websocket import EventSubWebsocket
import asyncio
from CrudWrapper import CrudWrapper
import random
from Secrets import * 

xp_dict = {"ec9ed023-1aed-4098-b955-73c249ab4567":12,
           "74a435cb-e067-41ac-ba6e-dddd88b11d86":84,
           "648833a2-d3f5-4c3f-8644-b9face6ad329":36}

reward_xps = list(xp_dict.keys())

crudWrapper = CrudWrapper("LOCAL")
twitch = None
chat = None

async def on_ready(ready_event: EventData):
    await ready_event.chat.join_room("EribyteVT")
    

async def add_xp_handler(id,xp_to_add, name, update):
    data = crudWrapper.getAssociatedFromTwitch(id)

    #not in db at all
    if(data == None or data == [] or data[0] == None):
        data = [crudWrapper.getDataFromTwitchdId(id)]

    total_xp = 0

    for account in data:
        total_xp += account['xp']    

    levelBefore = crudWrapper.getLevelFromXp(total_xp)

    #if new account or time between messages is enuf, add xp
    data = crudWrapper.addXpbyTwitchId(xp_to_add,id,update)
    total_xp += xp_to_add

    levelAfter = crudWrapper.getLevelFromXp(total_xp)
        
    if(levelAfter > levelBefore):
        await chat.send_message("eribytevt",f"Congratulations to @{name} for reaching level {levelAfter}!!!!")


async def on_message(msg: ChatMessage):
    id = msg.user.id

    data = crudWrapper.getDataFromTwitchdId(id)

    name  = msg.user.name 

    #if new account or time between messages is enuf, add xp
    if(data['lastMessageXp']==None or crudWrapper.enoughTime(data['lastMessageXp'])):
        xp_awarded_amount = random.randint(1,5)
        await add_xp_handler(id,xp_awarded_amount,name,True)

    

async def ping(cmd: ChatCommand):
    await cmd.reply("Pong!")

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

async def handle_xp(data: ChannelPointsCustomRewardRedemptionAddEvent):
    data = data.to_dict()
    id = data["event"]['reward']['id']

    user_id = data['event']['user_id']

    user_name = data['event']['user_name']

    if(id in reward_xps):
        bonus_xp = xp_dict[id]
    else:
        bonus_xp = data["event"]["reward"]["cost"]//150

    await add_xp_handler(user_id,bonus_xp,user_name,False)
    
    name = data['event']['reward']['title']




    print(f"{name}:{id}")


async def run():
    global twitch, chat
    TARGET_SCOPES = [AuthScope.MODERATOR_READ_FOLLOWERS,AuthScope.CHANNEL_MANAGE_REDEMPTIONS,AuthScope.USER_READ_SUBSCRIPTIONS,AuthScope.MODERATOR_READ_CHATTERS,AuthScope.MODERATOR_MANAGE_SHOUTOUTS,AuthScope.CHAT_READ,AuthScope.CHANNEL_MANAGE_RAIDS,AuthScope.MODERATOR_MANAGE_SHOUTOUTS,
                     AuthScope.CHAT_EDIT,AuthScope.MODERATOR_MANAGE_SHOUTOUTS,AuthScope.CHANNEL_READ_REDEMPTIONS]

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

    twitchChannel = await Twitch(APP_ID, APP_SECRET)
    helperChannel = UserAuthenticationStorageHelper(twitchChannel, TARGET_SCOPES,"Eri-Token.json")
    await helperChannel.bind()

    eventsub = EventSubWebsocket(twitchChannel)
    eventsub.start()

    user = await first(twitchChannel.get_users())
    print(user.id)

    await eventsub.listen_channel_points_custom_reward_redemption_add(user.id, callback=handle_xp)

    

asyncio.run(run())