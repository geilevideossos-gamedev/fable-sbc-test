"""Sourcing data per MPN (snapshot 2026-11-10, gathered from web-search snapshots of distributor listings).

Fields: digikey PN, mouser PN, unit price USD @ qty 1, lifecycle, second source, note.
"n/v" = the distributor number could not be seen in a snapshot - search the MPN on the distributor site.
Prices marked "~" are estimates (no clean USD snapshot).  Nothing here is a live quote.
"""
S = {
 "CM4104000": ("n/v (DigiKey order code SC0671)", "358-CM4104000", "55.00", "Active (production until >= Jan 2034)",
               "CM4102000 (2 GB) / CM4108000 (8 GB): drop-in", "DigiKey stock snapshots 246-1,810; Mouser 0 at check time"),
 "DF40C-100DS-0.4V(51)": ("H11615CT-ND", "n/v", "1.60", "Active", "Hirose DF40HC(3.0)-100DS-0.4V(51): same land pattern, 3.0 mm stack (needs 3 mm spacers)", "DigiKey 20k-70k"),
 "CYPD3177-24LQXQT": ("n/v (DigiKey product 10238323)", "n/v", "2.01", "Active", "none pin-compatible; functional alternates: TI TPS25730, ST STUSB4500 (re-layout)", "DigiKey 7k-9k, Mouser 15k (tray)"),
 "LMR33640ADDAR": ("n/v (DigiKey product 11308782)", "n/v", "~2.40", "Active", "TI LMR33630ADDAR (3 A): pin-compatible drop-in", "DigiKey 2.6k-3.5k"),
 "SRP7028A-6R8M": ("n/v (DigiKey product 4876742)", "n/v", "~1.05", "Active", "Bourns SRP7028AA-6R8M (AEC-Q200): drop-in", "DigiKey 11.6k; Isat 8 A, Irms 4.5 A, 60 mOhm max"),
 "USB2514B-I/M2": ("USB2514B-I/M2-ND", "579-USB2514B-I/M2", "3.17", "Active", "USB2514BT-I/M2 (reel) / USB2514B/M2 (0-70 C): drop-in", "DigiKey 4k-9k, Mouser 9k"),
 "ABM8-24.000MHZ-B2-T": ("n/v", "n/v", "0.58", "Active", "Abracon ABM8-24.000MHZ-D2-T: drop-in; any 24 MHz 3225 18 pF", "DigiKey 2k-12k; CL = 18 pF -> 27 pF load caps"),
 "TPS2553DBVR": ("n/v", "595-TPS2553DBVR", "0.80", "Active", "Diodes AP2553W6-7: same pin-out and EN polarity (flagged NRND by one aggregator; different ILIM equation)", "Mouser 8k-16k; DigiKey thin at check time"),
 "61400826021": ("732-2107-ND", "n/v", "2.03", "Active", "Same Sky UJ2-ADH-W1-TH (footprint NOT verified)", "DigiKey stock snapshots conflict (8.5k vs 0)"),
 "USB4105-GF-A": ("2073-USB4105-GF-ACT-ND", "n/v", "1.09", "Active", "none verified (GCT USB4105-GF-A-120 = same footprint, different shell stake length)", "DigiKey 127k"),
 "DM3AT-SF-PEJM5": ("n/v", "n/v", "~2.40", "Active", "none drop-in (Molex 104031-0811 needs a new footprint)", "DigiKey 16k"),
 "MAX98357AETE+T": ("n/v", "700-MAX98357AETE+T", "3.19", "Active", "MAX98357AETE+ (tube): same part; no second source", "Mouser 41k"),
 "ADAU7002ACBZ-R7": ("n/v", "n/v", "~3.40", "Active", "ADAU7002ACBZ-RL (13 in reel): same part", "DigiKey 4.1k-6.4k"),
 "IM69D130V01XTSA1": ("n/v", "726-IM69D130V01XTSA1", "2.81", "Active (production)", "Infineon IM69D120V01XTSA1: same package and pin-out, drop-in", "Mouser 36k (regional snapshot), Future 8k"),
 "MGM240PB32VNA3": ("n/v (DigiKey product 16676427)", "634-MGM240PB32VNA3R (reel)", "9.86", "Active (longevity commitment to 2032)", "MGM240PA32VNA3 (+10 dBm): drop-in", "Mouser ~2.1k; DigiKey 0 with 12-20 wk lead at check time"),
 "USBLC6-2SC6": ("497-5235-1-ND", "511-USBLC6-2SC6", "0.36", "Active", "multiple pin-compatible parts (e.g. Nexperia PRTR5V0U2X is NOT the same pin-out - verify)", "DigiKey 67k+, Mouser 100k+"),
 "AO3401A": ("785-1001-1-ND", "n/v", "0.46", "Active", "Diodes DMP3056L-7: SOT-23 G/S/D, drop-in", "DigiKey 14k-287k"),
 "2N7002,215": ("n/v", "n/v", "~0.20", "Active", "onsemi 2N7002LT1G or any SOT-23 2N7002: drop-in", "commodity"),
 "SMBJ22A": ("SMBJ22ALFCT-ND", "576-SMBJ22A", "0.31", "Active", "SMBJ22A from Bourns / Diodes / ST / Taiwan Semi: drop-in", "DigiKey 20k"),
 "SD24C-01FTG": ("n/v", "n/v", "~0.40", "Active", "Nexperia PESD24VL1BA is discontinued - do not use", "DigiKey ~53k"),
 "MM3Z10VT1G": ("n/v (DigiKey product 661697)", "n/v", "~0.15", "Active", "onsemi SZMM3Z10VT1G (AEC-Q101 version, drop-in, DigiKey ~11.9k) or any 10 V SOD-323 zener", "DigiKey 1.3k-2.7k (regional snapshots), 19-43 wk lead"),
 "150060VS75000": ("n/v", "n/v", "0.15", "Active", "any 0603 green LED", "DigiKey 268k"),
 "150060RS75000": ("n/v", "n/v", "~0.15", "Active", "any 0603 red LED", "stock not verified"),
 "156120GS75000": ("n/v", "n/v", "~0.45", "Active", "156120VS75000 (yellow-green): same footprint", "stock not verified"),
 "156120BS75000": ("n/v (DigiKey product 7316092)", "n/v", "~0.45", "Active", "Kingbright reverse-mount 1206 blue (verify footprint)", "DigiKey 2.4k-3.3k"),
 "156120RS75000": ("n/v (DigiKey product 4490056)", "n/v", "~0.40", "Active", "Kingbright reverse-mount 1206 red (verify footprint)", "DigiKey 10.6k"),
 "B2B-PH-K-S(LF)(SN)": ("n/v", "n/v", "~0.17", "Active", "none needed", "DigiKey 53k+"),
 "61300311121": ("n/v", "n/v", "~0.10", "Active", "any 1x3 2.54 mm header", "DNP"),
 "JS202011JCQN": ("n/v (DigiKey product 6137637)", "n/v", "~0.70", "Active", "C&K JS202011SCQN (gull-wing leads; footprint check needed)", "DigiKey 13k-18k"),
 "9774015151R": ("n/v", "n/v", "~0.75", "Active", "none needed", "stock not verified (Farnell/RS list it)"),
 "T520B107M006ATE070": ("399-4009-1-ND", "n/v", "0.88", "Active", "KEMET T520B157M006ATE070 (150 uF): same footprint", "DigiKey 56k-78k"),
 "CL05B104KO5NNNC": ("1276-1001-1-ND", "n/v", "0.10", "Active", "any 0402 100 nF X7R >= 16 V", "DigiKey millions"),
 "CL05A105KO5NNNC": ("1276-1067-1-ND", "n/v", "0.08", "Active", "any 0402 1 uF X5R >= 16 V", "DigiKey 2.2M"),
 "CL10A475KO8NNNC": ("1276-1784-1-ND", "n/v", "0.10", "Active", "any 0603 4.7 uF X5R >= 16 V", "DigiKey 700k+"),
 "CL10A105KB8NNNC": ("n/v", "n/v", "~0.10", "Active (not re-verified)", "any 0603 1 uF X5R/X7R 50 V", "commodity"),
 "CL10B104KB8NNNC": ("n/v", "n/v", "~0.10", "Active (not re-verified)", "any 0603 100 nF X7R 50 V", "commodity"),
 "CL31A106KBHNNNE": ("1276-2876-1-ND (base number 1276-2876 seen)", "n/v", "~0.35", "Active", "TDK C3216X5R1H106K160AB or Yageo CC1206KKX5R9BB106 (10 uF 50 V X5R 1206, drop-in). Murata GRM31CR61H106KA12L is obsolete - do not use", "stock snapshots conflict: DigiKey CA out of stock / UK substitute table ~1.46M; Future 4k"),
 "CL31A226KOHNNNE": ("1276-3048-1-ND", "n/v", "0.35", "Active", "any 1206 22 uF X5R 16 V (not the ...NNWE variant)", "DigiKey 77k"),
 "CL05C270JB5NNNC": ("n/v", "n/v", "~0.10", "Active (not re-verified)", "any 0402 27 pF C0G", "commodity"),
 "CL05C220JB5NNNC": ("1276-1116-1-ND", "n/v", "~0.10", "Active", "any 0402 22 pF C0G", "DNP"),
 "CL05B103KB5NNNC": ("n/v", "n/v", "~0.10", "Active (not re-verified)", "any 0402 10 nF X7R 50 V", "commodity"),
}
RES = ("311-<value>LRCT-ND pattern (311-10.0KLRCT-ND verified for 10k)", "n/v", "0.10", "Active", "any 0402 1% thick-film resistor", "Yageo RC0402FR-07 series, DigiKey 460k+ per value")

