from discord import Game
from discord.ext.commands import Bot
from discord import *
import os
import datetime

from lib.diff_checker import get_new, props_sorted
from lib.cycle_checker import get_cycle_info
from lib.blog import parse_posts, get_posts

BOT_PREFIX = "!"
BOT_TOKEN = os.environ.get("DISCORD_TOKEN")
bot = Bot(command_prefix=BOT_PREFIX)


commands_list = [
    "!Nexus",
    "!Proposals",
    "!Cycle",
    "!News"
]

# For sending to the #proposals channel

# await client.send_message(client.get_channel('370342005785755650'),
# (str(props_list) + "\n" + context.message.author.mention))


def prepare_news():
    posts = parse_posts(get_posts())

    fancy_blog = str()

    date = datetime.datetime.now()

    for post in posts.values():
        try:
            timestamp_ms = post['timestamp']
            timestamp = (timestamp_ms / 1000.0)
            date = datetime.datetime.fromtimestamp(timestamp)
        except Exception as e:
            print("Failed")
            print(post['timestamp'])
            print(e)

        fancy_blog += "-------------------------------"
        fancy_blog += '\n'
        fancy_blog += "**Title:** {}".format(post['title'])
        fancy_blog += "\n"
        fancy_blog += "**Subtitle:** {}".format(post['subtitle'])
        fancy_blog += "\n"
        fancy_blog += "**URL:** <{}>".format(post['url'])
        fancy_blog += "\n"
        fancy_blog += "**Date Published:** _{}_".format(date.strftime("%B %d, %Y"))
        fancy_blog += "\n"

    return fancy_blog


def prepare_proposals():
    proposals = props_sorted()
    # print(proposals)
    mn_count = get_cycle_info()['general']['consensus_masternodes']

    props_list = []

    for prop in proposals:
        if prop['will_be_funded'] is True:
            abs_votes = prop['yes'] - prop['no']
            percentage = round(((abs_votes / mn_count) * 100), 2)

            # Shorten titles
            # prop.update({"title": (prop['title'][:60] + "...")})

            # Add to list
            props_list.append((prop['title'], prop['dw_url'], abs_votes, percentage))

    proposal_messages = list()
    for prop in props_list:
        fancy_message = str() # reset each iteration

        fancy_message += "-------------------------------"
        fancy_message += '\n'
        fancy_message += "**Title:** {}".format(prop[0])
        fancy_message += '\n'
        fancy_message += "**Absolute Votes:** {} -> _{}%_".format(prop[2], prop[3])
        fancy_message += "\n"
        fancy_message += "**Link:** <{}>".format(prop[1])
        fancy_message += "\n"

        proposal_messages.append(fancy_message)

    list_of_messages = list()

    if len(''.join(proposal_messages)) > 1600:
        new_message = str()  # declare this new string which ends up getting added to the list
        for proposal in proposal_messages:
            if len(new_message) > 1600:
                list_of_messages.append(new_message)
                new_message = str()  # reset this variable

            else:
                new_message += proposal

        list_of_messages.append(new_message)

    else:
        new_message = ''.join(proposal_messages)
        list_of_messages.append(new_message)

    return list_of_messages


