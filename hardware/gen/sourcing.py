"""Sourcing data per MPN.

Live distributor data (DigiKey part number, lifecycle, stock, unit price at qty 1 and qty 100) is stored in
sourcing_live.json - checked on 2026-11-11 against the DigiKey product pages.  mouser.com refuses automated
access (HTTP 503 for every scripted request), so the Mouser columns only carry what search-engine snippets
showed, or part numbers built from Mouser's prefix scheme ("mouser_pn_unverified" in the JSON); both are marked
in the BOM and must be re-checked by hand before ordering.

This file adds what a database cannot know: second sources and the reason for each choice.
SECOND: MPN -> (second source, note)
"""
import json, os

LIVE = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sourcing_live.json")))
PARTS_LIVE = LIVE["parts"]

SECOND = {
 "CM4104000": ("CM4102000 (2 GB) / CM4108000 (8 GB): drop-in", "DigiKey price 95 USD on 2026-11-11 (memory prices; it was about 55 USD a year earlier), purchase limit, no backorders. Production until >= Jan 2034"),
 "DF40C-100DS-0.4V(51)": ("Hirose DF40HC(3.0)-100DS-0.4V(51): same land pattern, 3.0 mm stack (needs 3 mm spacers)", ""),
 "CYPD3177-24LQXQT": ("none pin-compatible; functional alternates: TI TPS25730, ST STUSB4500 (re-layout)", ""),
 "LMR33640ADDAR": ("no drop-in in stock. Same family and footprint: LMR33640DDDAR (1 MHz, 4,572 in stock at DigiKey) with L1 = 3.3 uH (Bourns SRP7028A-3R3M, same footprint) per the datasheet table - re-validate before use. LMR33630ADDAR (3 A) would be a current downgrade and is out of stock too",
                   "STOCK RISK: 0 at DigiKey, 2,500 expected 08-Jul-2027, 26 weeks lead time - check Mouser / TI store by hand"),
 "SRP7028A-6R8M": ("Bourns SRP7028AA-6R8M (AEC-Q200): drop-in", "Isat 8 A, Irms 4.5 A, 60 mOhm max"),
 "USB2514B-I/M2": ("USB2514BT-I/M2 (tape and reel): same part. USB2514B/M2 is 0-70 C only (downgrade)", ""),
 "TSX-3225 24.0000MF18X-C0": ("Abracon ABM8-24.000MHZ-B2-T (the previous choice; +-20 ppm tolerance / +-50 ppm stability over -20..70 C, 0.53 USD @100) or any 24 MHz 3.2x2.5 mm crystal with CL 18 pF, pads 1/3 = crystal",
                              "replaces the Abracon part: +-10 ppm tolerance and +-10 ppm over -20..+75 C per the Epson brief (DigiKey lists +-18 ppm over -40..85 C) instead of +-20 / +-50 ppm, same CL (18 pF -> 27 pF load capacitors stay), 45 % cheaper"),
 "TPS2553DBVR": ("TPS2553DBVT: the identical device on the 250-piece reel, 2,503 in stock at DigiKey (296-23990-1-ND, 1.36 / 0.79 USD) - order this one if boards are built before the DBVR reel is back. Diodes AP2553W6-7 is NRND, AP22653W6-7 is only rated 3.0-5.5 V",
                 "0 in stock at DigiKey, 3,000 expected mid-December 2026"),
 "61400826021": ("none verified (Same Sky UJ2-ADH-W1-TH has a different footprint)", ""),
 "USB4105-GF-A": ("none verified (GCT USB4105-GF-A-120: same footprint, longer shell stakes)", ""),
 "DM3AT-SF-PEJM5": ("none drop-in (Molex 104031-0811 needs a new footprint)", ""),
 "MAX98357AETE+T": ("no second source; the tube version MAX98357AETE+ is discontinued at DigiKey", ""),
 "ADAU7002ACBZ-R7": ("ADAU7002ACBZ-RL (13 inch reel): same part", ""),
 "IM69D130V01XTSA1": ("Infineon IM69D120V01XTSA1: same package and pin-out, drop-in", ""),
 "MGM240PB32VNA3": ("MGM240PA32VNA3 (+10 dBm): drop-in; MGM240PB32VNA3R = same part on reel", "STOCK RISK: 71 in stock at DigiKey, 30 weeks lead time. Longevity commitment to 2032"),
 "USBLC6-2SC6": ("none needed (27k in stock); note that Nexperia PRTR5V0U2X has a different pin-out", ""),
 "AO3401A": ("Diodes DMP3056L-7: SOT-23 G/S/D, drop-in", ""),
 "2N7002,215": ("Nexperia 2N7002BK,215 (315k in stock at DigiKey) works here (gates see 3.3 V) but is rated VGS +-20 V instead of +-30 V, so it was not swapped in automatically. onsemi 2N7002LT1G is a 115 mA part (current downgrade)",
                "0 in stock at DigiKey at check time (Active); Mouser snippet shows > 2 M (not live)"),
 "SMBJ22A": ("SMBJ22A from Bourns / Diodes / ST / Taiwan Semi: drop-in", ""),
 "SD24C-01FTG": ("no equal-or-better SOD-323 part in stock at DigiKey; Nexperia PESD24VL1BA is discontinued", "thin stock at DigiKey (219)"),
 "SZMM3Z10VT1G": ("onsemi MM3Z10VT1G (same die without AEC-Q101; 0 in stock at check time) or any 10 V SOD-323 zener >= 300 mW", "replaces MM3Z10VT1G, which was out of stock"),
 "150060VS75000": ("any 0603 green LED", ""), "150060RS75000": ("any 0603 red LED", ""),
 "156120GS75000": ("none with the exact reverse-mount footprint in this colour", "2,990 in stock at DigiKey"),
 "156120BS75000": ("Kingbright reverse-mount 1206 blue (verify footprint)", ""),
 "156120RS75000": ("Kingbright reverse-mount 1206 red (verify footprint)", ""),
 "B2B-PH-K-S(LF)(SN)": ("none needed", ""), "61300311121": ("any 1x3 2.54 mm header", "DNP"),
 "JS202011JCQN": ("C&K JS202011SCQN (gull-wing leads; footprint check needed)", ""),
 "9774015151R": ("none needed", ""),
 "T520B107M006ATE070": ("KEMET T520B157M006ATE070 (150 uF): same footprint", ""),
 "CL05B104KO5NNNC": ("any 0402 100 nF X7R >= 16 V", "10,000 in stock at DigiKey"),
 "CL05B103KB5NNNC": ("any 0402 10 nF X7R 50 V", ""), "CL05C270JB5NNNC": ("any 0402 27 pF C0G", ""), "CL05C220JB5NNNC": ("any 0402 22 pF C0G", "DNP"),
 "C1608X7R1C105K080AC": ("KEMET C0603C105K4RACTU, Yageo CC0603KRX7R7BB105 (both in stock): 1 uF 16 V X7R 0603",
                         "replaces the 0402 X5R part: that one keeps only about 0.3 uF at 5 V (buck VCC) and 0.5 uF at 3.3 V (CYPD3177 VDDD needs >= 0.8 uF)"),
 "C1608X5R1E475K080AC": ("Samsung CL10A475KO8NNNC (16 V; 0 in stock at check time)", "replaces the Samsung part (out of stock); 25 V instead of 16 V"),
 "C1608X5R1H105K080AB": ("Samsung CL10A105KB8NNNC (0 in stock at check time)", "replaces the Samsung part (out of stock), identical ratings"),
 "C0603C104K5RACTU": ("Samsung CL10B104KB8NNNC (0 in stock at check time); any 0603 100 nF X7R 50 V", "replaces the Samsung part (out of stock), identical ratings"),
 "GRM188R71H224KAC4D": ("Yageo CC0603KRX7R9BB224, TDK C1608X7R1H224K080AB, Samsung CL10B224KB8NNNC (not looked up live)", "new: LMR33640 input bypass must be 220 nF / 50 V / X7R (datasheet). DigiKey shows no stock figure for this part (17 weeks lead time) - verify before ordering"),
 "CL31B106KBHNNNE": ("Cal-Chip GMC31X7R106K50NT (DigiKey Marketplace only: 2,000-piece minimum at 0.403 USD), TDK C3216X7R1H106K160AC (expected Feb 2027); for a prototype the X5R part CL31A106KBHNNNE fits the footprint",
                     "X7R instead of X5R as the LMR33640 datasheet requires for CIN. STOCK: 0 at DigiKey at check time - 10 uF / 50 V / X7R / 1206 is short everywhere"),
 "CL31A226KOHNNNE": ("TDK C3216X5R1C226M160AB (31,754 in stock, +-20 %, 0.32 USD @100) or Samsung CL31A226KOCLFNC (194k in stock, only 0.85 mm thick -> check DC bias). Murata GRM31CR61C226ME15L is obsolete",
                     "0 in stock at DigiKey at check time (Mouser snippet: 212k, not live). Not swapped: no in-stock part with equal tolerance AND equal DC-bias behaviour"),
}
RES_SECOND = ("Yageo RC0402FR-07 series, Panasonic ERJ-2RKF, Stackpole RMCF0402FT: any 0402 1 % thick film, >= 1/16 W", "")

