import os
import json
import base64
import discord
import requests

from dotenv import load_dotenv
from discord import Interaction
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GELBOORU_USER = os.getenv('GELBOORU_USER_ID')
GELBOORU_KEY = os.getenv('GELBOORU_API_KEY')
E621_USER = os.getenv('E621_USERNAME')
E621_KEY = os.getenv('E621_API_KEY')

client = commands.Bot(command_prefix="o:", intents= discord.Intents.default())

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    await client.tree.sync()


@client.tree.command(name="gelbooru", description="get an image from gelbooru", nsfw=True)
async def gelbooru(interaction : Interaction, tags:str = 'none'):
    await interaction.response.defer()

    defaultTags = ['sort:random']
    tags = getTagList(tags, defaultTags)
    url = f'https://gelbooru.com/index.php?page=dapi&s=post&q=index&limit=1&json=1&user_id={GELBOORU_USER}&api_key={GELBOORU_KEY}&tags=' + '+'.join(tags)

    response = requests.get(url)

    if response.status_code == 200:
        data = json.loads(response.text)

        if data['@attributes']['count'] == 0:
            missingTags = []
            for tag in tags:
                tagResponse = requests.get(f'https://gelbooru.com/index.php?page=dapi&s=tag&q=index&json=1&user_id={GELBOORU_USER}&api_key={GELBOORU_KEY}&name={tag}')
                tagData = json.loads(tagResponse.text)
                if tagData['@attributes']['count'] == 0:
                    missingTags += [tag]
            if len(missingTags) > 0:
                embed = discord.Embed(color=0xDC322F, description=f'```ansi\n\u001b[1;31mUnknown tag(s): \u001b[0m{getStringFromTags(missingTags)}```')
                await interaction.followup.send(embed=embed)
                return

            embed = discord.Embed(color=0xDC322F, description=f'```ansi\n\u001b[1;31m0 \u001b[0mresults found```').add_field(name='', value=f'```ansi\n\u001b[0;31mTags: \u001b[0m{getStringFromTags(tags)}```')
            await interaction.followup.send(embed=embed)
            return

        post = data['post'][0]
        url = 'https://gelbooru.com/index.php?page=post&s=view&id=' + str(post['id'])
        
        description = f'```ansi\n\u001b[0;34mTags: \u001b[0m{getStringFromTags(tags)}```'

        embed = discord.Embed(title=post['id'], url=url, color=0x00A8FC, description=description).set_image(url=post['file_url'])
        await interaction.followup.send(embed=embed)
        return

    await interaction.followup.send(f'Error: {response.status_code}')


@client.tree.command(name="e621", description="get an image from e621", nsfw=True)
async def e621(interaction : Interaction, tags:str = 'none'):
    await interaction.response.defer()
    
    defaultTags = ['order:random']
    tags = getTagList(tags, defaultTags)
    url = 'https://e621.net/posts.json?limit=1&tags='

    for tag in tags:
        url += tag + '+'

    auth = base64.b64encode((f'{E621_USER}:{E621_KEY}').encode('UTF-8')).decode('UTF-8')
    response = requests.get(url, headers={'Authorization': f'Basic {auth}', 'User-Agent':f'Discord bot Gynoid (by {E621_USER} on e621)'})

    if response.status_code == 200:
        data = json.loads(response.text)
        
        if data['posts'] == []:
            embed = discord.Embed(color=0xDC322F, description=f'```ansi\n\u001b[0;31m0 \u001b[0mresults found```')
            await interaction.followup.send(embed=embed)
            return
        
        post = data['posts'][0]

        url = 'https://e621.net/posts/' + str(post['id'])
        tagList = str(tags).replace('[', '').replace(']', '').replace('\'', '').replace('_', ' ')
        description = f'```ansi\n\u001b[0;34mTags: \u001b[0m{tagList}```'

        embed = discord.Embed(title=post['id'], url=url, color=0x00A8FC, description=description).set_image(url=post['file']['url'])

        await interaction.followup.send(embed=embed)
        return

    await interaction.followup.send(f'Error: {response.status_code}')


@client.tree.command(name="help", description="list all commands")
async def help(interaction : Interaction):
    await interaction.response.defer()
    
    embed = discord.Embed(color=0x00A8FC)
    embed.add_field(name='/gelbooru `tags`', value='get a post from https://gelbooru.com/\n\nexample: **/gelbooru** `cat_ears rating:safe sort:random score:>150`\nwill get a random post with the tag cat ears, rated safe with a score greater than 150\nhttps://gelbooru.com/index.php?page=help&topic=cheatsheet', inline=False)
    embed.add_field(name='/e621 `tags`', value='get a post from https://e621.net/\n\nexample: **/e621** `fluffy_tail rating:explicit order:score -animated`\nwill get the highest scored post with the fluffy tail tag that is not animated\nhttps://e621.net/help/cheatsheet')
    
    await interaction.followup.send(embed=embed)


def getTagList(tags, defaultTags):
    if tags == 'none':
        return defaultTags
    else:
        for defaultTag in defaultTags:
            if defaultTag.startswith('-') and tags.find(defaultTag[1:]) == -1:
                tags +=  ' ' + defaultTag
            elif ':' in defaultTag and tags.find(defaultTag[0:defaultTag.find(':')]) == -1:
                tags +=  ' ' + defaultTag
            elif tags.find('-' + defaultTag) == -1 and ':' not in defaultTag and not defaultTag.startswith('-'):
                tags += ' ' + defaultTag

    return tags.split()


def getStringFromTags(tags):
    return ', '.join(tags).replace('_', ' ')

client.run(TOKEN)