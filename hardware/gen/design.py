#!/usr/bin/env python3
"""VoxHub CM4 carrier - the circuit, as code.  Run: python3 design.py <outdir>"""
import sys, os, json
from kisch import Design, PROJECT
from parts import PARTS, res as RES

d = Design("VoxHub CM4 - Home Assistant voice hub carrier", "A", "2026-11-10", "VoxHub (open hardware)")
L = d.lib
_cnt = {}

def ref(prefix):
    _cnt[prefix] = _cnt.get(prefix, 0) + 1
    return "%s%d" % (prefix, _cnt[prefix])

def F(key):
    m = PARTS[key]
    return {"Manufacturer": m[0], "MPN": m[1], "PartDescription": m[2]}

# ---- stock symbols copied into the project library ---------------------------
for s in ["Device:R", "Device:C", "Device:C_Polarized", "Device:L", "Device:LED", "Device:D_Zener", "Device:D_TVS",
          "Device:Crystal_GND24", "Transistor_FET:AO3401A", "Transistor_FET:2N7002", "Connector:TestPoint",
          "Connector_Generic:Conn_01x02", "Connector_Generic:Conn_01x03", "Jumper:SolderJumper_2_Open",
          "Mechanical:MountingHole", "Mechanical:MountingHole_Pad", "Mechanical:Fiducial",
          "Connector:USB_C_Receptacle_USB2.0_16P", "Connector:USB_A_Stacked",
          "Connector:Micro_SD_Card_Det_Hirose_DM3AT", "Connector:Conn_ARM_SWD_TagConnect_TC2030-NL",
          "Regulator_Switching:LMR33640ADDA",
          "Power_Protection:USBLC6-2SC6", "Switch:SW_DPDT_x2"]:
    L.use(s)
# unused hub ports 3/4 are strapped to 3V3 (port disable) -> passive; amp pad is ground
L.use("Interface_USB:USB2514B_Bi")
# VDC_OUT is a sense input for the switched rail (datasheet), not a driver
L.use("Interface_USB:CYPD3177-24LQ", pin_types={"11": "input"})
L.use("Audio:MAX98357A", pin_types={"17": "passive"})
# PDM mics share one data line (each drives one clock phase) -> model DATA as tri-state for ERC
L.use("Sensor_Audio:IM69D130", pin_types={"1": "tri_state"})
# USB-A VBUS pins are sourced by the board
L.use("Connector:USB_A_Stacked", alias="USB_A_Stacked_Host", pin_types={"1": "passive", "5": "passive", "4": "passive", "8": "passive"})

def P(n, name, t="passive"):
    return (n, name, t)

