# VoxHub CM4 - shopping list

Everything you must buy that is **not** on the assembled PCB from JLCPCB. Hardware revision A2.

- The board itself is ordered with [`ORDER_GUIDE.md`](ORDER_GUIDE.md), starting at its section "2. Before ordering:
  account and the parts that are short". The cost of that order is in its section "8. Cost estimate"; the parcel from
  JLCPCB is checked with its section "10. Incoming inspection - before anything is plugged in".
- What to do with the parts of this list is described in [`ASSEMBLY_AND_TEST.md`](ASSEMBLY_AND_TEST.md): section
  "2. Tools and parts on the table" names every part by the line number of this list, section "3. Bring-up before
  assembly" tests the board, section "4. Mechanical assembly" puts the device together.
- Nothing on this list needs soldering or crimping.
- All prices are in EUR **including VAT**, as the shop displayed them for Austria on **2026-11-12**. Shipping is to
  Austria.
- Prices and stock change daily; the compute module at Reichelt.at rose by 2.67 EUR within the morning of
  2026-11-12. The amount in your basket on the day you order is the one that counts.

How each figure was obtained (column "Checked" in the tables below):

| Mark | Meaning |
|---|---|
| R | read from the shop page for this document on 2026-11-12, about 09:00 UTC (re-check of the research notes) |
| L | first looked up for this document on 2026-11-12, about 09:00 UTC (the item is not in the research notes) |
| N | taken from the research notes (shop pages read earlier on 2026-11-12), not read again |

## Already on the board - do not buy

| Part | Why you do not need it |
|---|---|
| Standoffs / spacers for the compute module | The four M2.5 threaded spacers under the compute module (H5 to H8, Wurth 9774015151R, 1.5 mm high) are soldered onto the PCB by JLCPCB as part of the assembly order (line `C5353804` in `fab/jlcpcb/bom_jlcpcb.csv`). The module is screwed straight into them. |
| Nuts, threaded inserts | There are none in the design. Every screw into the printed enclosure forms its own thread in a 2.1 mm hole. |
| Speaker connector J7, microSD socket, USB sockets, Zigbee radio | All soldered by JLCPCB. |
| Thermal paste or thermal tape | The heat sink of this list has its adhesive foil already applied. |

## 1. Required for one device

One definite choice per line. Order exactly the shop article number shown. The bold number in front of each item
is the line number that the rest of this document refers to.

