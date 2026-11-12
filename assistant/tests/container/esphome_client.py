import asyncio
import sys
from pathlib import Path

from aioesphomeapi import APIClient, SwitchInfo

LEDS = Path(sys.argv[2])


def leds():
    return tuple((LEDS / name / "brightness").read_text().strip() for name in ("voxhub-green", "voxhub-blue"))


async def wait_for(expected, seconds=10.0):
    for _ in range(int(seconds * 10)):
        if leds() == expected:
            return True
        await asyncio.sleep(0.1)
    return False


async def main():
    results = []

    def check(name, ok):
        results.append(ok)
        print(("PASS  " if ok else "FAIL  ") + name, flush=True)

    client = APIClient(sys.argv[1], 6053, None)
    await client.connect(login=True)
    info = await client.device_info()
    described = f"device info: {info.friendly_name} / {info.model} {info.project_version}"
    check(described, info.friendly_name == "VoxHub Test")
    check("voice assistant features announced", bool(info.voice_assistant_feature_flags))
    entities, _ = await client.list_entities_services()
    names = sorted(entity.name for entity in entities)
    print("entities: " + ", ".join(names), flush=True)
    switches = [entity for entity in entities if isinstance(entity, SwitchInfo)]
    mute = next(entity for entity in switches if entity.object_id == "mute")
    states = {}
    client.subscribe_states(lambda state: states.__setitem__(state.key, state))
    check("LEDs idle (green) once Home Assistant is connected", await wait_for(("1", "0")))
    client.switch_command(mute.key, True)
    check("LEDs off while muted from Home Assistant", await wait_for(("0", "0")))
    await asyncio.sleep(1)
    check("mute switch state reported as on", getattr(states.get(mute.key), "state", None) is True)
    client.switch_command(mute.key, False)
    check("LEDs idle again after unmute", await wait_for(("1", "0")))
    await client.disconnect()
    seen = set()
    for _ in range(40):
        seen.add(leds())
        await asyncio.sleep(0.1)
    check("LEDs blink slowly (no connection) after Home Assistant left", seen == {("1", "0"), ("0", "0")})
    print(f"{sum(results)} of {len(results)} checks passed", flush=True)
    return 0 if all(results) else 1


sys.exit(asyncio.run(main()))