CM4_NAMES = """1:GND 2:GND 3:Ethernet_Pair3_P 4:Ethernet_Pair1_P 5:Ethernet_Pair3_N 6:Ethernet_Pair1_N 7:GND 8:GND
9:Ethernet_Pair2_N 10:Ethernet_Pair0_N 11:Ethernet_Pair2_P 12:Ethernet_Pair0_P 13:GND 14:GND 15:Ethernet_nLED3
16:Ethernet_SYNC_IN 17:Ethernet_nLED2 18:Ethernet_SYNC_OUT 19:Ethernet_nLED1 20:EEPROM_nWP 21:Pi_nLED_Activity
22:GND 23:GND 24:GPIO26 25:GPIO21 26:GPIO19 27:GPIO20 28:GPIO13 29:GPIO16 30:GPIO6 31:GPIO12 32:GND 33:GND 34:GPIO5
35:ID_SC 36:ID_SD 37:GPIO7 38:GPIO11 39:GPIO8 40:GPIO9 41:GPIO25 42:GND 43:GND 44:GPIO10 45:GPIO24 46:GPIO22
47:GPIO23 48:GPIO27 49:GPIO18 50:GPIO17 51:GPIO15 52:GND 53:GND 54:GPIO4 55:GPIO14 56:GPIO3 57:SD_CLK 58:GPIO2
59:GND 60:GND 61:SD_DAT3 62:SD_CMD 63:SD_DAT0 64:SD_DAT5 65:GND 66:GND 67:SD_DAT1 68:SD_DAT4 69:SD_DAT2 70:SD_DAT7
71:GND 72:SD_DAT6 73:SD_VDD_Override 74:GND 75:SD_PWR_ON 76:Reserved 77:+5V 78:GPIO_VREF 79:+5V 80:SCL0 81:+5V
82:SDA0 83:+5V 84:+3.3V_OUT 85:+5V 86:+3.3V_OUT 87:+5V 88:+1.8V_OUT 89:WL_nDisable 90:+1.8V_OUT 91:BT_nDisable
92:RUN_PG 93:nRPIBOOT 94:AnalogIP0 95:nPWR_LED 96:AnalogIP1 97:Camera_GPIO 98:GND 99:GLOBAL_EN 100:nEXTRST
101:USB_OTG_ID 102:PCIe_CLK_nREQ 103:USB2_N 104:Reserved 105:USB2_P 106:Reserved 107:GND 108:GND 109:PCIe_nRST
110:PCIe_CLK_P 111:VDAC_COMP 112:PCIe_CLK_N 113:GND 114:GND 115:CAM1_D0_N 116:PCIe_RX_P 117:CAM1_D0_P 118:PCIe_RX_N
119:GND 120:GND 121:CAM1_D1_N 122:PCIe_TX_P 123:CAM1_D1_P 124:PCIe_TX_N 125:GND 126:GND 127:CAM1_C_N 128:CAM0_D0_N
129:CAM1_C_P 130:CAM0_D0_P 131:GND 132:GND 133:CAM1_D2_N 134:CAM0_D1_N 135:CAM1_D2_P 136:CAM0_D1_P 137:GND 138:GND
139:CAM1_D3_N 140:CAM0_C_N 141:CAM1_D3_P 142:CAM0_C_P 143:HDMI1_HOTPLUG 144:GND 145:HDMI1_SDA 146:HDMI1_TX2_P
147:HDMI1_SCL 148:HDMI1_TX2_N 149:HDMI1_CEC 150:GND 151:HDMI0_CEC 152:HDMI1_TX1_P 153:HDMI0_HOTPLUG 154:HDMI1_TX1_N
155:GND 156:GND 157:DSI0_D0_N 158:HDMI1_TX0_P 159:DSI0_D0_P 160:HDMI1_TX0_N 161:GND 162:GND 163:DSI0_D1_N
164:HDMI1_CLK_P 165:DSI0_D1_P 166:HDMI1_CLK_N 167:GND 168:GND 169:DSI0_C_N 170:HDMI0_TX2_P 171:DSI0_C_P
172:HDMI0_TX2_N 173:GND 174:GND 175:DSI1_D0_N 176:HDMI0_TX1_P 177:DSI1_D0_P 178:HDMI0_TX1_N 179:GND 180:GND
181:DSI1_D1_N 182:HDMI0_TX0_P 183:DSI1_D1_P 184:HDMI0_TX0_N 185:GND 186:GND 187:DSI1_C_N 188:HDMI0_CLK_P
189:DSI1_C_P 190:HDMI0_CLK_N 191:GND 192:GND 193:DSI1_D2_N 194:DSI1_D3_N 195:DSI1_D2_P 196:DSI1_D3_P 197:GND
198:GND 199:HDMI0_SDA 200:HDMI0_SCL"""
CM4 = {int(t.split(":")[0]): t.split(":")[1] for t in CM4_NAMES.split()}

def cm4_type(n):
    nm = CM4[n]
    if nm == "+5V": return "power_in"
    if n == 84: return "power_out"
    return "passive"

for conn, lo in (("CM4_J1", 1), ("CM4_J2", 101)):
    left = [P(n, CM4[n], cm4_type(n)) for n in range(lo, lo + 100, 2)]
    right = [P(n, CM4[n], cm4_type(n)) for n in range(lo + 1, lo + 100, 2)]
    L.box(conn, left, right, ref="J", footprint="voxhub:%s_DF40C-100DS" % conn, width=55.88,
          value="CM4 socket pins %d-%d" % (lo, lo + 99),
          descr="Raspberry Pi CM4 mezzanine socket (Hirose DF40C-100DS-0.4V), pin numbers = CM4 datasheet numbering",
          datasheet="https://datasheets.raspberrypi.com/cm4/cm4-datasheet.pdf")

L.box("TPS2553", [P(1, "IN", "power_in"), P(3, "EN", "input"), P(2, "GND", "power_in")],
      [P(6, "OUT", "passive"), P(4, "~{FAULT}", "open_collector"), P(5, "ILIM", "passive")], ref="U",
      footprint=PARTS["U_SW"][3], datasheet="https://www.ti.com/lit/ds/symlink/tps2553.pdf",
      descr="Adjustable current-limited power switch, active-high enable", width=17.78)
L.box("ADAU7002", [P("A1", "PDM_DAT", "input"), P("A2", "PDM_CLK", "output"), P("D2", "CONFIG", "input"), P("C1", "GND", "power_in")],
      [P("D1", "IOVDD", "power_in"), P("B2", "BCLK", "input"), P("C2", "LRCLK", "input"), P("B1", "SDATA", "tri_state")],
      ref="U", footprint=PARTS["U_PDM"][3], datasheet="https://www.analog.com/media/en/technical-documentation/data-sheets/ADAU7002.pdf",
      descr="Stereo PDM to I2S/TDM converter", width=22.86)
