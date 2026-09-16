"""Generate scripts/fixtures/sample.log: a synthetic miniature of the verified corpus.

Every shape here is taken from docs/log-format.md. All identity values are invented.
Deterministic: same output on every run.
"""
import os
from datetime import datetime, timedelta

OUT = []
VER = "6.4.2408.2600"
SYNC_VER = "1.6.21"
MACHINE = "DEMO STORE 01"
GROUP = "DEMO GROUP"
IP_SELF, IP_B, IP_C = "10.0.0.11", "10.0.0.12", "10.0.0.13"
MAC = "AA:BB:CC:DD:EE:01"
SERIAL = "DEMOSERIAL0001"
SERVER = "demo.example.invalid"
MEDIA = "tpl-menuboard.1.2.3.4-store"
PLAYLIST_TS = "2026-01-08T14:46:31.027Z"
SCHED_TS = "2026-01-08T14.46.45.703"
EPOCH = datetime(1969, 12, 31, 21, 0, 0)   # epoch 0 rendered at UTC-3

_seed = 20260115
def rnd(lo, hi):
    """Deterministic pseudo-random in [lo, hi)."""
    global _seed
    _seed = (_seed * 1103515245 + 12345) & 0x7FFFFFFF
    return lo + (_seed % 100000) / 100000.0 * (hi - lo)

def emit(ts, level, msg):
    OUT.append(f"{ts.strftime('%Y-%m-%d %H:%M:%S')}.{ts.microsecond // 10000:02d} {level} {msg}")

def cs(ts, centis):
    return ts + timedelta(milliseconds=centis * 10)

def tick(ts, reboot_in, hb_ok=True):
    """The 60-second tick: seven lines, 52% of a real log's volume."""
    emit(cs(ts, 0), "INFO", f"[System Manager] CPU: {rnd(1, 54):.2f}%. Used RAM: {rnd(564.64, 866.50):.2f} Mb")
    emit(cs(ts, 3), "INFO", "[Hardware Policies] Processing policies")
    emit(cs(ts, 4), "INFO", "[Hardware Policies] Next Display State policy: NONE")
    emit(cs(ts, 7), "INFO", f"[System Manager] Device will reboot in {reboot_in} minutes")
    emit(cs(ts, 9), "INFO", "[Input Manager] Remote Control Enabled")
    emit(cs(ts, 11), "SUCCESS", "[Input Manager] Panel Unlocked")
    if hb_ok:
        emit(cs(ts, 14), "SUCCESS", "[Server Manager] Heartbeat received from server")
    else:
        emit(cs(ts, 14), "ERROR", "[Server Manager] Heartbeat Sync failed. Status: Error: Network Error")

