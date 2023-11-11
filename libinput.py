#!/usr/bin/python
import struct
import subprocess


def touchpad_evdev(x, y, device):
    STRUCT_FORMAT = "llHHI"
    EVENT_SIZE = struct.calcsize(STRUCT_FORMAT)

    with open(device, "rb") as buffer:
        event = buffer.read(EVENT_SIZE)

        while event:
            ev_type, ev_code, value = struct.unpack(STRUCT_FORMAT, event)[2:]

            if ev_type == 3:
                if ev_code == 0:
                    x.value = value
                elif ev_code == 1:
                    y.value = value

            event = buffer.read(EVENT_SIZE)

    return x, y


def get_absinfo(device):
    pipe = subprocess.Popen(
        ["libinput", "record", device],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    absinfo = {}
    section = {}

    stream = pipe.stdout
    try:
        while not pipe.poll():
            line = next(stream).decode().rstrip()

            if line.startswith("devices:"):
                section["devices"] = True
                continue
            if section.get("devices"):
                if line.startswith("  evdev:"):
                    section["devices_evdev"] = True
                    continue
                elif line.startswith("  hid:"):
                    section["devices_evdev"] = False
                    continue

                if section.get("devices_evdev"):
                    if line.startswith("    absinfo:"):
                        section["devices_evdev_absinfo"] = True
                        continue
                    elif line.startswith("    properties:"):
                        section["devices_evdev_absinfo"] = False
                        break

                    if section.get("devices_evdev_absinfo"):
                        key, value = line.strip().split(": ")
                        absinfo.update({int(key): eval(value)})

    except KeyboardInterrupt:
        print("Exiting due to interrupt")

    pipe.kill()
    return absinfo


def libinput_devices():
    devices_stdout = subprocess.getoutput(
        "libinput list-devices", encoding="utf-8"
    ).splitlines()

    devices = []
    devices_index = 0
    for line in devices_stdout:
        if not line:
            continue

        key, *value = line.split(":")
        value = ":".join(value).strip()
        if line.startswith("Device:"):
            devices.append({key: value})
        else:
            devices[devices_index].update({key: value})

        if line.startswith("Rotation:"):
            devices_index += 1

    return devices


def get_touchpad_device():
    for i in filter(
        lambda x: "touchpad" in x["Device"].lower() and "pointer" in x["Capabilities"],
        libinput_devices(),
    ):
        return i["Kernel"]