MGM = "1:GND 2:PB04 3:PB03 4:PB02 5:PB01 6:PB00 7:PA00 8:PA01/SWCLK 9:PA02/SWDIO 10:PA03/SWO 11:PA04 12:PA05 13:PA06 14:GND 15:VDD 16:PA07 17:PA08 18:PD03 19:PD02 20:PD01 21:PD00 22:PC00 23:GND 24:PC01 25:PC02 26:PC03 27:PC04 28:PC05 29:PC06 30:PC07 31:~{RESET} 32:GND 33:RFOUT 34:GND 35:GND 36:GND"
MG = {int(t.split(":")[0]): t.split(":")[1] for t in MGM.split()}
def mg(n):
    return P(n, MG[n], "power_in" if MG[n] in ("GND", "VDD") else "passive")
L.box("MGM240P", [mg(n) for n in (15, 31, 8, 9, 10, 12, 13, 16, 17, 5, 6, 7, 11, 2, 3, 4, 1, 14)],
      [mg(n) for n in (33, 18, 19, 20, 21, 22, 24, 25, 26, 27, 28, 29, 30, 23, 32, 34, 35, 36)], ref="U",
      footprint=PARTS["U_ZB"][3], datasheet="https://www.silabs.com/documents/public/data-sheets/mgm240p-datasheet.pdf",
      descr="Silicon Labs MGM240P EFR32MG24 multiprotocol (Zigbee/Thread) module", width=38.1)

GND, V5, V33 = "GND", "+5V", "+3V3"

# ---- little helpers ------------------------------------------------------
def cap(sh, key, x, y, top, bot=GND, value=None, dnp=False, pol=False):
    m = PARTS[key]
    v = value or m[2].split()[2] if not pol else value or m[2].split()[3]
    r = ref("C")
    sh.place("C_Polarized" if pol else "C", r, v, x, y, {"1": top, "2": bot}, footprint=m[3], fields=F(key), dnp=dnp,
             textpos=((1.9, -1.0, "left"), (1.9, 1.5, "left")))
    return r

def res(sh, val, x, y, a, b, horiz=True, dnp=False):
    m = RES(val)
    r = ref("R")
    f = {"Manufacturer": m[0], "MPN": m[1], "PartDescription": m[2]}
    if horiz:
        sh.place("R", r, val, x, y, {"1": a, "2": b}, rot=90, footprint=m[3], fields=f, dnp=dnp,
                 textpos=((0, -2.3, None), (0, 2.6, None)))
    else:
        sh.place("R", r, val, x, y, {"1": a, "2": b}, footprint=m[3], fields=f, dnp=dnp,
                 textpos=((1.9, -1.0, "left"), (1.9, 1.5, "left")))
    return r

def led(sh, key, x, y, a, k, value, pos=None):
    r = ref("D")
    sh.place("LED", r, value, x, y, {"2": a, "1": k}, rot=90, footprint=PARTS[key][3], fields=F(key), pos=pos,
             textpos=((2.2, -1.0, "left"), (2.2, 1.5, "left")))
    return r

def tp(sh, x, y, net, name):
    sh.place("TestPoint", ref("TP"), name, x, y, {"1": net}, footprint="TestPoint:TestPoint_Pad_D1.5mm", in_bom=False,
             fields={"MPN": "", "Manufacturer": "", "PartDescription": "Test pad (no part)"})

# =========================================================================
# Sheet 2: POWER  (USB-C PD sink -> load switch -> 5.1 V buck)
# =========================================================================
s = d.sheet("power", "Power: USB-C PD sink, 5 V buck")
d.near = "U1"
s.box(15, 20, 225, 150, "USB-C input and PD sink controller (CYPD3177 'BCR', resistor-strapped: 9-20 V, 2 A minimum)")
s.place("USB_C_Receptacle_USB2.0_16P", "J1", "USB4105-GF-A", 40, 80,
        {"A4": "VBUS", "A9": "VBUS", "B4": "VBUS", "B9": "VBUS", "A5": "CC1", "B5": "CC2",
         "A6": "NC", "A7": "NC", "B6": "NC", "B7": "NC", "A8": "NC", "B8": "NC",
         "A1": GND, "A12": GND, "B1": GND, "B12": GND, "S1": GND}, footprint=PARTS["J_USBC"][3], fields=F("J_USBC"))
r = ref("D"); s.place("D_Zener", r, "SMBJ22A", 75, 60, {"1": "VBUS", "2": GND}, rot=270, footprint=PARTS["D_TVS"][3], fields=F("D_TVS"),
                      textpos=((2.2, -1.0, "left"), (2.2, 1.5, "left")))
for i, cc in enumerate(("CC1", "CC2")):
    r = ref("D"); s.place("D_TVS", r, "SD24C", 75 + i * 12, 100, {"1": GND, "2": cc}, rot=90, footprint=PARTS["D_CC"][3], fields=F("D_CC"),
                          textpos=((2.2, -1.0, "left"), (2.2, 1.5, "left")))
