"""Sourcing data per MPN.

Primary source of revision A2 is the JLCPCB assembly library: sourcing_jlc.json holds the LCSC part number, the
library type (Basic / Preferred Extended / Extended), JLCPCB and LCSC stock and the JLCPCB price of every line, read
live with jlc_lookup.py.  The DigiKey data of the 2026-11-11 check (sourcing_live.json) stays as the second source:
DIGIKEY names, for every line whose JLCPCB part is not carried by DigiKey, the equivalent part that is.

SECOND: MPN -> (second source, note)
"""
import json, os

_HERE = os.path.dirname(os.path.abspath(__file__))
LIVE = json.load(open(os.path.join(_HERE, "sourcing_live.json")))
PARTS_LIVE = LIVE["parts"]
JLC = json.load(open(os.path.join(_HERE, "sourcing_jlc.json")))
PARTS_JLC = JLC["parts"]

DIGIKEY = {
 "CL10B105KA8NNNC": "C1608X7R1C105K080AC", "CL10A475KA8NQNC": "C1608X5R1E475K080AC", "CL10A105KB8NNNC": "C1608X5R1H105K080AB",
 "CC0603KRX7R9BB104": "C0603C104K5RACTU", "CL31A226KAHNNNE": "CL31A226KOHNNNE", "LTST-C191KRKT": "150060RS75000",
 "X322524MOB4SI": "TSX-3225 24.0000MF18X-C0",
 "0402CG220J500NT": "CL05C220JB5NNNC", "T520B107M006ATE040": "T520B107M006ATE070", "SLO0630H6R8MTT": "SRP7028A-6R8M",
 "MM3Z10VT1G": "SZMM3Z10VT1G",
 "0402WGF0000TCE": "RC0402FR-070RL", "0402WGF330JTCE": "RC0402FR-0733RL", "0402WGF3300TCE": "RC0402FR-07330RL",
 "0402WGF1001TCE": "RC0402FR-071KL",
 "0402WGF2201TCE": "RC0402FR-072K2L", "0402WGF2401TCE": "RC0402FR-072K4L", "0402WGF5101TCE": "RC0402FR-075K1L",
 "0402WGF1002TCE": "WR04X1002FTL", "0402WGF1202TCE": "RC0402FR-0712KL", "0402WGF2002TCE": "RC0402FR-0720KL",
 "0402WGF2492TCE": "RMCF0402FT24K9", "0402WGF4992TCE": "RMCF0402FT49K9", "0402WGF1003TCE": "RMCF0402FT100K",
 "0402WGF1503TCE": "RC0402FR-07150KL", "0402WGF4703TCE": "RC0402FR-07470KL",
}