| Item | Qty | Exact part number | Shop | Shop article no. | Price incl. VAT (EUR) | Link |
|---|---|---|---|---|---|---|
| **1** Raspberry Pi Compute Module 4 Lite, wireless, 4 GB RAM, no eMMC | 1 | Raspberry Pi CM4104000 | Reichelt.at | RPI CM4W 4GBLITE | 105.83 | [product page](https://www.reichelt.at/at/de/shop/produkt/raspberry_pi_compute_modul_4_4gb_ram_lite_wlan-290539) |
| **2** Speaker, enclosed, 4 ohm 3 W, flange 70.1 x 30.7 mm, 16.5 mm high, with JST-PH 2-pin plug on a lead of about 50 cm | 1 | Adafruit 3351 | BerryBase.at | ADA3351 | 5.50 | [product page](https://www.berrybase.at/mono-gehaeuselautsprecher-3w-4-ohm) |
| **3** Heat sink set, black: 14 x 14 x 7 mm (used) + 8.8 x 8.8 x 5 mm (not used), adhesive foil applied | 1 set | BerryBase RPI-2KKS | BerryBase.at | RPI-2KKS | 1.30 | [product page](https://www.berrybase.at/2-teiliges-kuehlkoerper-set-fuer-raspberry-pi-schwarz) |
| **4** microSD card SanDisk High Endurance 64 GB, with SD adapter | 1 | SanDisk SDSQQNR-064G-GN6IA (EAN 0619659173081) | BerryBase.at | 619659173081 | 28.90 | [product page](https://www.berrybase.at/sandisk-high-endurance-microsdxc-uhs-i-u3-speicherkarte-adapter-64gb) |
| **5** Screw M2.5 x 5 mm, pan head, cross recess PH1, steel zinc plated | 8 (buy 10) | DIN 7985 M2.5 x 5 | BerryBase.at | D7985 | 0.06 each, 10 pieces = 0.60 | [product page](https://www.berrybase.at/schraube-kopf-zylinder-m2-5x5) |
| **6** Screw M2.5 x 8 mm, pan head, cross recess PH1, steel zinc plated | 4 (buy 10) | DIN 7985 M2.5 x 8 | BerryBase.at | D7988 | 0.05 each, 10 pieces = 0.50 | [product page](https://www.berrybase.at/schraube-kopf-zylinder-m2-5x8) |
| **7** Rubber feet, round, self-adhesive, 8 mm x 3 mm, black, pack of 70 | 4 (1 pack) | Delock 18308 (EAN 4043619183081) | Reichelt.at | DELOCK 18308 | 4.89 | [product page](https://www.reichelt.at/at/de/shop/produkt/gummifuesse_rund_selbstklebend_8_x_3_mm_70_stk_schwarz-371080) |
| **8** Cellular rubber sheet, self-adhesive, 3 x 300 x 200 mm (you cut one piece 40 x 18 mm) | 1 sheet | Jamara 059850 (EAN 4042764129753) | Reichelt.at | JAMARA 059850 | 5.60 | [product page](https://www.reichelt.at/at/de/shop/produkt/moosgummiplatte_3_x_300_x_200_mm_selbstklebend_1_stueck-327925) |
| **9** USB-C PD charger 30 W, white, Euro plug | 1 | Goobay 79153 (EAN 4040849791536) | Reichelt.at | GOOBAY 79153 | 16.54 | [product page](https://www.reichelt.at/at/de/shop/produkt/usb-ladegeraet_30_w_gan_1x_usb-c_weiss-425716) |
| **10** USB-C to USB-C cable, 60 W, 1.0 m | 1 | Shiverpeaks BS20-75025 (EAN 4017538140043) | Reichelt.at | SHVP BS20-75025 | 5.84 | [product page](https://www.reichelt.at/at/de/shop/produkt/sync-_ladekabel_usb-c_60w_1_0_m-378629) |
| **11** PETG filament 1.75 mm, white, 1 kg spool, for the Bambu Lab printer (skip if you have PETG in a light colour) | 1 | Bambu Lab PETG Basic G00-W00-1.75-1000-SPL (EAN 6937285509727) | Reichelt.at | BL G00-W00-SPL | 19.15 | [product page](https://www.reichelt.at/at/de/shop/produkt/filament_petg_basic_weiss_1_75_mm_1_kg-433157) |
| **12** Screwdriver PH1, blade 80 mm (skip if you have a PH1 screwdriver) | 1 | Bernstein 4-624 (EAN 4250838513869) | Reichelt.at | BERN 4 624 | 6.81 | [product page](https://www.reichelt.at/at/de/shop/produkt/esd_schraubendreher_kreuzschlitz_ph_1-298887) |

Stock on 2026-11-12, in the words the shop uses:

| Line | Item | Stock text on the shop page | Checked |
|---|---|---|---|
| 1 | CM4104000, Reichelt | "ab Lager, Lieferzeit: 2 - 3 Werktage" | R |
| 2 | Adafruit 3351, BerryBase | "Sofort verfügbar · 67 Stück · 1-3 Tage" | R |
| 3 | RPI-2KKS, BerryBase | "Sofort verfügbar · 100+ Stück · 1-3 Tage" | R |
| 4 | SanDisk 64 GB, BerryBase | "Sofort verfügbar · 100+ Stück · 1-3 Tage" | R |
| 5 | D7985, BerryBase | "Sofort verfügbar · 100+ Stück · 1-3 Tage" | R |
| 6 | D7988, BerryBase | "Sofort verfügbar · 100+ Stück · 1-3 Tage" | R |
| 7 | DELOCK 18308, Reichelt | "ab Lager, Lieferzeit: 2 - 3 Werktage" | R |
| 8 | JAMARA 059850, Reichelt | "ab Lager, Lieferzeit: 2 - 3 Werktage" | R |
| 9 | GOOBAY 79153, Reichelt | "ab Lager, Lieferzeit: 2 - 3 Werktage" | R |
| 10 | SHVP BS20-75025, Reichelt | "ab Lager, Lieferzeit: 2 - 3 Werktage" | R |
| 11 | BL G00-W00-SPL, Reichelt | "ab Lager, Lieferzeit: 2 - 3 Werktage" | L |
| 12 | BERN 4 624, Reichelt | "ab Lager, Lieferzeit: 2 - 3 Werktage" | L |

Totals for one device (basket A of section 4, two parcels):

| What | EUR |
|---|---|
| Lines 1 to 10 (the parts of the device, 10 + 10 screws) | 175.50 |
| Shipping: Reichelt.at DPD 6.95 + BerryBase.at DHL Paket 5.95 | 12.90 |
| **One device, delivered** | **188.40** |
| Lines 11 and 12 (filament, screwdriver), same Reichelt parcel | 25.96 |
| **One device with filament and screwdriver, delivered** | **214.36** |

Lines 1 to 10 are the same articles, quantities and prices as `hardware/outputs/bom_system.csv` and as the cost table
"Everything else for one device" in `README.md` (175.50 + 12.90 = 188.40 EUR).

Assumed to be at hand, not on this list and not looked up: the Bambu Lab printer; a PC with a microSD or SD card
reader (the card comes with an SD adapter); a Wi-Fi network; and the workshop and household items named in
`ASSEMBLY_AND_TEST.md`, sections "2.2 Only for the bring-up test" and "2.3 Tools": a caliper, drill bits 2.0 mm and
1.5 mm, a sharp knife or scissors, adhesive tape or one small cable tie, a USB memory stick, one Zigbee device.

## 2. Two devices

Quantities for both assembled boards: 2 x line 1, 2 x line 2, 2 x line 3, 2 x line 4, 20 x line 5 (16 used),
10 x line 6 (8 used), 1 x line 7 (8 feet from the same pack of 70), 1 x line 8 (two pads from the same sheet),
2 x line 9, 2 x line 10, 1 x line 11 (one spool prints both enclosures), 1 x line 12.
Total delivered: 352.91 EUR without lines 11 and 12, 378.87 EUR with them (basket A, section 4).

## 3. Optional: tools for the bring-up tests

Only needed for the tests of `ASSEMBLY_AND_TEST.md`, section "3. Bring-up before assembly". The device works
without them.

| Item | Qty | Exact part number | Shop | Shop article no. | Price incl. VAT (EUR) | Stock text | Checked | Link |
|---|---|---|---|---|---|---|---|---|
| **13** USB-C PD charger 20 W, white (test case: 9 V contract) | 1 | Goobay 79151 (EAN 4040849791512) | Reichelt.at | GOOBAY 79151 | 11.90 | "ab Lager, Lieferzeit: 2 - 3 Werktage" | R | [product page](https://www.reichelt.at/at/de/shop/produkt/usb-ladegeraet_20_w_gan_1x_usb-c_weiss-425714) |
| **14** USB-C PD charger 65 W, black (test case: 20 V contract) | 1 | Goobay 79155 (EAN 4040849791550) | Reichelt.at | GOOBAY 79155 | 21.99 | "ab Lager, Lieferzeit: 2 - 3 Werktage" | R | [product page](https://www.reichelt.at/at/de/shop/produkt/usb-ladegeraet_65_w_gan_1x_usb-c_schwarz-425717) |
| **15** USB-C power meter, 4 to 30 V, 0 to 5 A, OLED display | 1 | KWS-1902C | BerryBase.at | 125471 | 7.50 | "Sofort verfügbar · 40 Stück · 1-3 Tage" | R | [product page](https://www.berrybase.at/usb-tester-kws-1902c-fuer-usb-c-4-30v-oled-display) |
| **16** Digital multimeter, 1999 counts, with test leads and battery | 1 | PeakTech P 1070 (EAN 4250569400100) | Reichelt.at | PEAKTECH 1070 | 18.97 | "ab Lager, Lieferzeit: 2 - 3 Werktage" | L | [product page](https://www.reichelt.at/at/de/shop/produkt/multimeter_digital_1999_counts-67138) |

Total of lines 13 to 16: 60.36 EUR. They travel in the same two parcels, so shipping does not change.

| Tool | Used in `ASSEMBLY_AND_TEST.md`, section |
|---|---|
| Chargers 20 W and 65 W (lines 13 and 14) | "3.4 Test 4 - USB PD with a 20 W, a 30 W and a 65 W charger, and with a plain 5 V supply" |
| USB-C power meter (line 15) | "3.3 Test 3 - first power from the 30 W charger" and the charger test above; it shows the voltage without probing |
| Multimeter (line 16) | "3.2 Test 2 - no short circuit (no power, multimeter)", "3.3 Test 3 - first power from the 30 W charger", the charger test above, "3.7 Test 7 - 3.3 V rail" |

- The 30 W charger of line 9 is the third test charger (15 V contract). Lines 13, 9 and 14 are the 20 W, 30 W and
  65 W chargers of the charger test. The cable of line 10 is used with all three.
- A fourth voltage (12 V) can be tested with the Raspberry Pi 27 W USB-C supply (Raspberry Pi SC1152, Reichelt.at
  article RPI PS 27W WT EU, 11.50 EUR, "ab Lager", R). It is not needed for the test plan.
- Multimeter: use the 20 V DC range for the 5 V rail and for 9 V, 12 V and 15 V on VBUS. For the 20 V contract of the
  65 W charger switch to the 200 V DC range, because a 1999-count meter shows at most 19.99 V on the 20 V range.
  DC ranges of the P 1070 per the shop page: 200 mV / 2000 mV / 20 V / 200 V / 300 V, +-0.8 % + 2 digits; continuity
  buzzer below 50 ohm.

## 4. Baskets per shop

### 4.1 Basket A - two parcels (Reichelt.at + BerryBase.at) - use this one

No shop that was checked has everything: Reichelt.at does not list the Adafruit 3351 (search, L) or M2.5 x 5 /
M2.5 x 8 machine screws (N); BerryBase.at cannot deliver the CM4104000 today (R) and has no 8 mm feet in stock (N).
Two parcels is the minimum.

Shipping to Austria (R): Reichelt.at DPD up to 10 kg 6.95 EUR (DHL 9.95, UPS 12.95). BerryBase.at "DHL Paket" 5.95 EUR
for an order value of 0.01 to 199.99 EUR, free from 200.00 EUR (UPS Standard 14.00).

| Shop | Item | Shop article no. | Qty, one device | EUR, one device | Qty, two devices | EUR, two devices |
|---|---|---|---|---|---|---|
| Reichelt.at | CM4 Lite 4 GB wireless | RPI CM4W 4GBLITE | 1 | 105.83 | 2 | 211.66 |
| Reichelt.at | Rubber feet 8 x 3 mm, 70 pieces | DELOCK 18308 | 1 | 4.89 | 1 | 4.89 |
| Reichelt.at | Cellular rubber sheet 3 mm | JAMARA 059850 | 1 | 5.60 | 1 | 5.60 |
| Reichelt.at | Charger 30 W | GOOBAY 79153 | 1 | 16.54 | 2 | 33.08 |
| Reichelt.at | USB-C cable 1 m | SHVP BS20-75025 | 1 | 5.84 | 2 | 11.68 |
| Reichelt.at | Shipping DPD | | | 6.95 | | 6.95 |
| | **Reichelt.at subtotal** | | | **145.65** | | **273.86** |
| BerryBase.at | Speaker | ADA3351 | 1 | 5.50 | 2 | 11.00 |
| BerryBase.at | Heat sink set | RPI-2KKS | 1 | 1.30 | 2 | 2.60 |
| BerryBase.at | microSD 64 GB | 619659173081 | 1 | 28.90 | 2 | 57.80 |
| BerryBase.at | Screw M2.5 x 5 | D7985 | 10 | 0.60 | 20 | 1.20 |
| BerryBase.at | Screw M2.5 x 8 | D7988 | 10 | 0.50 | 10 | 0.50 |
| BerryBase.at | Shipping DHL Paket | | | 5.95 | | 5.95 |
| | **BerryBase.at subtotal** | | | **42.75** | | **79.05** |
| | **Total, delivered** | | | **188.40** | | **352.91** |

Additions to the same two parcels (no extra shipping):

| Addition | Parcel | EUR |
|---|---|---|
| Filament BL G00-W00-SPL 19.15 + screwdriver BERN 4 624 6.81 | Reichelt.at | 25.96 |
| Bring-up tools: GOOBAY 79151 11.90 + GOOBAY 79155 21.99 + PEAKTECH 1070 18.97 | Reichelt.at | 52.86 |
| Bring-up tool: USB-C power meter 125471 | BerryBase.at | 7.50 |

Everything on this page: 274.72 EUR for one device, 439.23 EUR for two devices.

How to order:

1. Open the links of sections 1 and 3 for the Reichelt.at lines (1, 7, 8, 9, 10, 11, 12 and, if wanted, 13, 14, 16).
2. On each page compare the text after "Artikel-Nr.:" with the column "Shop article no.". For the compute module it
   must read `RPI CM4W 4GBLITE` and "Hst.-Teile-Nr.:" must read `CM4104000`. The article `RPI CM4 4GBLITE` (without
   the W, 100.54 EUR) is the module **without** Wi-Fi (CM4004000) - do not take it.
3. Check the stock line under the price. "ab Lager, Lieferzeit: 2 - 3 Werktage" means in stock.
   "Voraussichtlich lieferbar ab: (date)" or "z.Zt. nicht lieferbar" means not in stock: for the compute module switch
   to basket B, for any other line see section 6.
4. Set the quantity (table above) and put the article into the basket ("Warenkorb").
5. At checkout choose DPD as carrier (6.95 EUR to Austria up to 10 kg). Reichelt.at shows its prices
   "inkl. 20% gesetzl. MwSt." and "zzgl. Versandkosten".
6. Open the links for the BerryBase.at lines (2, 3, 4, 5, 6 and, if wanted, 15).
7. On each page compare the text after "Artikelnummer:" with the column "Shop article no.".
8. Check the stock line. "Sofort verfügbar · (number) Stück · 1-3 Tage" means in stock. "Artikel aktuell nicht
   lieferbar" means not deliverable.
9. Set the quantity - the screws are sold singly, enter 10 (for two devices 20 of D7985) - and press
   "In den Warenkorb".
10. Choose "DHL Paket" (5.95 EUR) and pay.
11. When the BerryBase.at parcel arrives, check the plug of the speaker before you do anything else with it:
    section 5.2, "Check the plug when the parcel arrives".

### 4.2 Basket B - three parcels (compute module from Semaf, Vienna)

Use it if Reichelt.at has no stock of the compute module, or to save a few euros.

Semaf Electronics (electronics.semaf.at, Alserbachstrasse 10, 1090 Wien, official Austrian Raspberry Pi distributor):
SKU `CM4104000`, **102.00 EUR** "inkl. 20% USt.", "10 Stück im Geschäftslokal lagernd", "Lieferzeit: ca. 1 - 3
Werktage" (R). Shipping within Austria from 6.50 EUR, free from 99 EUR (banner on the shop page, R); pick-up in the
shop is possible (N).
[product page](https://electronics.semaf.at/Compute-Module-4-mit-Wireless-mit-4GB-RAM-0GB-eMMC-Lite)

| Parcel | One device (EUR) | Two devices (EUR) |
|---|---|---|
| Semaf: CM4104000, shipping free | 102.00 | 204.00 |
| Reichelt.at: basket A without the compute module, + 6.95 shipping | 39.82 | 62.20 |
| BerryBase.at: as basket A | 42.75 | 79.05 |
| **Total, delivered** | **184.57** | **345.25** |
| Difference to basket A | -3.83 | -7.66 |

### 4.3 Cheaper variants

| Variant | Change | One device, delivered (EUR) |
|---|---|---|
| 2 GB module | CM4102000 from BerryBase.at instead of line 1: 69.00 EUR, "Sofort verfügbar · 16 Stück" (R), [product page](https://www.berrybase.at/raspberry-pi-compute-module-4/ram-2gb/flash-ohne-lite-/wlan-bluetooth-ja) - "Artikelnummer:" must read `CM4102000`. Limits: section 5.1 | 151.57 |
| Raspberry Pi 27 W supply | RPI PS 27W WT EU (11.50 EUR, cable attached) instead of lines 9 and 10 (22.38 EUR). 12 V contract, 27 W. Limits: section 5.8 | 177.52 |

## 5. Notes per item

### 5.1 Compute module (line 1)

Why CM4104000:

| Part number | RAM | Wi-Fi / Bluetooth | eMMC | Verdict |
|---|---|---|---|---|
| **CM4104000** | 4 GB | yes | none (Lite) | **Buy this.** Cheapest variant that runs Home Assistant OS with the voice add-ons with headroom; the variant the BOM, the OS image and the thermal estimate of this repository are written for. |
| CM4102000 | 2 GB | yes | none (Lite) | Fallback, about 37 EUR cheaper. 2 GB is the minimum Home Assistant states ("make sure to choose a model with at least 2 GB of RAM", home-assistant.io/installation/raspberrypi, read 2026-11-12). Little headroom: Home Assistant Core, Supervisor, Whisper, Piper, openWakeWord and the Zigbee stack run at the same time (estimate of the research notes, not measured: 1.6 to 1.9 GB in use). Use the Whisper model `tiny-int8` or Speech-to-Phrase. |
| CM4108000 | 8 GB | yes | none (Lite) | Works, not worth it: 179.09 EUR at Reichelt.at (R). More RAM does not make speech recognition faster; the about 8 s Whisper needs on a Raspberry Pi 4 are CPU time, identical on every CM4. |
| CM4101000 | 1 GB | yes | none (Lite) | **Does not work**: below Home Assistant's 2 GB minimum. |
| CM4004000 and every other number that starts with CM40 | any | **no** | any | **Does not work.** The carrier board has no Ethernet socket (and no HDMI). The Wi-Fi of the module is the only network connection of the device; a module without it can never be reached. |
| Numbers that end in 008, 016 or 032 (for example CM4104016) | any | any | 8 / 16 / 32 GB | **Do not buy.** The board boots from its microSD socket, and the SD card signals exist only on Lite modules (CM4 datasheet, section 2.11 "SDIO/eMMC (CM4Lite only)"). Writing an eMMC module would need the solder jumper JP1. |

How to read the number: `CM4` + `1` (wireless, `0` = none) + `04` (GB of RAM) + `000` (GB of eMMC, `000` = Lite).

Must match if you buy elsewhere: the manufacturer part number `CM4104000` (or `CM4102000`), nothing else.
DigiKey sells the same module under the name SC0671 (base product number CM4104000).

No Ethernet adapter or cable is on this list. Home Assistant's installation page calls an Ethernet connection
"Required for installation"; for this board the Wi-Fi name and password are written into the OS image instead
(`os/build-image.sh --wifi-ssid ... --wifi-psk ...`; `ASSEMBLY_AND_TEST.md`, section "3.6 Test 6 - first boot of
Home Assistant OS").

### 5.2 Speaker (line 2)

- Why this one: it is the only speaker with a factory-fitted 2-pin JST-PH plug, 4 ohm, 3 W, that was found in stock
  at an EU shop. The plug goes into J7 on the board as delivered. The speaker pocket of the enclosure is drawn for
  exactly this part.
- The maker's data sheet (C5282-001) is linked from the Adafruit product page:
  https://cdn-shop.adafruit.com/product-files/3351/C5282-001_datasheet__1_.pdf (read 2026-11-12). The enclosure
  follows it:

| Property | Data sheet | Enclosure (`enclosure/voxhub_enclosure.py`) |
|---|---|---|
| Flange | 70.11 x 30.72 mm, +-0.3 mm | locating frame 71.3 x 31.9 mm inside (0.6 mm clearance per side), 3 mm high |
| Total height | 16.5 +-0.5 mm | the pedestal of the base ends 18.5 mm below the inside of the top plate = 16.5 mm speaker + 2.0 mm compressed foam |
| Sound opening | oblong, not dimensioned in the drawing | oblong grille 46 x 24 mm with a 1 mm deep relief behind it |
| Impedance, power | 4.0 ohm +-15 %, rated 3 W, maximum 3.2 W | the amplifier MAX98357A delivers up to 3.2 W into 4 ohm |
| Lead | 500 +-10 mm (the shop pages say 22.5 inch = 57 cm) | coiled in the speaker bay |
| Plug | the drawing names it "XH2.54-2P"; Adafruit and BerryBase say "JST 2PH" | J7 is a JST-PH header, 2.0 mm contact spacing - see the check below |

- **No substitute.** Any other speaker means re-drawing `enclosure/voxhub_enclosure.py` and printing again. The
  research notes name one runner-up, Pimoroni COM1606 (UK shop, 3.95 EUR, N); it needs a square pocket and is
  therefore not an option for this build.
- Polarity does not matter: the amplifier output is bridge-tied, neither wire is ground. Plug it in as it comes.
- Do not shorten the lead - shortening means soldering. Where the surplus goes: `ASSEMBLY_AND_TEST.md`, sections
  "4.3 Speaker into its frame" and "4.5 Speaker lead".
- **No separate speaker lead is needed.** Do **not** buy the JST-PH pigtail (BerryBase.at article AK-PH20-2P,
  "Kabel mit JST PH 2.0mm Steckverbinder, AWG26, 20cm", 0.33 EUR): it has bare wire ends and would have to be soldered
  to a speaker. Do not buy the Same Sky CMS-4017-34SP of revision A1 either: it has solder terminals and does not
  fit the pocket.

**Check the plug when the parcel arrives.** The drawing in the maker's data sheet names the plug "XH2.54-2P", a
plug with 2.5 mm contact spacing. Adafruit and BerryBase sell the speaker with a JST-PH plug (2.0 mm), and the
product photos show a small white PH housing. J7 on the board is JST-PH (2.0 mm). Which plug the delivered speaker
has can only be seen on the part:

1. Take the speaker out of its bag. At the end of the red and black lead is a small white plug with two contacts.
2. Measure the width of the white plug across the two wires with a ruler or a caliper and compare:

| | Right plug (JST-PH) | Wrong plug (XH) |
|---|---|---|
| Distance between the two contacts | 2.0 mm | 2.5 mm |
| Width of the white housing | 5.8 mm (JST PHR-2) | 7.3 mm (JST XHP-2), visibly wider |
| On J7 of the board | slides on with light finger pressure, one way round only | does not go on |

3. Right plug: nothing to do. It is plugged into J7 in `ASSEMBLY_AND_TEST.md`, section
   "3.5 Test 5 - fit the heat sink, the compute module, the card and the speaker".
4. Wrong plug: **do not force it onto J7** and do not bend the two pins of J7. Return the speaker to the shop; the
   article text promises a "JST 2PH" cable. Do not buy a pigtail, an adapter or a loose plug that needs soldering or
   crimping. Note the result in the repository so that this list is corrected.

The widths are JST's own dimensions for the 2-pin housings of the PH series (2.0 mm) and the XH series (2.5 mm),
from JST's catalogues, read 2026-11-12. Housings of other makers can differ by a few tenths of a millimetre.

### 5.3 Heat sink (line 3)

- Why this one: 14 x 14 x 7 mm, aluminium, thermally conductive adhesive foil already applied - peel and stick onto
  the large chip (BCM2711) of the compute module. 1.30 EUR in the BerryBase parcel.
- The small 8.8 x 8.8 x 5 mm heat sink of the set is not used.
- Must match if substituted: base 14 x 14 mm, height not more than 9.5 mm including the adhesive, adhesive foil
  included. The enclosure model leaves 5.7 mm of air under the 7 mm heat sink (`enclosure/README.md`).
  A heat sink without foil (for example Fischer ICK BGA 14 X 14 at Reichelt.at, 1.16 EUR, N) needs thermal tape and is
  not for this build. BerryBase PKKRPI (13 x 13.5 x 10 mm) is too tall.
- No fan is needed.
- Fitted in `ASSEMBLY_AND_TEST.md`, section "3.5 Test 5 - fit the heat sink, the compute module, the card and the speaker".

### 5.4 microSD card (line 4)

- Why this one: Home Assistant OS writes to the card around the clock, so an endurance card is the useful type.
  64 GB costs 2.00 EUR more than the 32 GB card of the same series (26.90 EUR, BerryBase.at article 619659173067, N).
- Minimum size: 32 GB ("Make sure to use a card that provides at least 32 GB.", home-assistant.io/installation/raspberrypi,
  read 2026-11-12).
- The same page says "Ideally get one that is Application Class 2." The shop title of the High Endurance card names
  speed class U3 and no application class. The card interface of the board runs in 50 MHz high-speed mode, so the
  extra speed of an A2 card is not used; endurance was preferred. Runner-up with the A2 mark: SanDisk Extreme 64 GB
  A2 U3 V30, BerryBase.at article 619659193409, 26.50 EUR (N).
- Must match if substituted: microSD format (not full-size SD), 32 GB or more.

### 5.5 Screws (lines 5 and 6)

| Joint | Qty | Screw | What it goes into |
|---|---|---|---|
| Compute module onto the board | 4 | M2.5 x 5 | the four threaded spacers that JLCPCB soldered onto the PCB |
| PCB into the shell | 4 | M2.5 x 5 | four printed bosses, hole 2.1 mm, 5.2 mm deep |
| Base onto the shell | 4 | M2.5 x 8 | four printed posts, hole 2.1 mm, 10 mm deep |

- Why machine screws: thread-forming screws for plastic in 2.5 mm are sold in small quantities to businesses only
  (Screwerk). An M2.5 machine screw cuts its own thread in the printed 2.1 mm hole.
- Why BerryBase: single pieces at 0.05 to 0.06 EUR in a parcel that is ordered anyway. Reichelt.at lists no
  M2.5 x 5 or M2.5 x 8 machine screws (N).
- **Keep the two lengths apart.** The 8 mm screws are for the base only. In a PCB boss an 8 mm screw breaks through
  the top of the enclosure (hole 5.2 mm + PCB 1.6 mm = 6.8 mm; 0.8 mm of plastic remain above the hole).
- Must match if substituted:

| Property | Requirement | Reason |
|---|---|---|
| Thread | M2.5 | spacers are M2.5; PCB holes are 2.7 mm |
| Length, compute module | 5 mm (4 to 6 mm work, never longer than 6 mm) | 2.9 mm of thread in the spacer |
| Length, PCB into shell | 5 mm (6 mm also fits, never longer) | see above |
| Length, base | 8 mm (10 mm also fits) | hole 10 mm deep, 1.0 mm of base plate under the head |
| Head | pan head or cheese head, diameter 5.0 mm or less, not countersunk | the recess in the base is a flat-bottomed counterbore of 5.2 mm; flange-head screws with a 6.5 mm head do not fit |
| Drive | PH1 matches the screwdriver of line 12 | |

- No nuts, no washers, no inserts.
- Where they are used: `ASSEMBLY_AND_TEST.md`, sections "3.5 Test 5 - fit the heat sink, the compute module, the card and the speaker" (compute module),
  "4.4 Board onto the bosses - 4 x M2.5 x 5" and "4.7 Base - 4 x M2.5 x 8".

### 5.6 Rubber feet (line 7)

- Why this one: the base has four recesses of 8.6 mm diameter, 0.5 mm deep. An 8 mm foot fits; 3 mm height leaves
  2.5 mm under the base, which clears the heads of the base screws (they stand 0.5 to 0.6 mm proud) and lets air
  reach the vents in the base.
- Must match if substituted: diameter 8 mm, height at least 2 mm, self-adhesive.
- Does not fit: 3M Bumpon SJ5003 (11.1 mm diameter).
- Stuck on in `ASSEMBLY_AND_TEST.md`, section "4.8 Feet".

### 5.7 Cellular rubber for the speaker pad (line 8)

- What it is for: one piece of 40 x 18 mm is stuck onto the flat pedestal of the base (the pedestal is 40 x 18 mm).
  When the base is closed the pad is squeezed from 3 mm to about 2 mm and presses the speaker into its frame
  (`ASSEMBLY_AND_TEST.md`, section "4.2 Foam pad on the base").
- One sheet (300 x 200 mm) is enough for many pads.
- Must match if substituted: soft cellular rubber or closed-cell foam, 3 mm thick, self-adhesive. The gap between
  the pedestal and the speaker is 2.0 mm: a pad thinner than that does not hold the speaker, and a hard pad of 3 mm
  keeps the base from closing.
- Not on the list on purpose: foam rings for the two microphone openings. `enclosure/README.md` calls them optional
  and not needed for a first build, and no shop that was searched sells closed-cell foam of 0.5 mm.

### 5.8 Charger and cable (lines 9 and 10)

What the board asks for: it negotiates USB Power Delivery and takes the **highest-voltage fixed profile (PDO) between
9 V and 20 V that offers at least 2 A**. Programmable ranges (PPS) are ignored. If no profile qualifies, the board stays
at 5 V, the red LED D4 "PD FAULT" on the board lights and nothing else starts. The theoretical peak demand at the
USB-C socket is 19.5 W; realistic operation stays below 12 W. `README.md` asks for a charger of 27 W or more.

Profiles of the chargers, from the manufacturer's data (Goobay data read from wentronic.com, Raspberry Pi product
brief; N), and the contract that follows from the rule above (derived, not measured - no board exists yet; the
measurement is `ASSEMBLY_AND_TEST.md`, section "3.4 Test 4 - USB PD with a 20 W, a 30 W and a 65 W charger, and with a plain 5 V supply"):

| Charger | Fixed profiles | Contract the board gets | Verdict |
|---|---|---|---|
| **Goobay 79153, 30 W** (line 9) | 5 V 3 A, 9 V 3 A, 12 V 2.5 A, 15 V 2 A, 20 V 1.5 A | **15 V / 2 A = 30 W** (20 V 1.5 A is skipped: below 2 A) | **Buy this** as the permanent supply |
| Goobay 79155, 65 W (line 14) | 5 V 3 A, 9 V 3 A, 12 V 3 A, 15 V 3 A, 20 V 3.25 A | 20 V | Works. Runner-up if the charger should also feed a laptop |
| Raspberry Pi 27 W, SC1152 | 5.1 V 5 A, 9 V 3 A, 12 V 2.25 A, 15 V 1.8 A | 12 V / 2.25 A = 27 W (15 V 1.8 A is skipped) | Works. Cheapest that works; cable attached; below the 30 W chosen here |
| Goobay 79151, 20 W (line 13) | 5 V 3 A, 9 V 2.2 A, 12 V 1.7 A | 9 V / 2.2 A = 20 W (12 V 1.7 A is skipped) | Test case only: 0.5 W above the theoretical peak |

Chargers that do not work, or not well:

| Charger | What happens |
|---|---|
| Any 18 W or 20 W PD charger whose 12 V profile is below 2 A | Runs on 9 V with 18 to 20 W. Enough for a desk test, too little reserve as the permanent supply when both USB ports feed devices and the speaker plays. |
| USB-A chargers, USB ports of a computer, 5 V-only USB-C supplies, power banks without Power Delivery, chargers that only speak Quick Charge | No Power Delivery profile between 9 V and 20 V: the board stays off, red LED D4 lights. |
| PD chargers whose profiles between 9 V and 20 V all offer less than 2 A | Same: the board stays off. |
| Chargers that reach 9 V or more only through PPS | Same: PPS is ignored. |
| A USB-A to USB-C cable on any charger | Power Delivery does not work over USB-A: the board stays off. |
| Multi-port chargers | May interrupt or renegotiate the output when a second device is plugged in, which restarts the VoxHub. General behaviour of such chargers, not tested for any model. Use a single-port charger. |

Must match if the charger is substituted:

| Requirement | Value |
|---|---|
| Output | USB-C socket or fixed USB-C cable, USB Power Delivery |
| To work at all | at least one **fixed** profile between 9 V and 20 V with 2 A or more |
| As the permanent supply | 27 W or more: a fixed 12 V, 15 V or 20 V profile with 2 A or more, or 9 V with 3 A. The profiles are printed on the charger, for example "15.0V 2.0A" |
| Ports | one |

The Goobay 79152 is the black version of the 79153 (N, price not looked up).

Cable (line 10): USB Type-C plug on both ends, 60 W = 3 A, USB 2.0, 1.0 m (shop page, R). Must match if substituted:
USB-C on both ends, rated 3 A (60 W). The 2.0 m version is SHVP BS20-75035, 7.25 EUR, "ab Lager" (R). The
Raspberry Pi 27 W supply has its cable attached and needs none.

### 5.9 Filament (line 11)

- Why PETG: `enclosure/README.md` recommends it over PLA because the area around the voltage converter reaches
  about 60 C (`ASSEMBLY_AND_TEST.md`, section "1.3 Material").
- Why white: the three status LEDs shine through a 0.4 mm skin of the top cover. A light colour keeps them visible.
- Why this article: Bambu Lab's own PETG on a spool with RFID tag, in stock at Reichelt.at, in a parcel that is
  ordered anyway.
- Amount (estimate, calculated from the STL files of this repository, not from a slicer): shell 50.9 cm3 + base
  29.2 cm3 = about 80 cm3 of solid plastic. At 1.25 g/cm3, the density that `ASSEMBLY_AND_TEST.md`, section
  "1.4 Print time and filament (estimates, not sliced)", takes from the Bambu PETG Basic preset, that is at most
  about 100 g per enclosure even at 100 % infill, so about 200 g for two. One 1 kg spool is enough several times over.
- Must match if substituted: PETG, 1.75 mm, light colour.

### 5.10 Screwdriver (line 12)

All twelve screws have a PH1 cross recess (`ASSEMBLY_AND_TEST.md`, section "2.3 Tools"). The Bernstein 4-624 is a PH1 x 80 mm screwdriver with an ESD-safe handle
(blade diameter 4.5 mm, total length 180 mm; shop page, L). Any PH1 screwdriver does the job. A PH0 or PH2 tip does
not fit the recess properly.

### 5.11 USB-C power meter (line 15)

The KWS-1902C is connected in line between the charger and the board and shows voltage and current (4 to 30 V,
0 to 5 A, "Kompatibel mit PD3.0/PD2.0" per the shop page, R). That is enough to see whether the contract is 9, 12, 15 or 20 V.
Runner-up: FNIRSI FNB58 (BerryBase.at article FNI-FNB58, 49.90 EUR, listed today; 8 in stock per the notes, N),
which also lists the profiles a charger offers.

## 6. Second sources

"Incl. VAT" is the price the shop displayed; the VAT rate is named where the shop names it.

| Item | Second source | Article no. there | Price incl. VAT (EUR) | Stock on 2026-11-12 | Checked | Remark |
|---|---|---|---|---|---|---|
| CM4104000 | Semaf Electronics, Wien | CM4104000 | 102.00 (20 %) | "10 Stück im Geschäftslokal lagernd" | R | First choice if Reichelt is out of stock: basket B |
| CM4104000 | DigiKey.at | 2648-SC0671-ND (SC0671) | 101.20 (84.33 excl. VAT) | 525 | R | Purchase limit per customer every 30 days, no backorders. Shipping cost to Austria not retrieved |
| CM4104000 | Welectron (Germany) | RP1-402790 | 103.00 (19 % German VAT shown) | "ab Lager lieferbar" | R | UPS Standard to Austria 9.90 EUR up to 2 kg (N). VAT rate at checkout for Austria not tested |
| CM4104000 | BerryBase.at | CM4104000 | 104.80 | "Artikel aktuell nicht lieferbar" | R | Would move the module into the BerryBase parcel (still two parcels); not deliverable today |
| CM4104000 | JLCPCB / LCSC parts library | C20754867 | 141.35 USD, excl. VAT | 6 at JLCPCB; LCSC stock not returned | L | Not sensible: dearer, and shipped from China |
| CM4104000 | Mouser | - | - | - | - | Not retrievable: mouser.at denies automated access |
| CM4102000 (fallback) | BerryBase.at | CM4102000 | 69.00 | "Sofort verfügbar · 16 Stück" | R | Section 4.3 |
| CM4102000 (fallback) | Welectron (Germany) | RP1-402750 | 66.90 (19 % German VAT shown) | "ab Lager lieferbar" | R | Plus 9.90 EUR shipping (N) |
| CM4102000 (fallback) | Reichelt.at | RPI CM4W 2GBLITE | 68.52 | "Voraussichtlich lieferbar ab: 5.12.2026" | R | Not in stock |
| Speaker Adafruit 3351 | DigiKey.at | 3351-ND (as read, see section 7) | 4.21 (3.51 excl. VAT) | 30 | L | Same part, "SPEAKER 4OHM TOP PORT". Shipping cost not retrieved |
| Speaker Adafruit 3351 | adafruit.com (USA) | 3351 | 3.95 USD, excl. VAT | "In stock" | L | Ships from the USA; only if no EU shop has it |
| Heat sink | BerryBase.at | RPI-4KKS | 1.90 | "Sofort verfügbar · 100+ Stück" | R | 4-piece set, silver; contains a 14 x 14 x 7 mm heat sink with adhesive foil (contents N) |
| microSD card, same part | Reichelt.at | SDSQQNR064GGN6IA | 27.99 | "begrenzte Stückzahl" | R | Limited stock |
| microSD card, A2 runner-up | BerryBase.at | 619659193409 | 26.50 | 100+ | N | SanDisk Extreme 64 GB A2 |
| Screw M2.5 x 8 (base) | BerryBase.at | M25X10D7985 | 0.03 each | 83 | N | M2.5 x 10; fits the base only |
| Screws, thread-forming, for plastic | Screwerk (Germany) | STP390250060S (2.5 x 6), STP390250080S (2.5 x 8) | net 0.65 / 0.60 each from 10 | 361,810 / 933,615 | N | Sells to businesses only, minimum order 15 EUR, UPS 11.50 EUR. Torx T8 drive |
| Rubber feet | Reichelt.at | SUPRA EP 8MM | 3.82 (100 pieces) | "ab Lager" | R | 8 x 2 mm, transparent; 1.5 mm under the base instead of 2.5 mm |
| Cellular rubber | - | - | - | - | - | The notes name no second article. Any craft or hardware shop sells 3 mm self-adhesive cellular rubber ("Moosgummi selbstklebend 3 mm") |
| Charger | Reichelt.at | GOOBAY 79155 | 21.99 | "ab Lager" | R | 65 W, 20 V contract |
| Charger | Reichelt.at / BerryBase.at | RPI PS 27W WT EU / RPI5NT5AW | 11.50 / 12.40 | "ab Lager" / "100+ Stück" | R | Raspberry Pi 27 W, 12 V contract, cable attached |
| Charger | eu.ugreen.com | UGREEN Nexode 30 W, model 90666 | 29.99 | available | N | Same profiles as the Goobay 79153 (manufacturer page) |
| USB-C cable | Reichelt.at | SHVP BS20-75035 | 7.25 | "ab Lager" | R | 2.0 m |
| Filament | 3DJake.at | BL-G02-K0-1.75-1000-SPL (Bambu Lab PETG HF Black) | 25.99 | out of stock | R | Black hides the LEDs; not recommended |
| USB-C power meter | BerryBase.at | FNI-FNB58 | 49.90 | 8 | N | Section 5.11 |

LCSC / JLCPCB: only the compute module was looked up there; the research notes have no LCSC data for the other
items. Conrad.at, Amazon.de, Geizhals.at, Cyberport.at and voelkner.at could not be read on 2026-11-12.

## 7. What could not be verified

1. **Mouser:** mouser.at answers "Access to this page has been denied" to automated access. No Mouser price or stock is
   given for any item. The Mouser number 358-SC0671 in `hardware/gen/sourcing_live.json` comes from search-engine
   snippets of 2026-11-11, not from Mouser.
2. **LCSC:** the stock of the compute module at LCSC (C20754867) was not returned by the lookup; the 6 pieces and the
   price are JLCPCB's parts library. No other item of this list was looked up at LCSC.
3. **DigiKey.at:** shipping cost and free-shipping threshold for Austria were not retrieved. The DigiKey article
   number of the Adafruit 3351 was read as "3351-ND" by one automated reading of the search page and not confirmed
   by a second one.
4. **Welectron:** the shop displays German VAT (19 %); the rate at checkout for delivery to Austria was not tested.
   The shipping price (UPS Standard 9.90 EUR) is from the notes and was not read again.
5. **Conrad.at, Amazon.de, Geizhals.at, Cyberport.at, voelkner.at, TME:** not retrievable on 2026-11-12. Nothing from
   these shops is in this list.
6. **Bambu Lab EU store:** not retrievable (every request is redirected to the US store). The filament price is
   Reichelt's, not Bambu Lab's.
7. **Speaker plug:** the drawing in the maker's data sheet (C5282-001) names the plug "XH2.54-2P" (2.5 mm);
   Adafruit and BerryBase describe a "JST 2PH" plug (JST-PH, 2.0 mm) and their photos show a small white PH housing.
   The documents do not settle which plug the delivered speaker has - check it as described in section 5.2. The
   data sheet and the shop pages also differ in the lead length (500 mm / 22.5 inch) and in the weight
   (50 g / 26.4 g).
8. **Charger profiles:** read from manufacturer pages (Goobay via wentronic.com because goobay.com was unreachable),
   not measured. The contract per charger is derived from these tables and the strap settings of the PD controller;
   no board exists yet. The profiles of the Apple 20 W charger and of the Anker Nano 3 30 W (A2337) were not
   verified, so neither is recommended here. The statement about multi-port chargers is general, not tested.
9. **RAM use on a 2 GB module** (1.6 to 1.9 GB): an estimate of the research notes, neither measured nor documented
   by Home Assistant.
10. **Filament amount:** an upper bound calculated from the STL volumes with a density of 1.25 g/cm3 (not checked
    against Bambu Lab's data sheet), not a slicer result.
11. **Screw head in the base recess:** a DIN 7985 M2.5 head is 5.0 mm wide, the printed recess 5.2 mm. Whether the
    head enters without clearing the recess has not been tried on a print.
12. **Quantity limits:** DigiKey states a purchase limit for the compute module. Whether Reichelt.at or Semaf limit
    the quantity per customer was not checked (relevant for two devices).
13. **VAT rate at BerryBase.at:** the pages say "Preise inkl. MwSt." without naming the rate.
14. **Lines marked N** in sections 5 and 6 are from the research notes of the same day and were not read again for
    this document.