# items that are not on the PCB netlist (module, mechanics, accessories)
EXTRA = [
 ("Compute module", 1, "Raspberry Pi CM4 Lite, 4 GB, wireless", "Raspberry Pi", "CM4104000"),
 ("Speaker", 1, "Speaker 40 mm, 4 ohm, 3 W, 17.5 mm deep, solder tabs", "Same Sky", "CMS-4017-34SP"),
 ("Speaker lead", 1, "JST PH 2-pin housing (plus 2 crimps SPH-002T-P0.5S and 2 x 80 mm AWG26 wire)", "JST", "PHR-2"),
 ("Heat sink", 1, "Heat sink 14 x 14 x 6 mm for the BCM2711 (add 14 x 14 mm thermal tape)", "Same Sky", "HSB03-141406"),
 ("microSD card", 1, "microSD card >= 32 GB, A2 class (flash os/output/haos_voxhub-cm4-*.img.xz)", "SanDisk", "SDSQXAF-032G-GN6MA"),
 ("Screws CM4", 4, "Screw M2.5 x 5 mm pan head (CM4 to SMT spacers)", "generic", "M2.5x5 DIN 7985"),
 ("Screws PCB", 4, "Thread-forming screw for plastic 2.5 x 6 mm (PCB to shell bosses)", "generic", "2.5x6 PT / WN1412"),
 ("Screws base", 4, "Thread-forming screw for plastic 2.5 x 8 mm (base to shell posts)", "generic", "2.5x8 PT / WN1412"),
 ("Foam pad", 1, "Closed-cell foam pad 20 x 20 x 3 mm (speaker clamp) + 2 foam rings 5/2 x 0.5 mm (mic gaskets)", "generic", "EVA / Poron"),
 ("Feet", 4, "Self-adhesive rubber foot 8 mm", "generic", "3M SJ5003 class"),
]
SX = {
 "CMS-4017-34SP": ("2223-CMS-4017-34SP-ND", "n/v", "4.99", "Active", "PUI Audio AS04004PR-R (40 mm, 4 ohm, 3 W, 18.3 mm deep)", "DigiKey ~1k, Mouser ~950"),
 "PHR-2": ("455-1165-ND", "n/v", "0.10", "Active", "pre-crimped JST PH 2-pin lead", "DigiKey 750k+"),
 "HSB03-141406": ("n/v (DigiKey product 14567064)", "n/v", "1.12", "Active", "ATS-52150B-C1-R0 (15 x 15 x 7.5 mm, tape included)", "DigiKey 2k-3.5k; 36 C/W natural convection"),
 "SDSQXAF-032G-GN6MA": ("n/v", "n/v", "~9.00", "Active", "any A1/A2 microSD >= 32 GB", "consumer item"),
}