def boot(start_real, reason, with_epoch=True):
    """A boot. On Tizen the banner is stamped at epoch 0 until NTP lands."""
    if reason:
        emit(start_real, "INFO", f"[Dex Player] System will reboot. Reason: {reason}")
        emit(cs(start_real, 6), "INFO", "[Input Source] clear() success.")
    e = EPOCH + timedelta(seconds=17, milliseconds=630)
    t = e if with_epoch else start_real + timedelta(seconds=18)
    emit(t, "INFO", "=" * 53)
    emit(cs(t, 1), "INFO", f"Dex Player {VER}")
    emit(cs(t, 1), "INFO", "=" * 53)
    emit(cs(t, 1), "INFO", '[Main] Initializing Dex Player. Platform "tizen"')
    emit(cs(t, 1), "INFO", "Device UserAgent: Mozilla/5.0 (SMART-TV; LINUX; Tizen 4.0) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 TV Safari/537.36")
    emit(cs(t, 58), "ERROR", "Dir failed playlists")
    emit(cs(t, 58), "ERROR", "Dir failed schedules")
    t2 = t + timedelta(seconds=9)
    emit(t2, "INFO", "[Main] Player files checked")
    emit(cs(t2, 222), "INFO", "[Node Server Manager] Starting node as service")
    emit(cs(t2, 222), "INFO", "[Node Server Manager] Node server file: server2018.js")
    t3 = t2 + timedelta(seconds=2, milliseconds=580)
    ds = t3.strftime("%a %b %d %Y %H:%M:%S")
    emit(t3, "INFO", f"[Tizen App] Device time: {ds} -03:00")
    emit(cs(t3, 1), "INFO", f"[Tizen App] Device time with timezone applied: {ds} -03:00")
    emit(cs(t3, 1), "INFO", "[Tizen App] Waiting for system date time")
    emit(cs(t3, 4), "SUCCESS", "[Node Server Manager] Node server started")
    emit(cs(t3, 72), "INFO", "[Main] Player playlists and schedules files format checked")
    t4 = t3 + timedelta(seconds=2)
    ds4 = t4.strftime("%a %b %d %Y %H:%M:%S")
    emit(t4, "INFO", f"[Tizen App] Device time: {ds4} -03:00")
    emit(cs(t4, 1), "INFO", "[Tizen App] Waiting for system date time")
    # NTP lands: the epoch window closes here.
    r = start_real + timedelta(seconds=38, milliseconds=860)
    dsr = r.strftime("%a %b %d %Y %H:%M:%S")
    emit(r, "INFO", f"[Tizen App] Device time: {dsr} -03:00")
    emit(cs(r, 1), "INFO", f"[Tizen App] Device time with timezone applied: {dsr} -03:00")
    emit(cs(r, 12), "INFO", "[System Manager] Server time offset: 1042 milliseconds. Time zone: -3  hs Screen Time zone:  -03:00")
    emit(cs(r, 30), "INFO", "[Screenshots Manager] Started with 15 minutes interval")
    return r + timedelta(seconds=4)

def handshake(t):
    emit(t, "INFO", f"[Server Manager] Fetching dex config on https://{SERVER}:443/dex_config.xml")
    emit(cs(t, 4), "WARNING", "[Server Manager] No tenant code found in dex_config.xml")
    emit(cs(t, 8), "INFO", "[Server Manager] Sending Handshake")
    emit(cs(t, 37), "INFO", f"[System Manager] CPU: {rnd(40, 54):.2f}%. Used RAM: {rnd(640, 680):.2f} Mb")
    emit(cs(t, 39), "INFO", f"[Server Manager] Hostname: {IP_SELF} {MAC}")
    emit(cs(t, 54), "INFO", "[System Manager] The player has connectivity with the server")
    t2 = t + timedelta(seconds=2, milliseconds=670)
    emit(t2, "SUCCESS", '[Server Manager] Handshake received. Code "LICOK"')
    emit(cs(t2, 1), "INFO", f"[Server Manager] Machine: {MACHINE}")
    emit(cs(t2, 1), "INFO", "[Server Manager] Machine HB Interval: 60 seconds")
    return t2 + timedelta(milliseconds=260)

def multicast(t):
    emit(t, "INFO", "[Node] [Sync] Joining multicast group")
    emit(cs(t, 229), "INFO", f"[Node] [Sync] New member discovered: {IP_B} | State: PLAYING | Channel: 3 | Is Master: false | MachineId: 3059")
    emit(cs(t, 229), "INFO", "[Node] [Sync] Channels empty")
    emit(cs(t, 230), "INFO", "[Node] [Sync] Master false | memberInfo false | masterDetermined false")
    emit(cs(t, 232), "INFO", f"[Player] Dex Sync v{SYNC_VER} is Running")
    t2 = t + timedelta(seconds=25)
    emit(t2, "INFO", "[Node] [Sync] This Machine is Master")
    return t2 + timedelta(seconds=1)