def prepare_cycle():
    dc_data = get_new()
    cycle_info = dc_data['budget']
    proposal_info = dc_data['proposals']

    # print(cycle_info)

    # Calculations
    available_funds = float(cycle_info['total_amount']) - cycle_info['alloted_amount']
    payment_date = datetime.datetime.strptime(cycle_info['payment_date'], "%Y-%m-%d %H:%M:%S")
    voting_close = payment_date - datetime.timedelta(days=3.0245)

    avail = round(available_funds, 2)
    projection = 0
    total = round(float(cycle_info['total_amount']), 2)

    for prop in proposal_info:
        abs_votes = prop['yes'] - prop['no']
        prop.update({"abs_votes": abs_votes})

    for prop in proposal_info:
        if prop['abs_votes'] > 250:
            prop.update({"will_be_funded": True})
            projection += prop['monthly_amount']
        else:
            continue

    projection = round(projection, 2)
    fancy_message = str()

    now = datetime.datetime.now()
    countdown = voting_close - now

    fancy_message += "**Voting Closes In:** {}".format(str(countdown))
    fancy_message += "\n"
    fancy_message += "**Remaining Funds Available:**  {}/{}".format(avail, total)
    fancy_message += "\n"
    fancy_message += "**Remaining After Likely Allocation (Absolute Votes > 250):**  {}/{}".format(
        round((total - projection), 2), total)
    fancy_message += "\n"
    fancy_message += "**Voting Deadline (Estimated):**  {:%B %d, %Y @ %H:%M:%S} UTC".format(voting_close)
    fancy_message += "\n"
    fancy_message += "**Payout Date (Estimated):**  {:%B %d, %Y @ %H:%M:%S} UTC".format(payment_date)
    fancy_message += "\n \n"
    fancy_message += "_Exact timing is a projection based on average block times and may not be completely accurate._"

    return fancy_message


@bot.event
async def on_message(message):
    print("Triggered message")
    if message.author == bot.user:
        return

    # Help information
    reply = str()
    if message.content.upper().startswith('!NEXUS'):
        for command in commands_list:
            reply += (command + "\n")

        msg = "{} \n**Commands:** \n{}".format(message.author.mention, reply).format(message)

        await bot.send_message(message.channel, msg)

    # Blog
    if message.content.upper().startswith("!NEWS"):
        fancy_blog = prepare_news()
        if str(message.channel.type) == "private":
            pass
        else:
            await bot.send_message(message.channel, "{} Check your DM's for a reply.".format(message.author.mention))

        try:
            await bot.send_message(message.author, ("**Blog Posts** \n \n" +
                                                       str(fancy_blog) + "\n"))
        except Exception as e:
            print(e)
            await bot.send_message(message.author, "Failed to send message. We are investigating.")

    # Cycle information
    if message.content.upper().startswith('!CYCLE'):
        fancy_message = prepare_cycle()

        if str(message.channel.type) == "private":
            pass
        else:
            await bot.send_message(message.channel, "{} Check your DM's for a reply.".format(message.author.mention))

        try:
            await bot.send_message(message.author, ("**Current Cycle Information:** \n \n" +
                                                       str(fancy_message) + "\n"))
        except Exception as e:
            print(e)
            await bot.send_message(message.author, "Failed to send message. We are investigating.")

        """
        await client.send_message(message.channel, ("**Current Cycle Information:** \n \n" +
                                                    str(fancy_message) + "\n" + "@{}".format(message.author)))
        """

    # Proposals
    if message.content.upper().startswith('!PROPOSALS'):
        list_of_messages = prepare_proposals()

        print(message.author.mention)

        if str(message.channel.type) == "private":
            pass
        else:
            await bot.send_message(message.channel, "{} Check your DM's for a reply.".format(message.author.mention))

        try:
            for count, fancy_message in enumerate(list_of_messages):
                count += 1
                await bot.send_message(message.author, ("**Proposals that will be funded ({}/{}):** \n \n".format(count, len(list_of_messages)) + fancy_message + "\n"))

        except Exception as e:
            print("Most likely ran into a problem due to the length of the message.")
            print("Message 1 length: {}".format(len(fancy_message)))
            print("Message 2 length: {}").format(len(fancy_message_2))
            print(e)

            await bot.send_message(message.author, "Failed to send message. We are investigating.")

        """
        await client.send_message(message.channel, ("**Proposals that will be funded:** \n \n" +
                                                    str(fancy_message) + "\n" + "@{}".format(message.author)))
        """


@bot.event
async def on_ready():
    await bot.change_presence(game=Game(name="!Nexus to list commands", type=1))
    print("Logged in as " + bot.user.name)


if __name__ == '__main__':
    bot.run(BOT_TOKEN)