cap(s, "C_1u_35", 88, 60, "VBUS"); cap(s, "C_100n_50", 99, 60, "VBUS")
s.place("CYPD3177-24LQ", "U1", "CYPD3177-24LQXQT", 150, 80,
        {"1": "PD_VMIN", "2": "PD_VMAX", "3": "PD_FET_EN", "4": "NC", "5": "PD_ICOARSE", "6": "PD_IFINE", "7": "NC",
         "8": "NC", "9": "PD_FAULT", "10": "PD_FLIP", "11": "VBUS_SW", "12": "I2C_SDA", "13": "I2C_SCL", "14": "CC2", "15": "CC1",
         "18": "VBUS", "19": GND, "22": GND, "23": "PD_VDDD", "24": "PD_VCCD", "25": GND},
        footprint=PARTS["U_PD"][3], fields=F("U_PD"))
cap(s, "C_1u", 112, 125, "PD_VDDD"); cap(s, "C_100n", 123, 125, "PD_VDDD"); cap(s, "C_1u", 134, 125, "PD_VCCD")
# strap dividers (values: see DECISIONS.md / datasheet table)
STRAPS = [("PD_VMIN", "5.1k", "1k"), ("PD_VMAX", "0", None), ("PD_ICOARSE", "5.1k", "2.4k"), ("PD_IFINE", None, "0")]
for i, (net, top, bot) in enumerate(STRAPS):
    y = 40 + i * 20
    if top: res(s, top, 197, y, "PD_VDDD", net)
    if bot: res(s, bot, 197, y + 8, net, GND)
s.text("Straps: VBUS_MIN = 9 V, VBUS_MAX = 20 V,\nISNK_COARSE = 2 A, ISNK_FINE = +0 mA", 150, 147, size=1.5)
res(s, "1k", 150, 135, "PD_FAULT", "PD_FAULT_LED")
led(s, "LED_R", 175, 140, "PD_FAULT_LED", GND, "PD FAULT (red)")
res(s, "49.9k", 112, 142, "PD_VDDD", "PD_FLIP")
d.near = "Q1"
s.box(15, 155, 130, 275, "VBUS load switch: P-FET driven by the BCR's active-low, slew-controlled gate driver")
s.place("AO3401A", ref("Q"), "AO3401A", 60, 190, {"1": "PD_GATE", "2": "VBUS", "3": "VBUS_SW"}, rot=0, footprint=PARTS["Q_P"][3], fields=F("Q_P"))
res(s, "100k", 35, 215, "VBUS", "PD_GATE"); cap(s, "C_10n", 35, 240, "VBUS", "PD_GATE")
r = ref("D"); s.place("D_Zener", r, "10V", 60, 240, {"1": "VBUS", "2": "PD_GATE"}, rot=270, footprint=PARTS["D_Z10"][3], fields=F("D_Z10"),
                      textpos=((2.2, -1.0, "left"), (2.2, 1.5, "left")))
res(s, "150k", 95, 215, "PD_GATE", "PD_FET_EN")
s.text("VBUS_FET_EN pulls low after a 9-20 V contract.\nVgs = -0.4 x VBUS (-3.6 V @ 9 V, -8 V @ 20 V),\n10 V zener clamps transients.", 70, 262, size=1.4)
s.flag("VBUS", 30, 180); s.flag("VBUS_SW", 100, 180); s.flag(GND, 30, 265)
d.near = "U2"
s.box(135, 155, 405, 247, "5.1 V / 4 A synchronous buck (LMR33640, 400 kHz) - UVLO 7.0 V keeps it off at vSafe5V")
s.place("LMR33640ADDA", "U2", "LMR33640ADDAR", 215, 205,
        {"1": GND, "2": "VBUS_SW", "3": "BUCK_EN", "4": "NC", "5": "BUCK_FB", "6": "BUCK_VCC", "7": "BUCK_BOOT", "8": "BUCK_SW", "9": GND},
        footprint=PARTS["U_BUCK"][3], fields=F("U_BUCK"))
for i in range(2): cap(s, "C_10u_35", 150 + i * 11, 185, "VBUS_SW")
cap(s, "C_100n_50", 172, 185, "VBUS_SW")
res(s, "470k", 160, 215, "VBUS_SW", "BUCK_EN"); res(s, "100k", 160, 225, "BUCK_EN", GND)
cap(s, "C_1u", 195, 238, "BUCK_VCC")
cap(s, "C_100n", 250, 185, "BUCK_BOOT", "BUCK_SW")
r = ref("L"); s.place("L", r, "6.8uH", 275, 205, {"1": "BUCK_SW", "2": V5}, rot=90, footprint=PARTS["L_6u8"][3], fields=F("L_6u8"),
                      textpos=((0, -2.6, None), (0, 2.8, None)))