def status_block(t):
    """54 '=' delimiters. Note the double spaces and the trailing space: they are format."""
    emit(t, "INFO", "=" * 54)
    emit(cs(t, 1), "INFO", f"Player Version: {VER}")
    emit(cs(t, 2), "INFO", f"Serial Number: {SERIAL}")
    emit(cs(t, 2), "INFO", "Webview Version: ")
    emit(cs(t, 2), "INFO", f"Server: https://{SERVER}:443")
    emit(cs(t, 2), "INFO", "Firmware Version: T-INFOLINK2018-1052")
    emit(cs(t, 2), "INFO", "Machine time zone offset: -180")
    emit(cs(t, 3), "INFO", "Screenshots Interval: 900")
    emit(cs(t, 4), "INFO", f"CPU usage: {rnd(1, 20):.2f}%. Used RAM: {rnd(700, 800):.2f} Mb")
    emit(cs(t, 4), "INFO", f"Client IP: {IP_SELF}")
    emit(cs(t, 5), "INFO", "Machine ID: 3057")
    emit(cs(t, 6), "INFO", "Machine Tags: DEMO, SYNC01")
    emit(cs(t, 6), "INFO", "Tenant ID: 3. Tenant Name: DEMO TENANT")
    emit(cs(t, 7), "INFO", "Machine Sync ID:  1")
    emit(cs(t, 7), "INFO", "Multicast IP:  239.0.0.1")
    emit(cs(t, 7), "INFO", "Device will reboot at: 2021-04-30T04:00:00")
    emit(cs(t, 7), "INFO", "=" * 54)
    emit(cs(t, 9), "INFO", f"[Player] [Sync] Version: {SYNC_VER} - Group: {GROUP} - Members: {IP_SELF} [Master] {IP_B} {IP_C} ")
    t2 = t + timedelta(milliseconds=140)
    emit(t2, "INFO", "=" * 19 + "SYNC GROUP INFO" + "=" * 20)
    row = f"| PLAYING | Playlist: 6065 [{PLAYLIST_TS}] | Schedule: 238 [{SCHED_TS}] | Playlist To Change: [a.json,b.json,c.json]"
    emit(cs(t2, 0), "INFO", f"{IP_SELF} {row}  (MASTER)")
    emit(cs(t2, 0), "INFO", f"{IP_B} {row} ")
    emit(cs(t2, 0), "INFO", f"{IP_C} {row} ")
    emit(cs(t2, 1), "INFO", "=" * 54)
    return t2 + timedelta(seconds=1)

def playlist_change(t):
    emit(t, "INFO", "[MENUBOARD_TPL] [INFO] STOP_TPL received")
    emit(cs(t, 27), "SUCCESS", "[Player] Processing State Sync")
    emit(cs(t, 45), "SUCCESS", f'[Player] Playing Playlist "DEMO MORNING [{PLAYLIST_TS}]"')
    emit(cs(t, 54), "INFO", "[MENUBOARD_TPL] [INFO] Clean media managers on unload")
    emit(cs(t, 54), "INFO", "[Node] [Sync] PLAYLIST ID = 6065")
    emit(cs(t, 55), "INFO", "[Node] [Sync] New Playlist received")
    emit(cs(t, 67), "INFO", "[Player] Schedule time: LOCAL")
    nd = (t + timedelta(hours=6)).strftime("%a %b %d %Y %H:%M:%S")
    nw = t.strftime("%a %b %d %Y %H:%M:%S")
    emit(cs(t, 68), "INFO", f"[Player] End date: {nd} GMT-0300. Now: {nw} GMT-0300")
    emit(cs(t, 69), "INFO", "[Player] Next Playlist in 359 minutes")
    emit(cs(t, 69), "INFO", "[Player] Playing Schedule")
    emit(cs(t, 251), "INFO", "[Node] [Sync] Sending command PLAY burst to all members")
    emit(cs(t, 346), "INFO", f'[Player] [Sync] PLAY Command received. Media "{MEDIA}"')
    emit(cs(t, 348), "INFO", f"[Node] [Sync] [SyncShouldPlay] Don't play '{MEDIA}' from: 22:00:00 - to: 06:00:00")
    emit(cs(t, 350), "INFO", "[MENUBOARD_TPL] [INFO] [OffsetsManager] platform: QM")
    emit(cs(t, 351), "INFO", "[MENUBOARD_TPL] [INFO] [DataManager] SKUs found in configs:  42")
    emit(cs(t, 352), "INFO", "[MENUBOARD_TPL] [INFO] [StoreDataManager] TPL Mode: STORE ")
    return t + timedelta(seconds=5)