SECOND = {
 "CM4104000": ("CM4102000 (2 GB) / CM4108000 (8 GB): drop-in", "Production until >= Jan 2034"),
 "DF40C-100DS-0.4V(51)": ("Hirose DF40HC(3.0)-100DS-0.4V(51): same land pattern, 3.0 mm stack (needs 3 mm spacers)", ""),
 "CYPD3177-24LQXQT": ("second JLCPCB listing of the same part: C5904158; none pin-compatible from another maker (TI TPS25730, ST STUSB4500 need a re-layout)", ""),
 "LMR33640ADDAR": ("same family and footprint: LMR33640DDDAR (1 MHz, JLCPCB C1852154) with L1 = 3.3 uH per the data sheet table - re-validate before use",
                   "A1 flagged this line: 0 at DigiKey (26 weeks). JLCPCB has it in stock"),
 "SLO0630H6R8MTT": ("Vishay IHLP2525CZER6R8M01 (JLCPCB C506575; 125 C part temperature instead of 150 C), Bourns SRP7028A-6R8M (the A1 part, 0 at JLCPCB): same pads",
                    "replaces the Bourns part: L, Irms 4.5 A, Isat 8 A (-20 %), -55..+150 C identical, DCR 45 / 54 mOhm instead of 54 / 60"),
 "USB2514B-I/M2": ("USB2514BT-I/M2 (tape and reel, JLCPCB C510949): same part. USB2514B/M2 is 0-70 C only (downgrade)", ""),
 "TPS2553DBVR": ("TPS2553DBVT: the identical device on the small reel", "A1 flagged this line: 0 at DigiKey. JLCPCB has it in stock"),
 "USB4105-GF-A": ("none verified (GCT USB4105-GF-A-120: same footprint, longer shell stakes)", ""),
 "DM3AT-SF-PEJM5": ("none drop-in (Molex 104031-0811 needs a new footprint)", ""),
 "MAX98357AETE+T": ("no second source", ""),
 "ADAU7002ACBZ-R7": ("ADAU7002ACBZ-RL (13 inch reel, JLCPCB C654434: 0): same part. No other PDM-to-I2S converter exists at JLCPCB",
                     "STOCK RISK: 104 at JLCPCB (need: 2) - buy it into the JLCPCB parts library first (Parts Manager) or let JLCPCB source it (Global Sourcing)"),
 "IM69D130V01XTSA1": ("Infineon IM73D122V01XTMA1 (JLCPCB C5563886, same footprint and pin-out, 73 dB SNR, IP57; absolute maximum 3.6 V instead of 4.0 V) or IM72D128V01XTMA1 (C5119248)",
                      "JLCPCB lists the part as IM69D130V01 (C536262)"),
 "RF-BM-2652P2": ("no drop-in in stock: RF-star RF-BM-2652P4 (CC2652P7, same outline, other firmware build); Ebyte E72-2G4M20S1E needs another footprint",
                  "replaces the Silicon Labs MGM240PB32VNA3 (0 at JLCPCB and LCSC). Not carried by DigiKey"),
 "USBLC6-2SC6": ("none needed; note that Nexperia PRTR5V0U2X has a different pin-out", "LCSC C7519 is the STMicroelectronics listing"),
 "AO3401A": ("Diodes DMP3056L-7: SOT-23 G/S/D, drop-in", "LCSC C15127 is the Alpha & Omega listing"),
 "2N7002,215": ("Nexperia 2N7002BK,215 works here (gates see 3.3 V) but is rated VGS +-20 V instead of +-30 V; the JLCPCB Basic 2N7002 (C8545) is a 115 mA / +-20 V part - not used",
                "A1 flagged this line: 0 at DigiKey. JLCPCB has it in stock"),
 "SMBJ22A": ("SMBJ22A from Bourns / Diodes / ST / Taiwan Semi: drop-in", "LCSC C224015 is the Littelfuse listing"),
 "SD24C-01FTG": ("no equal-or-better SOD-323 part found", "LCSC C207246 is the Littelfuse listing"),
 "MM3Z10VT1G": ("onsemi SZMM3Z10VT1G (same die with AEC-Q101, JLCPCB C894520 - no footprint record in the JLCPCB library) or any 10 V SOD-323 zener >= 300 mW", ""),
 "B2B-PH-K-S(LF)(SN)": ("none needed", ""), "61300311121": ("any 1x3 2.54 mm header", "DNP"),
 "61400826021": ("Jing Extension 907-112A1022D10200 (JLCPCB C29780026, 2,959 in stock): same hole pattern within 0.12 mm, shell 0.26 mm taller, passes the enclosure window; no temperature range on its drawing. Korean Hroparts U-A-28DD-Y-1 (C530601): identical pattern, +85 C",
                 "STOCK: 116 at JLCPCB (need: 2). Hand-soldered THT part"),
 "9774015151R": ("Sinhoo SMTSO2515CTJ (JLCPCB C2915629) needs a 4.25 mm hole and a 6.3 mm pad - not a drop-in", "230 at JLCPCB, not sold at LCSC"),
 "X322524MOB4SI": ("YXC X322524MRB4SI (CL 18 pF, JLCPCB C70571) or the A1 part Epson TSX-3225 24.0000MF18X-C0 (CL 18 pF): both need 27 pF load capacitors instead of 15 pF",
                   "CL 12 pF -> C26 / C27 = 15 pF; +-10 ppm, +-20 ppm over -40..+85 C"),
 "0402CG150J500NT": ("any 0402 15 pF C0G 50 V", "crystal load capacitors for CL 12 pF"),
 "LTST-C191KRKT": ("Wurth 150060RS75000 (the A1 part); Hubei KENTO KT-0603R is JLCPCB Basic but rated 25 mA / 40 mW", "30 mA / 75 mW / -55..+85 C: every rating of the A1 part met"),
 "150060VS75000": ("any 0603 AlInGaP green LED, VF about 2.0 V", ""),
 "KT-0603G": ("any 0603 InGaN green LED >= 25 mA, -40..+85 C (VF about 2.7 V at 2 mA)", "replaces the reverse-mount Wurth 156120GS75000 (0 at JLCPCB): ordinary LED on side B inside the light pipe"),
 "KT-0603B": ("any 0603 InGaN blue LED >= 25 mA, -40..+85 C", "replaces the reverse-mount Wurth 156120BS75000 (not at JLCPCB): ordinary LED on side B inside the light pipe"),
 "JS202011JCQN": ("C&K JS202011SCQN (gull-wing leads; footprint check needed)", ""),
 "T520B107M006ATE040": ("KEMET T520B107M006ATE070 (the A1 part, 70 mOhm), Vishay T55B107M6R3C0040 (JLCPCB C2158743): same footprint", "replaces the 70 mOhm version: 40 mOhm, 1.8 A ripple, same case and ratings"),
 "CL05B104KO5NNNC": ("any 0402 100 nF X7R >= 16 V", ""),
 "CL05B103KB5NNNC": ("any 0402 10 nF X7R 50 V", ""), "0402CG220J500NT": ("any 0402 22 pF C0G 50 V", "DNP"),
 "CL10B105KA8NNNC": ("TDK C1608X7R1C105K080AC (16 V, the A1 part), Samsung CL10B105KO8NNNC (16 V, JLCPCB C59782): 1 uF X7R 0603", "25 V instead of 16 V; X7R kept on purpose (DC bias)"),
 "CL10A475KA8NQNC": ("TDK C1608X5R1E475K080AC (the A1 part)", "same ratings as the A1 part (25 V X5R)"),
 "CL10A105KB8NNNC": ("TDK C1608X5R1H105K080AB (the A1 part)", "same ratings as the A1 part (50 V X5R)"),
 "CC0603KRX7R9BB104": ("KEMET C0603C104K5RACTU (the A1 part); any 0603 100 nF X7R 50 V", "same ratings as the A1 part"),
 "GRM188R71H224KAC4D": ("Samsung CL10B224KB8NNNC (JLCPCB C64705), Yageo CC0603KRX7R9BB224 (C107083): 220 nF 50 V X7R 0603", "LMR33640 input bypass must be 220 nF / 50 V / X7R (data sheet)"),
 "CL31B106KBHNNNE": ("TDK C3216X7R1H106KT0A0E (JLCPCB C694197)", "X7R as the LMR33640 data sheet requires for CIN. A1 flagged this line: 0 at DigiKey. JLCPCB has it in stock"),
 "CL31A226KAHNNNE": ("Samsung CL31A226KOHNNNE (16 V, the A1 part, JLCPCB C90146)", "25 V instead of 16 V, same case height (1.6 mm)"),
}
RES_SECOND = ("Yageo RC0402FR-07 series (the A1 parts), Panasonic ERJ-2RKF, Stackpole RMCF0402FT: any 0402 1 % thick film, >= 1/16 W", "")