def second(mpn):
    if mpn in SECOND: return SECOND[mpn]
    if mpn.startswith(("RC0402FR-07", "RMCF0402FT", "WR04X")): return RES_SECOND
    return ("", "")

# items that are not on the PCB netlist (module, mechanics, accessories)
EXTRA = [
 ("Compute module", 1, "Raspberry Pi CM4 Lite, 4 GB, wireless", "Raspberry Pi", "CM4104000"),
 ("Speaker", 1, "Speaker 40 mm, 4 ohm, 3 W, 17.5 mm deep, solder tabs", "Same Sky", "CMS-4017-34SP"),
 ("Speaker lead", 1, "JST PH 2-pin housing (plus 2 crimps SPH-002T-P0.5S and 2 x 80 mm AWG26 wire)", "JST", "PHR-2"),
 ("Heat sink", 1, "Heat sink 14 x 14 x 6 mm for the BCM2711 (add 14 x 14 mm thermal tape)", "Same Sky", "HSB03-141406"),
 ("microSD card", 1, "microSD card >= 32 GB, A1 class or better (flash os/output/haos_voxhub-cm4-*.img.xz)", "SanDisk", "SDSQXAF-032G-GN6MA"),
 ("Screws CM4", 4, "Screw M2.5 x 5 mm pan head (CM4 to SMT spacers)", "generic", "M2.5x5 DIN 7985"),
 ("Screws PCB", 4, "Thread-forming screw for plastic 2.5 x 6 mm (PCB to shell bosses)", "generic", "2.5x6 PT / WN1412"),
 ("Screws base", 4, "Thread-forming screw for plastic 2.5 x 8 mm (base to shell posts)", "generic", "2.5x8 PT / WN1412"),
 ("Foam pad", 1, "Closed-cell foam pad 20 x 20 x 3 mm (speaker clamp) + 2 foam rings 5/2 x 0.5 mm (mic gaskets)", "generic", "EVA / Poron"),
 ("Feet", 4, "Self-adhesive rubber foot 8 mm", "generic", "3M SJ5003 class"),
]
EXTRA_SECOND = {
 "CMS-4017-34SP": ("PUI Audio AS04004PR-R (40 mm, 4 ohm, 3 W, 18.3 mm deep - check the pedestal height)", ""),
 "PHR-2": ("pre-crimped JST PH 2-pin lead", ""),
 "HSB03-141406": ("ATS-52150B-C1-R0 (15 x 15 x 7.5 mm, tape included)", "36 C/W natural convection"),
 "SDSQXAF-032G-GN6MA": ("any A1/A2 microSD >= 32 GB", "consumer item, not carried by DigiKey; about 9 USD retail (estimate)"),
}
GENERIC_PRICE = 0.10      # estimate for screws, foam and feet (hardware-store items)
ESTIMATES = {"SDSQXAF-032G-GN6MA": 9.00}