res(s, "100k", 270, 225, V5, "BUCK_FB"); res(s, "24.3k", 270, 235, "BUCK_FB", GND)
cap(s, "C_22p", 300, 232, V5, "BUCK_FB", dnp=True)
for i in range(4): cap(s, "C_22u", 315 + i * 11, 200, V5)
cap(s, "C_100n", 359, 200, V5)
res(s, "2.2k", 340, 235, V5, "PWR_LED_A"); led(s, "LED_G", 365, 240, "PWR_LED_A", GND, "PWR (green)")
s.flag(V5, 380, 205)
d.near = "TPZONE"
for i, (n, nm) in enumerate((("VBUS", "VBUS"), ("VBUS_SW", "VBUS_SW"), (V5, "+5V"), (V33, "+3V3"), (GND, "GND"))):
    tp(s, 300 + i * 20, 172, n, nm)

# =========================================================================
# Sheet 3: CM4 socket, microSD, UI (LEDs, mute switch), debug
# =========================================================================
s = d.sheet("cm4", "Compute Module 4 socket, microSD, user interface")
d.near = "J2"
n1 = {n: "NC" for n in range(1, 101)}
for n in range(1, 101):
    if CM4[n] == "GND": n1[n] = GND
    if CM4[n] == "+5V": n1[n] = V5
n1.update({21: "ACT_LED_K", 25: "I2S_DOUT", 26: "I2S_LRCLK", 27: "I2S_DIN", 29: "AMP_SD", 30: "LED_B_EN", 34: "LED_G_EN",
           38: "UART4_RTS", 39: "UART4_TX", 40: "UART4_RX", 41: "ZB_BOOT", 44: "UART4_CTS", 45: "ZB_NRST",
           46: "ZB_SWDIO", 47: "ZB_SWCLK", 48: "MUTE_SENSE", 49: "I2S_BCLK", 51: "DBG_RX", 55: "DBG_TX",
           56: "I2C_SCL", 58: "I2C_SDA", 57: "SD_CLK", 61: "SD_DAT3", 62: "SD_CMD", 63: "SD_DAT0", 67: "SD_DAT1",
           69: "SD_DAT2", 75: "SD_PWR_ON", 78: V33, 84: V33, 86: V33, 93: "NRPIBOOT"})
s.place("CM4_J1", "J2", "DF40C-100DS-0.4V(51)", 70, 150, {str(k): v for k, v in n1.items()}, fields=F("J_CM4"))
n2 = {n: "NC" for n in range(101, 201)}
for n in range(101, 201):
    if CM4[n] == "GND": n2[n] = GND
n2.update({101: GND, 103: "USB_UP_N", 105: "USB_UP_P"})
s.place("CM4_J2", "J3", "DF40C-100DS-0.4V(51)", 185, 150, {str(k): v for k, v in n2.items()}, fields=F("J_CM4"))
s.text("Module: Raspberry Pi CM4 Lite, wireless (CM4104000 / CM4102000 / CM4108000)\nGPIO map: see README. USB_OTG_ID tied low = host.", 30, 275, size=1.6)
d.near = "U3"
s.box(250, 20, 405, 110, "microSD (boot / storage) - card power switched by SD_PWR_ON")
s.place("Micro_SD_Card_Det_Hirose_DM3AT", "J4", "DM3AT-SF-PEJM5", 370, 65,
        {"1": "SD_DAT2", "2": "SD_DAT3", "3": "SD_CMD", "4": "SD_VDD", "5": "SD_CLK", "6": GND, "7": "SD_DAT0", "8": "SD_DAT1",
         "9": "NC", "10": "NC", "11": GND}, footprint=PARTS["J_SD"][3], fields=F("J_SD"))
s.place("TPS2553", "U3", "TPS2553DBVR", 290, 50, {"1": V33, "3": "SD_PWR_ON", "2": GND, "6": "SD_VDD", "4": "NC", "5": "SD_ILIM"}, fields=F("U_SW"))
res(s, "49.9k", 290, 72, "SD_ILIM", GND); res(s, "10k", 290, 82, V33, "SD_PWR_ON")
cap(s, "C_100n", 262, 95, V33); d.near = "J4"; cap(s, "C_4u7", 320, 95, "SD_VDD"); cap(s, "C_100n", 331, 95, "SD_VDD")
s.flag("SD_VDD", 342, 98)
d.near = "UI"
s.box(250, 115, 405, 215, "User interface: status LEDs (reverse-mount, shine through PCB to the top cover) and hardware mic mute")
for i, (key, en, name) in enumerate((("LED_UG", "LED_G_EN", "GREEN"), ("LED_UB", "LED_B_EN", "BLUE"))):
    x = 265 + i * 55
    res(s, "680" if i == 0 else "470", x, 135, V5, "LED%d_A" % i)
    led(s, key, x + 20, 150, "LED%d_A" % i, "LED%d_K" % i, name, pos=(34.0 + i * 4.6, 71.2, 90, "F"))
    q = ref("Q"); s.place("2N7002", q, "2N7002", x + 5, 180, {"1": en, "2": GND, "3": "LED%d_K" % i}, footprint=PARTS["Q_N"][3], fields=F("Q_N"))
    res(s, "10k", x, 200, en, GND)   # beats the SoC's ~50k boot-time pull-up on GPIO5/6
