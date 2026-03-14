#!/usr/bin/env python3
"""
Discord Voice Bot for OpenClaw - Bidirectional Voice
- Joins voice channels
- Listens to speech and transcribes with Whisper
- Sends to OpenClaw for response
- Responds with ElevenLabs TTS
"""

import os
import io
import asyncio
import tempfile
import wave
import discord
from discord.ext import commands
import aiohttp

# Configuration
DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
WHISPER_URL = "http://127.0.0.1:8178/inference"
AGENT_URL = "http://127.0.0.1:8766/agent"
ELEVENLABS_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE = "onwK4e9ZLuTAKqWW03F9"  # Daniel

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Track voice connections
voice_connections = {}
listening_channels = set()


async def transcribe_audio(audio_file_path: str) -> str:
    """Send audio to Whisper for transcription."""
    converted_path = None
    try:
        # Convert to 16kHz mono WAV (whisper-cpp format)
        converted_path = audio_file_path.replace('.wav', '_converted.wav')
        proc = await asyncio.create_subprocess_exec(
            'ffmpeg', '-y', '-i', audio_file_path,
            '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le',
            converted_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()
        
        if proc.returncode != 0:
            print(f"[DEBUG] ffmpeg conversion failed")
            return ""
        
        async with aiohttp.ClientSession() as session:
            with open(converted_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename='audio.wav', content_type='audio/wav')
                data.add_field('response_format', 'json')
                
                async with session.post(WHISPER_URL, data=data, timeout=30) as resp:
                    response_text = await resp.text()
                    print(f"[DEBUG] Whisper status={resp.status}, response={response_text[:200]}")
                    if resp.status == 200:
                        import json
                        result = json.loads(response_text)
                        return result.get('text', '').strip()
                    else:
                        print(f"[DEBUG] Whisper error: {response_text}")
    except Exception as e:
        print(f"Transcription error: {e}")
    finally:
        # DEBUG: keep converted file for testing
        if converted_path:
            print(f"[DEBUG] Converted file saved at: {converted_path}")
            # try:
            #     os.unlink(converted_path)
            # except:
            #     pass
    return ""


async def get_agent_response(message: str, user_id: str) -> str:
    """Get response from OpenClaw agent."""
    try:
        # Add instruction to match user's language
        full_message = f"[Voice message - reply in the same language as the user, keep response concise for TTS]\n\n{message}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                AGENT_URL,
                json={"message": full_message, "session_id": f"discord-voice-{user_id}"},
                timeout=90
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get('response', '')
    except Exception as e:
        print(f"Agent error: {e}")
    return "Sorry, I couldn't generate a response."


async def generate_tts(text: str) -> bytes:
    """Generate TTS audio using ElevenLabs."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE}",
                headers={
                    "xi-api-key": ELEVENLABS_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2"
                },
                timeout=30
            ) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception as e:
        print(f"TTS error: {e}")
    return b""


async def play_audio(vc: discord.VoiceClient, audio_data: bytes):
    """Play audio in voice channel."""
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        f.write(audio_data)
        temp_path = f.name
    
    try:
        source = discord.FFmpegPCMAudio(temp_path)
        if vc.is_playing():
            vc.stop()
        vc.play(source)
        while vc.is_playing():
            await asyncio.sleep(0.1)
    finally:
        await asyncio.sleep(0.5)
        try:
            os.unlink(temp_path)
        except:
            pass


async def finished_callback(sink: discord.sinks.WaveSink, channel: discord.TextChannel, vc: discord.VoiceClient):
    """Called when recording is finished."""
    print(f"Recording finished, processing {len(sink.audio_data)} users...")
    
    for user_id, audio in sink.audio_data.items():
        # Save audio to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
            audio.file.seek(0)
            audio_bytes = audio.file.read()
            f.write(audio_bytes)
        
        # Debug: show audio file size and save sample
        file_size = len(audio_bytes)
        print(f"[DEBUG] User {user_id}: audio file size = {file_size} bytes")
        
        # Save a debug copy
        debug_path = f"/tmp/discord_audio_{user_id}.wav"
        with open(debug_path, 'wb') as df:
            df.write(audio_bytes)
        print(f"[DEBUG] Saved raw audio to {debug_path}")
        
        try:
            # Transcribe
            text = await transcribe_audio(temp_path)
            print(f"[DEBUG] Whisper returned: '{text}'")
            
            if not text or len(text.strip()) < 2:
                print(f"No speech detected from user {user_id}")
                continue
            
            # Filter out noise/artifacts
            if text.strip() in ['[BLANK_AUDIO]', '...', '.', '[MUSIC]', '[NOISE]']:
                continue
            
            user = bot.get_user(user_id)
            username = user.display_name if user else f"User {user_id}"
            
            print(f"[{username}] {text}")
            await channel.send(f"🎤 **{username}:** {text}")
            
            # Get response
            response = await get_agent_response(text, str(user_id))
            print(f"[Rez] {response[:100]}...")
            
            # Truncate for Discord if needed
            display_response = response[:1900] + "..." if len(response) > 1900 else response
            
            # Generate and play TTS
            audio_data = await generate_tts(response)
            if audio_data and vc.is_connected():
                await play_audio(vc, audio_data)
            
            await channel.send(f"🤖 **Rez:** {display_response}")
            
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass


@bot.event
async def on_ready():
    print(f"🤖 {bot.user} is online!")
    print(f"   Servers: {[g.name for g in bot.guilds]}")
    
    # Force sync commands to all guilds (instant instead of up to 1 hour)
    for guild in bot.guilds:
        try:
            synced = await bot.sync_commands(guild_ids=[guild.id], force=True)
            print(f"   ✅ Synced {len(synced) if synced else 'all'} commands to {guild.name}")
        except Exception as e:
            print(f"   ❌ Sync error for {guild.name}: {e}")


@bot.slash_command(name="join", description="Join je voice channel")
async def join(ctx: discord.ApplicationContext):
    """Join the user's voice channel."""
    if not ctx.author.voice:
        await ctx.respond("❌ Je moet in een voice channel zijn!", ephemeral=True)
        return
    
    channel = ctx.author.voice.channel
    
    if ctx.guild.id in voice_connections:
        await voice_connections[ctx.guild.id].move_to(channel)
    else:
        vc = await channel.connect()
        voice_connections[ctx.guild.id] = vc
    
    await ctx.respond(f"✅ Joined **{channel.name}**!\n\n"
                      f"**Commands:**\n"
                      f"• `/listen` - Start luisteren (5 sec)\n"
                      f"• `/talk` - Continu luisteren (stop met `/stop`)\n"
                      f"• `/ask <vraag>` - Tekst vraag met voice antwoord\n"
                      f"• `/say <tekst>` - Laat me iets zeggen\n"
                      f"• `/leave` - Verlaat voice channel")


@bot.slash_command(name="leave", description="Verlaat de voice channel")
async def leave(ctx: discord.ApplicationContext):
    """Leave the voice channel."""
    if ctx.guild.id in voice_connections:
        if ctx.guild.id in listening_channels:
            listening_channels.discard(ctx.guild.id)
        await voice_connections[ctx.guild.id].disconnect()
        del voice_connections[ctx.guild.id]
        await ctx.respond("👋 Tot ziens!")
    else:
        await ctx.respond("Ik ben niet in een voice channel.", ephemeral=True)


@bot.slash_command(name="listen", description="Luister en reageer (5 seconden)")
async def listen(ctx: discord.ApplicationContext, seconds: int = 5):
    """Listen for a set duration and respond."""
    if ctx.guild.id not in voice_connections:
        await ctx.respond("❌ Gebruik eerst `/join`!", ephemeral=True)
        return
    
    vc = voice_connections[ctx.guild.id]
    
    if seconds < 1 or seconds > 30:
        seconds = 5
    
    await ctx.respond(f"🎤 Luisteren voor {seconds} seconden... Spreek nu!")
    
    # Start recording - callback receives (sink, channel, *args)
    async def on_recording_done(sink, channel, *args):
        await finished_callback(sink, ctx.channel, vc)
    
    sink = discord.sinks.WaveSink()
    vc.start_recording(sink, on_recording_done, ctx.channel)
    
    # Wait
    await asyncio.sleep(seconds)
    
    # Stop recording
    vc.stop_recording()
    
    await ctx.send("📝 Verwerken...")


@bot.slash_command(name="talk", description="Start continu luisteren")
async def talk(ctx: discord.ApplicationContext):
    """Start continuous listening mode."""
    if ctx.guild.id not in voice_connections:
        await ctx.respond("❌ Gebruik eerst `/join`!", ephemeral=True)
        return
    
    vc = voice_connections[ctx.guild.id]
    
    if ctx.guild.id in listening_channels:
        await ctx.respond("Al aan het luisteren! Gebruik `/stop` om te stoppen.", ephemeral=True)
        return
    
    listening_channels.add(ctx.guild.id)
    await ctx.respond("🎤 **Continu luisteren gestart!**\n"
                      "Spreek en pauzeer - ik reageer na elke pauze.\n"
                      "Gebruik `/stop` om te stoppen.")
    
    # Continuous listening loop
    while ctx.guild.id in listening_channels:
        try:
            # Use an event to wait for callback completion
            processing_done = asyncio.Event()
            
            async def on_recording_done(sink, channel, *args):
                try:
                    await finished_callback(sink, ctx.channel, vc)
                finally:
                    processing_done.set()
            
            sink = discord.sinks.WaveSink()
            vc.start_recording(sink, on_recording_done, ctx.channel)
            
            await asyncio.sleep(5)  # Record 5 second chunks
            
            if ctx.guild.id in listening_channels and vc.is_connected():
                try:
                    vc.stop_recording()
                except:
                    pass
                # Wait for processing to complete before next recording
                try:
                    await asyncio.wait_for(processing_done.wait(), timeout=60)
                except asyncio.TimeoutError:
                    print("Processing timeout, continuing...")
            else:
                break
            
            # Small delay before next recording
            await asyncio.sleep(0.5)
                
        except Exception as e:
            print(f"Listening error: {e}")
            await asyncio.sleep(1)  # Brief pause before retry
    
    listening_channels.discard(ctx.guild.id)


@bot.slash_command(name="stop", description="Stop met luisteren")
async def stop(ctx: discord.ApplicationContext):
    """Stop continuous listening."""
    if ctx.guild.id in listening_channels:
        listening_channels.discard(ctx.guild.id)
        vc = voice_connections.get(ctx.guild.id)
        if vc and vc.recording:
            vc.stop_recording()
        await ctx.respond("🔇 Gestopt met luisteren.")
    else:
        await ctx.respond("Ik was niet aan het luisteren.", ephemeral=True)


@bot.slash_command(name="ask", description="Stel een vraag aan Rez (tekst)")
async def ask(ctx: discord.ApplicationContext, vraag: str):
    """Ask Rez a question via text, get voice response."""
    await ctx.defer()
    
    print(f"[{ctx.author.display_name}] {vraag}")
    
    response = await get_agent_response(vraag, str(ctx.author.id))
    print(f"[Rez] {response[:100]}...")
    
    vc = voice_connections.get(ctx.guild.id) if ctx.guild else None
    
    if vc and vc.is_connected():
        audio_data = await generate_tts(response)
        if audio_data:
            await play_audio(vc, audio_data)
    
    display_response = response[:1900] + "..." if len(response) > 1900 else response
    await ctx.respond(f"**🎤 {ctx.author.display_name}:** {vraag}\n\n**🤖 Rez:** {display_response}")


@bot.slash_command(name="say", description="Laat Rez iets zeggen in voice")
async def say(ctx: discord.ApplicationContext, tekst: str):
    """Make the bot say something."""
    if ctx.guild.id not in voice_connections:
        await ctx.respond("❌ Gebruik eerst `/join`!", ephemeral=True)
        return
    
    vc = voice_connections[ctx.guild.id]
    if not vc.is_connected():
        await ctx.respond("❌ Niet verbonden.", ephemeral=True)
        return
    
    await ctx.defer()
    
    audio_data = await generate_tts(tekst)
    if not audio_data:
        await ctx.respond("❌ TTS generatie mislukt")
        return
    
    await play_audio(vc, audio_data)
    await ctx.respond(f"🔊 *\"{tekst}\"*")


@bot.slash_command(name="status", description="Check bot status")
async def status(ctx: discord.ApplicationContext):
    """Show bot status."""
    in_voice = ctx.guild.id in voice_connections and voice_connections[ctx.guild.id].is_connected()
    is_listening = ctx.guild.id in listening_channels
    
    embed = discord.Embed(title="🤖 Rez Voice Status", color=0x00ff00 if in_voice else 0xff0000)
    embed.add_field(name="Voice", value="✅ Connected" if in_voice else "❌ Not connected", inline=True)
    embed.add_field(name="Listening", value="🎤 Active" if is_listening else "🔇 Inactive", inline=True)
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
    
    await ctx.respond(embed=embed)


@bot.event
async def on_voice_state_update(member, before, after):
    """Handle when users join/leave voice channels."""
    if member == bot.user:
        return
    
    guild_id = member.guild.id
    if guild_id in voice_connections:
        vc = voice_connections[guild_id]
        if vc.is_connected() and len(vc.channel.members) == 1:
            # Bot is alone, wait and leave
            await asyncio.sleep(60)
            if vc.is_connected() and len(vc.channel.members) == 1:
                listening_channels.discard(guild_id)
                await vc.disconnect()
                del voice_connections[guild_id]


def main():
    if not DISCORD_TOKEN:
        print("❌ DISCORD_BOT_TOKEN not set!")
        return
    
    if not ELEVENLABS_KEY:
        print("⚠️ ELEVENLABS_API_KEY not set - TTS disabled")
    
    print("🚀 Starting Discord Voice Bot (Bidirectional)...")
    print(f"   Whisper: {WHISPER_URL}")
    print(f"   Agent: {AGENT_URL}")
    print(f"   TTS: {'✅' if ELEVENLABS_KEY else '❌'}")
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