def debug_on(t):
    """DEBUG is enabled in production by a remote tag, with no reboot."""
    emit(t, "DEBUG", "[Player] hbMetadata: {\"machineId\":3057,\"playlistId\":6065,\"scheduleId\":238}")
    emit(cs(t, 6), "INFO", '[Server Manager] New Tags saved ["DEMO","Debug","SYNC01"]')
    emit(cs(t, 20), "DEBUG", "[System Manager] TimeOffset : 1042")
    emit(cs(t, 24), "DEBUG", "[Download Manager] Downloading false")
    emit(cs(t, 28), "DEBUG", "[Pending Downloads] Already checked pending downloads once, not checking again.")
    emit(cs(t, 33), "DEBUG", "[Player] [Sync] All group members have the same content")
    emit(cs(t, 41), "DEBUG", "[Player] [State] Schedule fields playlistId=6065 scheduleId=238 trigger=false")
    emit(cs(t, 52), "DEBUG", "[Player] [HB] Schedule fields playlistId=6065 scheduleId=238 trigger=false")
    # With Debug on, the player emits raw JSON and blows past the ~325-char ceiling
    # the other lines respect. The real corpus reached 5,681 characters.
    files = ",".join(
        '{"MachineFileId":%d,"Name":"demo-asset-%02d.png","Size":%d,"Hash":"%s","Status":"OK"}'
        % (7100 + i, i, 10240 + i * 137, ("%032x" % (0xABCDEF0123456789 + i * 7919))[:32])
        for i in range(9)
    )
    emit(cs(t, 61), "DEBUG", "[Machine Files Reporter] this.machineFilesArray Updated [" + files + "]")
    return t + timedelta(seconds=1)

def storage_incident(t):
    for i in range(4):
        u = cs(t, i * 3)
        emit(u, "WARNING", "[Tizen Storage] The storage is locked. Cannot write playlists/demo-morning.json.lock")
        emit(cs(u, 1), "ERROR", "[Player] Checking playlist failed  Cannot read property 'message' of undefined")
    t2 = t + timedelta(seconds=1)
    emit(t2, "ERROR", "[Player] While updating content. Error listing files for schedules/demo-morning.json. PLATFORM ERROR other")
    emit(cs(t2, 2), "ERROR", "[Player] CheckInternalIntegrity. Downloading MachineFiles Cannot read property 'message' of undefined Cannot read property 'message' of undefined")
    emit(cs(t2, 10), "WARNING", "[Player] Socket not initialized for report")
    return t2 + timedelta(seconds=4)


# ---- timeline -------------------------------------------------------------
day = datetime(2026, 1, 15)

# 1. Fifteen normal ticks before the scheduled reboot.
t = day.replace(hour=3, minute=45)
for i in range(15):
    tick(t, 15 - i)
    t += timedelta(seconds=60)

# 2. Scheduled reboot, with the epoch window.
t = boot(day.replace(hour=4, minute=0), "Scheduled reboot")
t = handshake(t)
t = multicast(t)

# 3. Twenty ticks; a fifteen-long heartbeat failure streak in the middle.
t = day.replace(hour=4, minute=2)
for i in range(20):
    tick(t, 1440 - i, hb_ok=not (3 <= i < 18))
    t += timedelta(seconds=60)

# 4. Status block, sync group, playlist change.
t = status_block(day.replace(hour=4, minute=23, second=51))
t = playlist_change(day.replace(hour=5, minute=0, second=12))

# 5. Six more ticks, then DEBUG is turned on remotely.
t = day.replace(hour=5, minute=2)
for i in range(6):
    tick(t, 1380 - i)
    t += timedelta(seconds=60)
t = debug_on(day.replace(hour=5, minute=8, second=44))

# 6. Storage incident and a soft-clean reboot.
t = storage_incident(day.replace(hour=5, minute=12, second=47))
t = boot(day.replace(hour=5, minute=13, second=51), "SOFT_CLEAN_COMMAND")
t = handshake(t)

# 7. Four ticks, then a gap of several hours, then four more.
t = day.replace(hour=5, minute=16)
for i in range(4):
    tick(t, 1320 - i)
    t += timedelta(seconds=60)
t = day.replace(hour=14, minute=30)
for i in range(4):
    tick(t, 810 - i)
    t += timedelta(seconds=60)

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample.log")
with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(OUT) + "\n")
print(f"{len(OUT)} lines -> {path}")