s.place("SW_DPDT_x2", "SW1", "JS202011JCQN (MUTE)", 375, 140, {"1": "NC", "2": V33, "3": "MIC_MUTE"}, unit=1, footprint=PARTS["SW_MUTE"][3], fields=F("SW_MUTE"))
s.place("SW_DPDT_x2", "SW1", "JS202011JCQN (MUTE)", 375, 165, {"4": "MIC_SDATA", "5": "I2S_DIN", "6": GND}, unit=2, footprint=PARTS["SW_MUTE"][3], fields=F("SW_MUTE"))
res(s, "330", 370, 185, "MIC_MUTE", "MUTE_LED_A"); led(s, "LED_UR", 395, 200, "MUTE_LED_A", GND, "RED (muted)", pos=(43.2, 71.2, 90, "F"))
res(s, "10k", 370, 195, "MIC_MUTE", "MUTE_SENSE"); res(s, "100k", 370, 205, "MUTE_SENSE", GND)
res(s, "100k", 330, 205, "I2S_DIN", GND)
s.text("SW1 pole A lights the red LED, pole B physically disconnects mic data\nfrom the CM4 (I2S_DIN grounded) - mute cannot be overridden by software.", 252, 213, size=1.4)
d.near = "CM4CAP"
s.box(250, 220, 405, 247, "Module support: activity LED, 5 V decoupling, rpiboot jumper, debug UART (DNP)")
res(s, "1k", 265, 230, V33, "ACT_LED_A"); led(s, "LED_G", 290, 236, "ACT_LED_A", "ACT_LED_K", "ACT (green)")
cap(s, "C_22u", 320, 235, V5); cap(s, "C_22u", 331, 235, V5); cap(s, "C_100n", 342, 235, V5); cap(s, "C_100n", 353, 235, V33)
s.place("SolderJumper_2_Open", "JP1", "RPIBOOT", 130, 255, {"1": "NRPIBOOT", "2": GND},
        footprint="Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm", in_bom=False,
        fields={"MPN": "", "Manufacturer": "", "PartDescription": "Solder jumper (no part)"})
s.place("Conn_01x03", "J5", "DEBUG UART", 60, 250, {"1": GND, "2": "DBG_TX", "3": "DBG_RX"}, footprint=PARTS["J_DBG"][3], fields=F("J_DBG"), dnp=True)

# =========================================================================
# Sheet 4: USB hub and host ports
# =========================================================================
s = d.sheet("usb", "USB 2.0 hub and USB-A host ports")
d.near = "U4"
s.box(15, 20, 215, 275, "USB2514B hub: upstream = CM4 USB2, ports 1-2 = USB-A, ports 3-4 disabled by strap")
s.place("USB2514B_Bi", "U4", "USB2514B-I/M2", 110, 130,
        {"1": "USB1_N", "2": "USB1_P", "3": "USB2_N", "4": "USB2_P", "5": V33, "6": "HUB_DIS3M", "7": "HUB_DIS3P", "8": "HUB_DIS4M", "9": "HUB_DIS4P", "10": V33,
         "11": GND, "12": "USB_PWR1", "13": "USB_OC1_N", "14": "HUB_CRFILT", "15": V33, "16": "USB_PWR2", "17": "USB_OC2_N",
         "18": "NC", "19": "NC", "20": "NC", "21": "NC", "22": "HUB_NONREM1", "23": V33, "24": "HUB_CFG0", "25": "HUB_CFG1",
         "26": "HUB_RST_N", "27": "HUB_VBUSDET", "28": "HUB_NONREM0", "29": V33, "30": "USB_UP_N", "31": "USB_UP_P",
         "32": "HUB_XO", "33": "HUB_XI", "34": "HUB_PLLFILT", "35": "HUB_RBIAS", "36": V33, "37": GND},
        footprint=PARTS["U_HUB"][3], fields=F("U_HUB"))
