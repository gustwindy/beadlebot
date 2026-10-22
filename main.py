import asyncio
import base64
import io
import json

from envparse import env
from nextcord.ext import commands
import nextcord

import api

bot = commands.Bot()
artists = []
last = 0

admins = [656132997422252042, 456476787556352011]
env.read_envfile(".env")


async def permissions(ctx: nextcord.Interaction):
    if ctx.user and ctx.user.id in admins:
        return True
    _ = await ctx.send("https://tenor.com/view/smooth-moves-vivid-stasis-hajimeli-avatar-gif-8171135286649739072")
    return False

def update_cache():
    global artists
    artists = api.list_artists()

@bot.slash_command()
async def new_artist(ctx: nextcord.Interaction,common_name: str = nextcord.SlashOption(description="The 'main' name of the artist"),aliases: str = nextcord.SlashOption(description="Delimited by commas")):
    if not await permissions(ctx): return
    final = [i.strip() for i in aliases.split(",")]

    req = api.new_artist(common_name, final)

    if req.status_code != 200:
        _ = await ctx.send(f"## error\n{json.loads(req.content)["message"]}")
    else:
        _ = await ctx.send(f"## new artist: `{common_name}`\n{", ".join(final)}")

    update_cache()

async def artist_complete(ctx: nextcord.Interaction,artist: str):
    if not artists:
        update_cache()

    autocomplete = {}
    for i in artists:
        if i["commonName"].startswith(artist):
            autocomplete[i["commonName"]] = str(i["id"])
    await ctx.response.send_autocomplete(autocomplete)

@bot.slash_command()
async def edit_aliases(ctx: nextcord.Interaction,artist: str = nextcord.SlashOption(autocomplete_callback=artist_complete),add_aliases: str = nextcord.SlashOption(description="Delimited by commas",required=False),remove_aliases: str = nextcord.SlashOption(description="Delimited by commas",required=False)):
    if not await permissions(ctx): return

    req = api.edit_aliases(
        int(artist),
        [i.strip() for i in add_aliases.split(",")] if add_aliases else [],
        [i.strip() for i in remove_aliases.split(",")] if remove_aliases else [],
    )
    resp = json.loads(req.content)

    if req.status_code != 200:
        _ = await ctx.send(f"## error\n{resp["message"]}")
    else:
        _ = await ctx.send(content=f"## new aliases\n{resp["aliases"]}")

    update_cache()


@bot.slash_command()
async def get_artist(ctx: nextcord.Interaction,artist: str = nextcord.SlashOption(autocomplete_callback=artist_complete)):
    if not await permissions(ctx): return

    for i in artists:
        if str(i["id"]) == artist:
            _ = await ctx.send(content=f"```json\n{json.dumps(i,indent=4)}\n```")

@bot.slash_command()
async def list_artists(ctx: nextcord.Interaction):
    if not await permissions(ctx): return

    update_cache()
    _ = await ctx.send(content=f"## artists\n```{"\n".join([i["commonName"] for i in artists])}```")

@bot.slash_command()
async def upload_drawing(ctx: nextcord.Interaction, image: nextcord.Attachment, artist: str = nextcord.SlashOption(autocomplete_callback=artist_complete)):
    if not await permissions(ctx): return

    if image.size > 20_000_000:
        _ = await ctx.send("image too big !! 20mb limit")
        return
    img = base64.b64encode(await image.read()).decode("ascii")

    req = api.new_drawings(int(artist), img)
    resp = json.loads(req.content)

    if req.status_code != 200:
        _ = await ctx.send(f"## error\n{resp["message"]}")
    else:
        _ = await ctx.send(content=f"gg ez id: {resp.get("id","?")}", files=[await image.to_file(filename="image.png")])

@bot.slash_command()
async def view_drawing(ctx: nextcord.Interaction,id: str = nextcord.SlashOption(description="this is an int or u will explode")):
    if not await permissions(ctx): return

    req = api.view_drawing(int(id))

    if req.status_code != 200:
        _ = await ctx.send(f"nope {json.loads(req.content)}")
    else:
        _ = await ctx.send(content="gg ez", files=[nextcord.File(io.BytesIO(req.content),filename="image.png")])

class Page(nextcord.ui.View):
    def __init__(self,drawings,nth=0):
        super().__init__(timeout=600)
        self.nth = nth
        self.drawings = drawings

    async def update(self, interaction: nextcord.Interaction):
        print(self.nth,len(self.drawings))
        self.nth = max(min(self.nth,len(self.drawings)-1),0)
        print(self.nth,len(self.drawings))
        
        await interaction.response.defer()
        await interaction.edit_original_message(content=f"one sec...")
        
        chosen = self.drawings[self.nth]
        view = Page(self.drawings,self.nth)
        req = await bot.loop.run_in_executor(None,api.view_drawing,chosen["id"])
        file = nextcord.File(io.BytesIO(req.content),filename="image.png")
        print(chosen)
        
        await interaction.edit_original_message(content=f"**drawing id: `{chosen["id"]}`** (page {self.nth})",file=file,view=view)
    
    @nextcord.ui.button(label="Last", style=nextcord.ButtonStyle.red)
    async def last(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.nth -= 1
        await self.update(interaction)


    @nextcord.ui.button(label="Next", style=nextcord.ButtonStyle.green)
    async def next(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.nth += 1
        await self.update(interaction)
    
@bot.slash_command()
async def show_drawings_of(ctx: nextcord.Interaction, artist: str = nextcord.SlashOption(autocomplete_callback=artist_complete)):
    if not await permissions(ctx): return

    drawings = api.list_drawings()
    filtered = []
    
    for i in drawings:
        if i["artist"] == int(artist):
            filtered.append(i)
    
    print(filtered)
    
    view = Page(filtered)
    await ctx.send("Click on one of the buttons below to start previewing.\nThe images are not sorted in any particular order.", view=view)


@bot.slash_command()
async def force_next(ctx: nextcord.Interaction,drawing_id: str = nextcord.SlashOption(description="this is an int or u will explode")):
    if not await permissions(ctx): return

    req = api.force_drawing(int(drawing_id))

    if req.status_code != 200:
        _ = await ctx.send(f"nope {json.loads(req.content)}")
    else:
        _ = await ctx.send(content=f"gg ez {drawing_id}")

bot.run(env.str("TOKEN"))