def second(mpn):
    if mpn in SECOND: return SECOND[mpn]
    if mpn.startswith("0402WGF"): return RES_SECOND
    return ("", "")

def digikey(mpn):
    alt = DIGIKEY.get(mpn, mpn)
    return alt, PARTS_LIVE.get(alt)

# items that are not on the PCB netlist (module, mechanics, accessories)
EXTRA_CHECKED = "2026-11-12"
EXTRA = [
 dict(function="Compute module", qty=1, buy=1, description="Raspberry Pi Compute Module 4 Lite, 4 GB RAM, wireless, no eMMC", maker="Raspberry Pi", mpn="CM4104000",
      shop="Reichelt.at", article="RPI CM4W 4GBLITE", eur=103.16, pack="1",
      url="https://www.reichelt.at/at/de/shop/produkt/raspberry_pi_compute_modul_4_4gb_ram_lite_wlan-290539",
      second="Semaf Wien 102.00, Welectron 103.00, DigiKey SC0671; CM4102000 (2 GB) is the cheaper drop-in", note="the board has no Ethernet: only wireless variants work"),
 dict(function="Speaker", qty=1, buy=1, description="Enclosed speaker 3 W 4 ohm, 70 x 30 x 17 mm, JST-PH 2-pin plug on a 57 cm lead", maker="Adafruit", mpn="3351",
      shop="BerryBase.at", article="ADA3351", eur=5.50, pack="1", url="https://www.berrybase.at/mono-gehaeuselautsprecher-3w-4-ohm",
      second="none without re-drawing the speaker pocket of the enclosure", note="plugs into J7, no soldering"),
 dict(function="Heat sink", qty=1, buy=1, description="Heat sink set for Raspberry Pi: 14 x 14 x 7 mm (used) + 8.8 x 8.8 x 5 mm, adhesive foil applied", maker="BerryBase", mpn="RPI-2KKS",
      shop="BerryBase.at", article="RPI-2KKS", eur=1.30, pack="set of 2", url="https://www.berrybase.at/2-teiliges-kuehlkoerper-set-fuer-raspberry-pi-schwarz",
      second="BerryBase RPI-4KKS; any 14 x 14 mm heat sink up to 9.5 mm high with adhesive foil", note="on the BCM2711 of the CM4"),
 dict(function="microSD card", qty=1, buy=1, description="microSDXC 64 GB, endurance type (Home Assistant OS writes around the clock)", maker="SanDisk", mpn="SDSQQNR-064G-GN6IA",
      shop="BerryBase.at", article="619659173081", eur=28.90, pack="1",
      url="https://www.berrybase.at/sandisk-high-endurance-microsdxc-uhs-i-u3-speicherkarte-adapter-64gb",
      second="any A1 / A2 class microSD of 32 GB or more", note="flash os/output/haos_voxhub-cm4-*.img.xz"),
 dict(function="Screws CM4 + PCB", qty=8, buy=10, description="Screw M2.5 x 5 mm pan head PH1, DIN 7985 (4 x CM4 to the SMT spacers, 4 x PCB to the shell bosses)", maker="generic", mpn="DIN 7985 M2.5x5",
      shop="BerryBase.at", article="D7985", eur=0.06, pack="single", url="https://www.berrybase.at/schraube-kopf-zylinder-m2-5x5",
      second="ISO 7045 / ISO 14583 M2.5 x 5; Screwerk STP390250060S (2.5 x 6 thread-forming, business customers only) for the bosses", note="never longer than 6 mm"),
 dict(function="Screws base", qty=4, buy=10, description="Screw M2.5 x 8 mm pan head PH1, DIN 7985 (base to the shell posts)", maker="generic", mpn="DIN 7985 M2.5x8",
      shop="BerryBase.at", article="D7988", eur=0.05, pack="single", url="https://www.berrybase.at/schraube-kopf-zylinder-m2-5x8",
      second="M2.5 x 10 also fits; Screwerk STP390250080S (thread-forming, business customers only)", note="head 5.0 mm in a 5.2 mm counterbore"),
 dict(function="Feet", qty=4, buy=1, description="Rubber feet 8 x 3 mm, round, self-adhesive", maker="Delock", mpn="18308",
      shop="Reichelt.at", article="DELOCK 18308", eur=4.89, pack="70",
      url="https://www.reichelt.at/at/de/shop/produkt/gummifuesse_rund_selbstklebend_8_x_3_mm_70_stk_schwarz-371080",
      second="any 8 mm stick-on foot at least 2 mm high", note="base recesses are 8.6 mm"),
 dict(function="Speaker pad", qty=1, buy=1, description="Self-adhesive cellular rubber sheet 3 x 300 x 200 mm (cut 40 x 18 mm for the speaker pedestal)", maker="Jamara", mpn="059850",
      shop="Reichelt.at", article="JAMARA 059850", eur=5.60, pack="1 sheet",
      url="https://www.reichelt.at/at/de/shop/produkt/moosgummiplatte_3_x_300_x_200_mm_selbstklebend_1_stueck-327925",
      second="any soft closed-cell foam about 3 mm thick", note="compressed to about 1.5 mm when the base is closed"),
 dict(function="Power supply", qty=1, buy=1, description="USB-C PD charger 30 W (5 V 3 A, 9 V 3 A, 12 V 2.5 A, 15 V 2 A, 20 V 1.5 A)", maker="Goobay", mpn="79153",
      shop="Reichelt.at", article="GOOBAY 79153", eur=16.54, pack="1",
      url="https://www.reichelt.at/at/de/shop/produkt/usb-ladegeraet_30_w_gan_1x_usb-c_weiss-425716",
      second="Goobay 79155 (65 W); any USB-C PD charger with a fixed 12 / 15 / 20 V profile of 2 A or more", note="the board negotiates 15 V / 2 A"),
 dict(function="USB-C cable", qty=1, buy=1, description="USB-C to USB-C cable, 60 W, 1 m", maker="Shiverpeaks", mpn="BS20-75025",
      shop="Reichelt.at", article="SHVP BS20-75025", eur=5.84, pack="1", url="https://www.reichelt.at/at/de/shop/produkt/sync-_ladekabel_usb-c_60w_1_0_m-378629",
      second="any USB-C to USB-C cable rated 3 A", note=""),
]
EXTRA_SHIPPING = {"Reichelt.at": 6.95, "BerryBase.at": 5.95}