s.place("Crystal_GND24", "Y1", "24MHz", 45, 215, {"1": "HUB_XI", "3": "HUB_XO", "2": GND, "4": GND}, footprint=PARTS["Y_24M"][3], fields=F("Y_24M"))
cap(s, "C_27p", 30, 240, "HUB_XI"); cap(s, "C_27p", 60, 240, "HUB_XO")
res(s, "12k", 40, 60, "HUB_RBIAS", GND); cap(s, "C_100n", 30, 85, "HUB_PLLFILT"); cap(s, "C_100n", 45, 85, "HUB_CRFILT")
res(s, "10k", 40, 110, V33, "HUB_RST_N"); cap(s, "C_100n", 60, 110, "HUB_RST_N")
res(s, "100k", 40, 130, V33, "HUB_VBUSDET")
for i, nn in enumerate(("HUB_CFG0", "HUB_CFG1", "HUB_NONREM0", "HUB_NONREM1")):
    res(s, "100k", 40, 150 + i * 10, nn, GND)
for i, nn in enumerate(("HUB_DIS3M", "HUB_DIS3P", "HUB_DIS4M", "HUB_DIS4P")):
    res(s, "10k", 185, 60 + i * 10, V33, nn)
for i in range(6): cap(s, "C_100n", 85 + i * 11, 245, V33)
cap(s, "C_4u7", 151, 245, V33)
s.box(220, 20, 405, 247, "Downstream ports: per-port 1.2 A current-limited switch, ESD protection, stacked USB-A")
for i in (1, 2):
    y = 60 + (i - 1) * 110
    d.near = "U%d" % (4 + i)
    s.place("TPS2553", "U%d" % (4 + i), "TPS2553DBVR", 255, y, {"1": V5, "3": "USB_PWR%d" % i, "2": GND, "6": "USB%d_VBUS" % i,
            "4": "USB_OC%d_N" % i, "5": "USB%d_ILIM" % i}, fields=F("U_SW"))
    res(s, "20k", 255, y + 22, "USB%d_ILIM" % i, GND); res(s, "10k", 255, y + 32, V33, "USB_OC%d_N" % i)
    cap(s, "C_4u7", 232, y + 50, V5); cap(s, "C_100u_poly", 300, y + 50, "USB%d_VBUS" % i, pol=True, value="100uF"); cap(s, "C_100n", 314, y + 50, "USB%d_VBUS" % i)
    s.place("USBLC6-2SC6", "U%d" % (6 + i), "USBLC6-2SC6", 320, y,
            {"1": "USB%d_N" % i, "6": "USB%d_N" % i, "3": "USB%d_P" % i, "4": "USB%d_P" % i, "5": "USB%d_VBUS" % i, "2": GND}, fields=F("U_ESD"))
    s.flag("USB%d_VBUS" % i, 330, y + 53)
_cnt["U"] = 8
s.place("USB_A_Stacked_Host", "J6", "61400826021", 380, 120,
        {"1": "USB1_VBUS", "2": "USB1_N", "3": "USB1_P", "4": GND, "5": "USB2_VBUS", "6": "USB2_N", "7": "USB2_P", "8": GND, "9": GND},
        footprint=PARTS["J_USBA"][3], fields=F("J_USBA"))

# =========================================================================
# Sheet 5: Audio
# =========================================================================
s = d.sheet("audio", "Audio: PDM microphones, PDM-to-I2S, class-D speaker amplifier")
s.box(15, 20, 215, 150, "Stereo MEMS microphone array (bottom port through PCB) and PDM -> I2S converter")
for i, sel in enumerate((GND, V33)):
    x = 45 + i * 60
    d.near = "MK%d" % (i + 1)
    s.place("IM69D130", "MK%d" % (i + 1), "IM69D130", x, 60, {"1": "PDM_DAT", "2": V33, "3": "PDM_CLK_M", "4": sel, "5": GND},
            fields=F("MK_PDM"))
    cap(s, "C_100n", x - 20, 95, V33)
s.text("MK1 SELECT=GND (left), MK2 SELECT=VDD (right); 70 mm apart", 30, 115, size=1.5)
d.near = "U9"
s.place("ADAU7002", "U9", "ADAU7002ACBZ-R7", 165, 60, {"A1": "PDM_DAT", "A2": "PDM_CLK", "D2": V33, "C1": GND, "D1": V33,
        "B2": "I2S_BCLK", "C2": "I2S_LRCLK", "B1": "MIC_SDATA"}, fields=F("U_PDM"))
res(s, "33", 150, 95, "PDM_CLK", "PDM_CLK_M"); cap(s, "C_100n", 190, 100, V33); res(s, "100k", 150, 105, "MIC_SDATA", GND)
res(s, "100k", 150, 115, "PDM_DAT", GND)
s.text("CONFIG = IOVDD -> I2S output; BCLK = 64 fs, PDM clock = 64 fs (3.072 MHz @ 48 kHz)", 110, 135, size=1.5)
d.near = "U10"
s.box(15, 155, 215, 275, "Speaker amplifier (MAX98357A, I2S in, 3.2 W into 4 ohm from 5 V)")
s.place("MAX98357A", "U10", "MAX98357AETE+T", 100, 205,
        {"1": "I2S_DOUT", "2": "NC", "3": GND, "4": "AMP_SD", "7": V5, "8": V5, "9": "SPK_P", "10": "SPK_N", "11": GND,
         "14": "I2S_LRCLK", "15": GND, "16": "I2S_BCLK", "17": GND}, fields=F("U_AMP"))
cap(s, "C_22u", 30, 245, V5); cap(s, "C_22u", 41, 245, V5); cap(s, "C_100n", 52, 245, V5); res(s, "100k", 75, 255, "AMP_SD", GND)
s.place("Conn_01x02", "J7", "SPEAKER 4R", 185, 205, {"1": "SPK_P", "2": "SPK_N"}, footprint=PARTS["J_SPK"][3], fields=F("J_SPK"))
s.text("SD_MODE driven by GPIO16 (3.3 V = left channel, low = shutdown). GAIN_SLOT open = 9 dB.", 30, 270, size=1.5)

# =========================================================================
# Sheet 6: Zigbee / Thread radio
# =========================================================================
s = d.sheet("zigbee", "Zigbee / Thread radio (MGM240P, EFR32MG24)")
d.near = "U11"
z = {n: "NC" for n in range(1, 37)}
for n in (1, 14, 23, 32, 34, 35, 36): z[n] = GND
z.update({15: V33, 31: "ZB_NRST", 8: "ZB_SWCLK", 9: "ZB_SWDIO", 10: "ZB_SWO", 12: "UART4_RX", 13: "UART4_TX",
          16: "UART4_RTS", 17: "UART4_CTS", 22: "ZB_BOOT"})
s.box(15, 20, 290, 150, "MGM240P network co-processor on CM4 UART4 (GPIO8-11, hardware flow control) + SWD")
s.place("MGM240P", "U11", "MGM240PB32VNA3", 110, 85, {str(k): v for k, v in z.items()}, fields=F("U_ZB"))
cap(s, "C_4u7", 30, 130, V33); cap(s, "C_100n", 41, 130, V33); cap(s, "C_100n", 60, 130, "ZB_NRST")
res(s, "10k", 90, 135, V33, "ZB_NRST"); res(s, "10k", 90, 143, V33, "ZB_BOOT")   # GPIO24/25 default to pull-down at boot
s.place("Conn_ARM_SWD_TagConnect_TC2030-NL", "J8", "TC2030-NL (SWD)", 230, 80,
        {"1": V33, "2": "ZB_SWDIO", "3": "ZB_NRST", "4": "ZB_SWCLK", "5": GND, "6": "ZB_SWO"}, in_bom=False,
        fields={"MPN": "", "Manufacturer": "", "PartDescription": "Tag-Connect footprint (no part)"})
s.text("UART: PA05 = module TX -> GPIO9 (RXD4), PA06 = module RX <- GPIO8 (TXD4),\nPA07 = module CTS <- GPIO11 (RTS4), PA08 = module RTS -> GPIO10 (CTS4).\n"
       "PC00 = bootloader entry, active low (GPIO25), RESET = GPIO24. SWD also wired to GPIO22/23\nso the CM4 can flash the radio in-system (openocd bit-bang).", 150, 140, size=1.5)

# =========================================================================
# Root sheet: mechanical items
# =========================================================================
s = d.root
d.near = None
s.text("VoxHub CM4 - Home Assistant voice hub\nUSB-C PD (9-20 V) -> 5.1 V buck -> CM4 Lite + USB hub + audio + Zigbee", 30, 40, size=3.0, bold=True)
for i in range(4):
    s.place("MountingHole", "H%d" % (i + 1), "M2.5 board mount", 40 + i * 30, 170, {}, footprint="MountingHole:MountingHole_2.7mm_M2.5",
            in_bom=False, fields={"MPN": "", "Manufacturer": "", "PartDescription": "PCB mounting hole"})
for i in range(4):
    s.place("MountingHole_Pad", "H%d" % (i + 5), "CM4 spacer M2.5x1.5", 40 + i * 30, 200, {"1": GND}, footprint=PARTS["H_CM4"][3], fields=F("H_CM4"))
for i in range(3):
    s.place("Fiducial", "FID%d" % (i + 1), "Fiducial", 180 + i * 20, 170, {}, footprint="Fiducial:Fiducial_1mm_Mask2mm", in_bom=False,
            fields={"MPN": "", "Manufacturer": "", "PartDescription": "Fiducial"})

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else ".."
    d.write(out)
    json.dump(d.components, open(os.path.join(out, "gen", "model_netlist.json"), "w"), indent=1, sort_keys=True)
    print("components:", len(d.components), "nets:", len(d.nets_used))
