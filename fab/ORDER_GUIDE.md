# VoxHub CM4 carrier, revision A3 - ordering at JLCPCB, click by click

Applies to hardware revision A3 and to the files in `fab/jlcpcb/` of the same commit as this guide. The board in these files carries the text "VoxHub CM4  rev A3" on its top side. Files whose board says "rev A2" belong to the older guide; do not mix the two. Earlier files of revision A3 carry the same text; they are told apart by the first lines of the Gerber files (section 1).
Order: 5 PCBs, 2 of them fully assembled on both sides, delivery to Austria. The order is planned so that you do not solder anything; the one case in which solder may have to be added by hand after delivery is named in section 1 (paragraph "Solder paste").

Read the whole guide once before you start. Then work through sections 2 to 7 in order.

**What is new against the guide for revision A2**

- The parts list has 44 rows instead of 53 and 42 machine-placed part types instead of 51. That alone is 13.77 USD less in fees (section 8.2).
- Three parts were replaced after the stock check of 2026-11-20: the double USB-A socket J6, the two microphones and the USB hub chip U4 (the same chip on tape and reel). The parts of revision A2 are now their alternates (section 2.4).
- Two parts are thin instead of three; only these two are reserved in advance (section 2.3).
- JLCPCB has a footprint for every part now. All 136 rows of the placement report say `ok` (section 5.4). For the new USB-A socket J6 that confirms position, rotation and pin 1, not the fit of the real part (explained there).
- The order form is filled in as before. The via covering stays "Epoxy Filled & Capped"; the form preselects "Plugged", so you have to change it. New traps of the form are in sections 3.3 and 4.3.
- New step at checkout: compare DHL Express (DDP) with FedEx Express (DDP) (section 7.1).
- Expected total: 422.00 USD (383.98 EUR), with the part prices of 2026-11-21 and JLCPCB's form prices of 2026-11-20 (which figure is of which day: top of section 8). The old and the new estimate side by side: section 8.2.

**Where the facts come from**

| Mark in this guide | Meaning |
|---|---|
| live | read without login from JLCPCB's order form https://cart.jlcpcb.com/quote, from JLCPCB's shipping calculator https://jlcpcb.com/shipping or from JLCPCB's parts database. The order form was read on 2026-11-12 and again on 2026-11-20 between 22:48 and 23:31 UTC: the prices of the chosen configuration (3.5, 4.3, 8) are unchanged to the cent. A statement that was seen on 2026-11-12 only says so. Stock and prices of every part of the parts list: 2026-11-21 (`hardware/gen/sourcing_jlc.json`, field `checked`, which holds the date only). The time this guide gives for that read, 09:57 UTC, is the time at which the read ended and the file was written; it is not in the file. The parts list was read twice. The first read began on 2026-11-20 and ended on 2026-11-21 at 00:07 UTC; the documents of this repository call it the read of 2026-11-20. The second is the read of 2026-11-21, 09:57 UTC. Between the two JLCPCB's USD prices rose by about 0.24 %: of the 48 parts in the file (the 44 of the parts list and 4 others), each of the 24 that cost 0.10 USD or more rose by 0.19 to 0.29 %; of the 24 cheaper ones, whose prices have four decimals, 14 are unchanged, 9 rose and one (MM3Z10VT1G) fell. Every stock figure and part price of the parts list that this guide gives without another date is from the second read. The prices were not read again when the files to upload were generated again in the afternoon of 2026-11-21 (section 1). Stock and prices of the other parts named in section 2.4: 2026-11-20 between 22:23 and 22:46 UTC, unless a row says 2026-11-21. Shipping prices: 2026-11-20 and 2026-11-21 (00:30 to 01:00 UTC) |
| help | JLCPCB help-centre article. Of the articles about the pages behind the login, five were fetched again on 2026-11-20 at 22:49 UTC. They are the revision that was read on 2026-11-12 ("Last updated on Sep 09, 2026") and still contain what this guide takes from them: "How do I place a PCBA order?" (the steps of sections 5.1 to 5.5 and 7.1), "Component Matching Guidelines for PCBA Orders" (5.3), "PCB Assembly FAQs (Part 2)" (5.4), "Terms and Conditions of JLCPCB Assembly Service" (7.3) and "SMT Service Lead Time Overview" (2.4, 5.5, 9). Not fetched again, so as fetched on 2026-11-12: the articles about the parts pre-order, about using your own parts and about Global Sourcing (2.3, 2.4), the article about Review Before Payment (7.1, 7.2), and what this guide says about the error messages of the upload (5.2), the yellow mark (5.3), **Edit Order** (5.4) and the shortage preference (5.5), which is in none of the five. The labels of the shortage preference were found again on 2026-11-21, not in an article but in the public script of JLCPCB's order site (5.5). The articles about via covering, shipping, customs and VAT were fetched on 2026-11-20 and 2026-11-21. Everything after the button **NEXT** needs a login and was documented from these articles only |
| list | JLCPCB's assembly price list "PCB Assembly Cost: What Does the Price Include?", last updated 22 Oct 2026. Fetched again on 2026-11-20: the same revision, every amount unchanged |
| estimate | arithmetic from the above; the real figure appears on JLCPCB's pages before you pay |

The two reads of the order form did not see the same things. On 2026-11-12 a neutral test file of this board's size, layer count and hole sizes was uploaded. On 2026-11-20 nothing was uploaded and the size was typed in. What the form does after an upload (the line "Detected ...", the dialog **Layer Sequence**, the change of the size to 100 * 84 when PCB Assembly is switched on) is therefore as seen on 2026-11-12. The block **PCB Assembly** opens only after an upload; on 2026-11-20 its options and fee texts were read on JLCPCB's own demo board (80 x 70 mm).

Text in **bold** is a label exactly as it appears on the screen. Prices are in USD as JLCPCB shows them.
EUR values use the ECB reference rate of 2026-11-20: 1 EUR = 1.0990 USD, 1 USD = 0.9099 EUR (the guide for revision A2 used the rate of 2026-11-11: 1.1127 and 0.8987).

Directions on the board, used in the whole guide (the same as in `fab/ASSEMBLY_AND_TEST.md`): hold the board with the parts up
and the edge with the three connectors (USB-C, double USB-A, microSD) away from you. That edge is the **rear edge**, the opposite
edge is the **front edge**, left and right are as you see them. Positions are given as x / y in millimetres: x from the left
edge, y from the rear edge (the board is 100 x 74 mm). In the tables of section 5.4 the position of a part is the placement
point of the CPL file; for a few parts that is not the middle of the part (explained there).
JLCPCB calls the side with almost all parts **Top** and the other side **Bottom**; this guide uses the same words.

---

## 1. What is in `fab/jlcpcb`

| File | Content | Where it goes |
|---|---|---|
| `gerbers.zip` | 13 files: 4 copper layers (`voxhub-F_Cu.gtl`, `voxhub-In1_Cu.g1`, `voxhub-In2_Cu.g2`, `voxhub-B_Cu.gbl`), 2 solder mask, 2 solder paste, 2 silkscreen, the outline (`voxhub-Edge_Cuts.gm1`), 2 drill files (`voxhub-PTH.drl`, `voxhub-NPTH.drl`) | **Add gerber file** on the order form (section 3) |
| `bom_jlcpcb.csv` | parts list: 44 rows, one row per JLCPCB part number, 136 parts per board. Columns `Comment, Designator, Footprint, LCSC Part #`; `Comment` is JLCPCB's own name of the part | BOM upload (section 5) |
| `cpl_jlcpcb.csv` | position and rotation of the same 136 parts: 132 on the top side, 4 on the bottom side. Columns `Designator, Mid X, Mid Y, Layer, Rotation` | CPL upload (section 5) |
| `placement_report.csv` | one row per part: the rotation that was written into the CPL, how it was matched to JLCPCB's own footprint and how well that footprint fits the pads of the board | not uploaded - it is your check list for the placement preview (section 5.4) |

Nothing needs editing. Upload the three files exactly as they are.
The counts and positions in this guide belong to the files generated on 2026-11-21 between 15:23 and 15:26 UTC with KiCad 10.0.8. Each of the 11 Gerber files and the two drill files in `gerbers.zip` names its creation time in its first lines: 15:23:38 or 15:23:39 UTC. The archive was packed at 15:25:26 UTC and the three CSV files were written at 15:25:44 UTC; these two are file times of the tree in which the build ran and are not inside the files. The three CSV files did not change in this build: they are byte for byte those of the A3 files generated in the morning of the same day.
Since this build each of the 11 Gerber files also names the revision: its third line, `TF.ProjectId`, ends with `,A3*` (the creation time is in the second line). To look at it, open a Gerber file from a copy of the archive in a text editor. The two drill files have no such field. (The two drill maps and the job file in `hardware/outputs/gerbers`, which are not uploaded, name revision A3 as well.) Every earlier `gerbers.zip` in the history of this repository, those of revision A3 included, says `rev?` in that line and has an earlier time. Do not upload one of those: in the earlier A3 archives part of the solder paste of the four spacers lies on solder mask (paragraph "Solder paste" below).
If the files in `fab/jlcpcb/` are newer than that, a count in sections 1, 5 or 8 may differ by a few; the procedure stays the same.

- Do not open the CSV files in a spreadsheet program and save them again. If you want to look at them, open a copy.
- Do not rename the files inside `gerbers.zip` and do not re-pack the archive.

Facts about the board that the form will ask for or show. The tracks, vias and holes of revision A3 are those of revision A2. The copper differs in two ways. In three land patterns ten pads became smaller (row "Copper to holes without plating" below). And the filled ground areas differ very slightly: at six places of the top layer the edge of the fill lies up to 0.03 mm elsewhere, and slivers of copper at about 260 places, none wider than 0.005 mm and 0.025 mm2 together (0.021 mm2 of it on the top layer), are gone on the four layers. No gap and no connection changed. In the solder paste of the top side three things differ: the apertures of the four outer USB-C contacts became shorter with their pads, the 200 apertures of the two CM4 sockets J2 and J3 kept their size of 0.17 x 0.67 mm and got a smaller corner radius (0.035 instead of 0.0425 mm), and the apertures of the four spacers and the two microphones were made smaller (paragraph "Solder paste" below). The solder mask differs only at the three land patterns, the silkscreen only in the revision text; outline and drill files are the same. All of this is measured, by comparing the Gerber files of the two revisions; the small differences in the fill and at the CM4 sockets look like an effect of the change from KiCad 9 to KiCad 10, which was not proved (`DECISIONS.md`, K-6, K-7, R-2 and R-21).
The holes were counted, the distance of the copper to the edge was measured on all four layers, and so was the distance of the copper to each of the 15 holes without plating, the last time on 2026-11-21 in the Gerber and drill files of this `gerbers.zip`.

| Property | Value |
|---|---|
| Size | 100 x 74 mm, corners rounded |
| Layers | 4 |
| Small holes | 294 holes of 0.30 mm: 286 vias (pads 0.5 mm and 0.6 mm) and 8 thermal holes in one exposed pad. Five of the vias lie inside the exposed pads of U1, U4 and U10; no other via lies in or touches a pad (`hardware/outputs/via_in_pad.txt`) |
| Other holes | plated: 4 slots 0.6 mm wide, 2 x 0.75 mm, 8 x 0.92 mm, 3 x 1.0 mm, 4 x 2.3 mm; not plated: 2 x 0.65 mm, 2 x 0.8 mm (microphone sound ports), 3 x 0.99 mm, 4 x 2.7 mm, 4 x 3.7 mm |
| Copper to the board edge | 0.45 mm on all four layers, along the straight edges and around the four rounded corners (JLCPCB asks for 0.4 mm at an edge where a rail is scored off). Closer only at two shield pads of the microSD socket on the rear edge of the top layer (0.375 mm) |
| Copper to holes without plating | 0.2 mm or more at all 15 holes, on all four layers (smallest value measured in the Gerber files: 0.2003 mm). JLCPCB clears 0.2 mm of copper around a hole without plating, so it has no reason to cut copper back at any of them. Revision A3 corrected three land patterns for this rule. The ring-shaped ground pad of each microphone now reaches from 0.61 to 1.04 mm from the centre of its 0.8 mm sound hole; the hole edge is at 0.40 mm, so the ring starts 0.21 mm from the hole. Infineon's land pattern for the microphone, which revision A2 used as it is, draws this ring from 0.58 mm; its inner edge was moved out by 0.03 mm, and the ring is 0.43 mm wide instead of 0.46. The six solder paste apertures on this ring now start at 0.63 mm from the centre (0.60 mm before) and so lie inside it. The other two are the ring pads of the four spacers H5 to H8 (now 0.25 mm from their 3.7 mm hole) and the four outer contacts of the USB-C socket (now 0.21 mm from its two 0.65 mm holes). If JLCPCB asks about copper near one of these holes all the same, the answer is in section 7.3 |
| Silkscreen | polarity marks and a few texts only; every line is 0.15 mm or wider, text is 1.0 mm high or more (the smallest mark is the dot next to U9, a filled circle of 0.29 mm). There are **no reference designators** (R1, U4 ...) printed on the board; they exist only in the CPL file |

**Solder paste.** The solder paste layer has no aperture outside a solder mask opening on either side of the board. That is measured in the Gerber files of this `gerbers.zip`, with two Gerber readers: 0.000 mm2 of paste lie outside the mask openings on the top side and 0.000 mm2 on the bottom side. In the archives generated before, from 2026-11-20, 23:48 UTC, to 2026-11-21, 09:57 UTC, it was 7.94 to 7.98 mm2 on the top side (measured in the same way). Revision A3 had made the ring pads of the four spacers H5 to H8 and of the two microphones narrower and had left their paste as it was in revision A2, so 1.98 mm2 of paste per spacer and, in the last two of those archives, 0.02 mm2 per microphone lay on solder mask. A review of the order package found it; no check of the build compares paste with mask openings. Against the archive of 09:57 UTC six parts changed, H5 to H8, MK1 and MK2: 28 of the 664 apertures of the top paste layer became smaller. Nothing else changed geometrically in any of the 13 files. The paste of a spacer now reaches from 2.15 to 2.92 mm from the centre of its hole (before: from 1.90 mm), on a ring pad from 2.10 to 3.00 mm. The paste on the ring of a microphone reaches from 0.63 to 1.00 mm from the centre of its sound hole (before: from 0.60 mm), on a ring from 0.61 to 1.04 mm.

Each spacer gets less paste than its maker suggests. The data sheet of the spacer (Wurth 9774015151R, revision 001.002) suggests a stencil of four segments from 3.8 to 5.9 mm diameter and says "Solder Cream Thickness 150 um min.": 13.26 mm2 x 0.15 mm = 1.99 mm3 of paste per spacer. The board has 10.22 mm2, which is 1.02 mm3 with a stencil 0.10 mm thick (51 %) and 1.23 mm3 with one of 0.12 mm (62 %). Revision A2 had 12.75 mm2: 64 % and 77 %. Per area of the ring pad the paste is 2.6 % less than in revision A2. All of these figures are calculated: the areas from the dimensions in the data sheet and from the land pattern of the board, the volumes from the areas. The two stencil thicknesses are assumptions: what JLCPCB uses was not looked up, and neither was whether JLCPCB cuts its stencil from this paste layer or from its own footprint library. No board was soldered. The paste was left as it is: the ring had to move away from the hole, the paste follows the ring, and its outer edge is where it was in revision A2 (`DECISIONS.md`, R-19 and R-28).

What you do about it: nothing at the order. No option of the order form and neither of the two remarks changes; **Special stencil** stays **No** and **Solder Paste** stays **High temp.** (4.2), and if JLCPCB itself proposes a step stencil you accept it as before (7.3). When the boards have arrived, look at the solder joint of each of the four spacers (section 10.3). Where the fillet of solder around the foot of a spacer is missing, solder is added there by hand with a soldering iron (`fab/ASSEMBLY_AND_TEST.md`, test 1, describes the check and the repair). This is the only place in this guide where soldering may become necessary.

---

## 2. Before ordering: account and the parts that are short

### 2.1 Account

1. Open https://jlcpcb.com and click **Sign In** (top right). You can register a JLCPCB account or sign in with Google or Apple (the login page offers these three ways).
2. When you enter your address later, enter it as a private person: your name, no company name. JLCPCB decides from the name and the address whether the parcel is a private (B2C) or a business (B2B) import (help).

### 2.2 The thin parts today

Rule of this project: a BOM line with fewer than 200 pieces in JLCPCB's assembly stock is "thin".
`hardware/outputs/bom_summary.json` and `order_cost.json` list two such lines.

| Part | Designator | JLCPCB Part # | JLCPCB stock (live 2026-11-21, 09:57 UTC) | Needed for 2 boards | Unit price (live) |
|---|---|---|---|---|---|
| ADAU7002ACBZ-R7 (microphone interface IC) | U9 | C481886 | 63 (104 on 2026-11-12) | 2 | 2.4754 USD (3.9059 on 2026-11-12) |
| RF-BM-2652P2 (Zigbee radio module) | U11 | C5440064 | 126 (126 on 2026-11-12) | 2 | 8.6843 USD (6.6325 on 2026-11-12) |

Every other line has more than 200 pieces, and no line has less than twice the pieces needed. The next thinnest ones, for information (`hardware/outputs/order_cost.csv`):
IM72D128V01XTMA1 microphones (C5119248) 613, need 4; CYPD3177-24LQXQT (C2952489) 729; SMBJ22A (C224015) 1,834; LMR33640ADDAR (C2836966) 2,073;
9774015151R spacers (C5353804) 2,071, need 8 (230 on 2026-11-12); 907-112A1022D10200 USB-A socket (C29780026) 2,434.

Stock moves, and it can move fast. Between 2026-11-12 and 2026-11-20 three lines of revision A2 fell to almost nothing: USB2514B-I/M2 from 1,182 to 2 pieces, the Wurth USB-A socket from 116 to 18, the IM69D130V01 microphones from 392 to 43 (392 is the figure in the stock file of 2026-11-12; the guide for revision A2 showed 372, read at 10:08 UTC of that day). That is why revision A3 uses other parts for them.
On the day you order, look again at the two thin parts and at the six lines named above. If one of the six has fallen below 200 pieces, reserve it together with the two thin parts (section 2.3). The quantity is the column `Billed quantity` of `hardware/outputs/order_cost.csv` plus one: IM72D128V01XTMA1 **5**, CYPD3177-24LQXQT **3**, SMBJ22A **6**, LMR33640ADDAR **3**, 9774015151R **9**, 907-112A1022D10200 **3**.
For five of the six that is twice the pieces per board plus one. SMBJ22A is the exception: one piece per board, but JLCPCB adds 2 pieces for losses and has a minimum of 5, so its row asks for 5 (the larger of 2 + 2 and 5) and you reserve 6. Whether JLCPCB also counts the loss pieces when a part comes out of **My Parts Lib** is not in the help articles that were read; 6 pieces are enough either way.

To see the stock of a part right now, open `https://jlcpcb.com/partdetail/C481886` (replace the C number).

### 2.3 Reserve the two thin parts first

JLCPCB lets you buy parts into a private stock that only your own assembly orders can use. Do this before anything else; it takes a few minutes.
(Source: help article "What is JLCPCB Parts Pre-order Service?", updated 9 Sep 2026. The pages themselves need a login and were not seen.)

1. Sign in. Open **Parts Manager**. It has three functions: **My Parts Lib**, **Order Parts**, **New parts request**.
2. Click **Order Parts**. Search for `C481886`. Enter quantity **3**. Add it to the cart.
3. Do the same for `C5440064` (quantity **3**). Two pieces of each are needed, the third is a spare.
   The help article says: "In-stock extended parts can be pre-ordered, no minimum quantity required."
4. Pay within one hour. The article says the parts order stays in the cart for 1 hour and is cancelled after that.
5. Open **Parts Order History** and then **My Parts Lib**. For parts that were in stock the article says they are "shown in your own library immediately after you make the payment". Continue only when both parts are listed with quantity 3.

What it costs: 3 x (2.4754 + 8.6843) = 33.48 USD (estimate at the library prices of 2026-11-21; the price shown on the **Order Parts** page and whether tax is added there could not be verified). The guide for revision A2 had three parts here and 39.89 USD.
The parts stay at JLCPCB. They are never shipped to you ("the parts you store in JLCPCB can only be used for assembly orders").
When you place the board order, JLCPCB takes these parts automatically: "If there are enough pieces in 'My Parts' for the assembly order, the system will use 'My Parts' by default." (help article "How to use my own parts for PCB assembly order", fetched 2026-11-12).

### 2.4 If a part is gone

"Gone" means: stock 0, or less than the pieces needed (2; for the microphones 4). Do not place the board order with a missing part - an owner who does not solder cannot add it later.
The first two rows have no substitute. The other three rows are the lines that were replaced for revision A3; each has an alternate that fits the board as it is. The alternates and what they need are also in `hardware/outputs/bom.csv`, column "Other second sources".

| Part gone | Alternate, JLCPCB Part #, stock on the day it was read | What differs | What you do |
|---|---|---|---|
| ADAU7002ACBZ-R7 (U9) | none. ADAU7002ACBZ-RL (13 inch reel, C654434) is the same part: 0 in stock on 2026-11-20. The only other PDM converters in JLCPCB's library (ADAU7118, ADAU7112) have other packages. Second source in the BOM: DigiKey 505-ADAU7002ACBZ-R7CT-ND (7,888 in stock on 2026-11-11, 2.66 USD) | - | There is no substitute. Use JLCPCB's Global Sourcing service (help article "How to use JLCPCB Global Sourcing Parts Service?", fetched 2026-11-12) to let JLCPCB buy ADAU7002ACBZ-R7 from a distributor: review 1 to 3 business days, then "9-15 days" on one help page and "normally 9-20 business days" on another; it cannot be cancelled. Place the board order only when the part is listed in **My Parts Lib** |
| RF-BM-2652P2 (U11) | none that can be ordered as it is. RF-star RF-BM-2652P4 (C5441193, same outline, other firmware build): 0 in stock on 2026-11-20, and LCSC marks it as discontinued. RF-star RF-BM-2652P2I (C5440077): 165 in stock on 2026-11-20, 6.8339 USD. Ebyte E72-2G4M20S1E needs another footprint. Not carried by DigiKey | RF-BM-2652P2I: same pads, but a socket for an external antenna instead of the printed antenna | Do not order the boards. Report it to the maintainer of this repository; the possible ways (JLCPCB **Pre-order** of C5440064 with a minimum quantity, the 2652P2I module with an external antenna, or the P4 module with a different firmware file) need a decision |
| 907-112A1022D10200 (J6) | **1.** Wurth **61400826021**, C5366339, the part of revision A2: 18 in stock on 2026-11-21 (116 on 2026-11-12), 2.7601 USD. **2.** Korean Hroparts **U-A-28DD-Y-1**, C530601: 168 in stock on 2026-11-20, 0.3529 USD, minimum 2 | Wurth: the footprint of the board was drawn for this part; its shell is 0.26 mm lower; rated -40 to +105 C. JLCPCB has no footprint drawing for it: the placement preview may show a box, a wrong position or nothing, and JLCPCB first has to create a footprint (help: "typically completed within 48 hours"). Hroparts: its front pin row is 0.09 mm off the holes of the board; rated -55 to +85 C; its drawing is not fully dimensioned. Measured from that drawing, its shell posts (2.26 mm at the root) may not go fully into a hole drilled at JLCPCB's lower limit of 2.22 mm - the part could sit up to 0.17 mm high - and its mouth can stand up to 0.3 mm proud of the enclosure wall | Take the Wurth part if it has 2 or more, otherwise the Hroparts part. Both are thin: reserve 3 pieces first as in 2.3, or the 2 that are left (Wurth: 3 x 2.7601 = 8.28 USD). Then on the parts list page (section 5.3) click the magnifier icon in the row of J6, search the C number, select it. Add to the assembly remark: "J6: C5366339 is used instead of C29780026 (same footprint)." - or C530601. With the Hroparts part tell the maintainer before the boards arrive: the USB-A opening of the enclosure has to be checked against the real part |
| IM72D128V01XTMA1 (MK1, MK2) | **1.** Infineon **IM73D122V01XTMA1**, C5563886: 875 in stock on 2026-11-20, 2.6800 USD. **2.** Infineon **IM69D130V01**, C536262, the part of revision A2: 43 in stock on 2026-11-21 (392 on 2026-11-12), 3.1249 USD | Both: same package, pads, pin-out and JLCPCB footprint as the fitted part; the CPL stays as it is. IM73D122: 10 dB more sensitive (-26 instead of -36 dBFS), overload point 122 instead of 128 dBSPL. IM69D130V01: same sensitivity as the fitted part; Infineon lists it as "not for new design" | Take the IM73D122, which has enough stock - unless 5 pieces of the IM69D130V01 can still be reserved; with that part nothing but the remark changes. IM73D122: the microphone gain of the software has to be lowered. 10 dB is a factor of 3.16: divide every gain value the documents name by it. There are two defaults. In the two-device system the default 4 becomes about 1.3 (4 / 3.16): on the hub it is the option **Microphone gain** of the VoxHub Satellite add-on, on the satellite `VOXHUB_MIC_GAIN` in `/etc/voxhub/satellite.env`. In the VoxHub Assistant add-on the default 32 of its option **Microphone gain** becomes about 10 (32 / 3.16). Both new values are arithmetic and were not tried. The gain advice and the playback volumes of the microphone tests in `fab/ASSEMBLY_AND_TEST.md` are written for the fitted part: tell the maintainer before the boards arrive. IM69D130V01: nothing changes in the software, but the part is thin - reserve 5 pieces first as in 2.3 (4 and a spare, 5 x 3.1249 = 15.62 USD) and use it only if you get them. In both cases: magnifier icon in the row of MK1, MK2 on the parts list page, search the C number, select it; in item 1 of the assembly remark (section 6.2) replace "C5119248, IM72D128V01XTMA1" by the number and name of the part you took |
| USB2514BT-I/M2 (U4) | Microchip **USB2514B-I/M2**, C220679, the part of revision A2: 2 in stock on 2026-11-20 (1,182 on 2026-11-12), 2.4042 USD | nothing: it is the same device in a tray instead of on tape and reel. The letter "T" of the order code is not printed on the chip (Microchip data sheet) | Use C220679 if it has 2 or more: magnifier icon in the row of U4, search `C220679`, select it. Add to the assembly remark: "U4: C220679 is used instead of C510949 (same device)." If both are gone: do not order the boards; report it to the maintainer |

---

## 3. The PCB form, option by option

Page: https://cart.jlcpcb.com/quote, tab **Standard PCB/PCBA**. You can fill in this page without being logged in.

Do these two things first, in this order:

1. Set the country. In the right column find **Shipping Estimate**, click the shipping method name, choose **Austria** in the country list (default: "United States Of America"), close the dialog. Do this first: when the country was changed later in a test on 2026-11-12, the page reset **Surface Finish** to "HASL(with lead)".
   The method named in this box is only an estimate. After every change of an option it falls back to plain "DHL Express" (live). Leave it; the shipping method is chosen at checkout (section 7.1).
2. Click **Add gerber file** and choose `fab/jlcpcb/gerbers.zip`. Wait until the box shows the two board pictures and a line like "Detected 4 layer board of 74x100mm(2.913x3.937 inches)." (this is what the form showed for a test file of the same size on 2026-11-12). **Layers** and **Dimensions** are then filled in.

Then go down the page. The tables follow the page order.

### 3.1 Top block

| Option | Select | Why |
|---|---|---|
| **Base Material** | **FR-4** | standard glass-epoxy board |
| **Layers** | **4** | filled in by the upload; check it |
| **Dimensions** | **100 * 74** mm | filled in by the upload and read-only. It changes to 100 * 84 when you switch on PCB Assembly (section 4) - that is correct |
| **PCB Qty** | **5** | smallest quantity; 2 are assembled, 3 stay without parts |
| **Product Type** | **Industrial/Consumer electronics** | the other choices are Aerospace and Medical |

### 3.2 PCB Specifications

| Option | Select | Why |
|---|---|---|
| **Different Design** | **1** | one board design in the file |
| **Delivery Format** | **Single PCB** | JLCPCB adds the assembly rails itself (section 4) |
| **PCB Thickness** | **1.6mm** | the enclosure and the connectors are designed for 1.6 mm |
| **PCB Color** | **Green** | no surcharge. Black and white need wider solder-mask bars (0.13 mm instead of 0.10 mm) than fit between the 0.4 mm pitch pads |
| **Silkscreen** | **White** | only choice |
| **Material Type** | **FR4 TG135** | 0 USD. The row has six choices now (live): besides "FR4 TG135" and "FR4 TG155" four named laminates (Nan Ya NP-140F, KB6164 - TG135, Nan Ya NP-155F, KB-6165 - TG155); leave them. If "FR4 TG155" is selected here, you clicked a smaller via size by mistake (see 3.3) |
| **Surface Finish** | **ENIG** | flat gold pads; required for the 0.22 mm pads of U9 and for the 0.4 mm pitch connectors. The row has four choices now (live): "OSP" (with a badge "New"), "HASL(with lead)", "LeadFree HASL", "ENIG". For a 4-layer board "HASL(with lead)" is preselected, on the empty start form "OSP" - change it |
| **Gold Thickness** (appears with ENIG) | **1 U"** | the standard thickness; 2 U" costs more and is not needed |

### 3.3 High-spec Options

| Option | Select | Why |
|---|---|---|
| **Outer Copper Weight** | **1 oz** | as designed |
| **Inner Copper Weight** | **0.5 oz** | as designed; the stack-up JLC04161H-3313 is the one for 0.5 oz inner copper |
| **Specify Layer Sequence** | **Yes**. A dialog **Layer Sequence** opens with four lists. Choose **L1(Top layer)** = `voxhub-F_Cu.gtl`, **L2(Inner layer1)** = `voxhub-In1_Cu.g1`, **L3(Inner layer2)** = `voxhub-In2_Cu.g2`, **L4(Bottom layer)** = `voxhub-B_Cu.gbl`, then **Confirm** | In1 is the ground plane directly under the USB tracks of the top layer; this removes any doubt about the order. Seen on 2026-11-12 (the row exists only after an upload): the lists show the file names of the uploaded archive; until you confirm, the row shows "This option is required." in red |
| **Specify Stackup** | **Yes**. A dialog **Layer Stackup** opens. Choose **JLC04161H-3313**, then **Confirm** | the board was designed for this layer structure (0.0994 mm prepreg between top layer and ground plane). 0.00 USD (live). The dialog notes "This is a special stackup, and it doesn't support economic PCB assembly" - correct, this order is Standard assembly |
| **Impedance Control** (appears after the stack-up is chosen) | **No requirement** | Naming the stack-up already makes JLCPCB build the exact layer structure of its own impedance calculator, in which the board's USB 2.0 lines are 89.96 ohm (the pair from the hub to the CM4: 0.14 mm tracks, 0.16 mm gap, 32 mm long) and 90.42 ohm (the two runs to the USB-A ports: 0.185 mm tracks of 45.21 ohm each, 11 and 16 mm long); USB 2.0 accepts 76.5 to 103.5 ohm. The paid choice "±10% (±5Ω if value≤50Ω)" (+33.08 USD on 2026-11-12, not read again; it forces **Confirm Production file**) would add a guaranteed and tested impedance: JLCPCB's engineers adjust the track widths and need a table of the impedance tracks inside the Gerber archive - it does not give a different board |
| **Via Covering** | **Epoxy Filled & Capped**. You have to click it: for a 4-layer board the form preselects **Plugged** (live), and **Tented** is greyed out (hover text: "The Via Tented option is upgraded to Via Plugged for free.") | The board has 5 vias and 8 thermal holes inside the exposed pads of U1, U2, U4 and U10 (no other via touches a pad). The free choice "Plugged" never closes a hole that sits in a pad (help, article updated 10 Nov 2026: "holes in pad, and vias with a distance less than 0.35mm from the pad cannot be plugged with ink"), so these 13 holes would stay open and could draw solder away from the part - and nobody can rework these prototypes. Moving the vias out of the pads, so that "Plugged" would be safe, was worked out for revision A3 and rejected: a hotter regulator and amplifier and solder mask strips under two chips, to save 20.96 USD (`DECISIONS.md`, C-11). +17.46 USD on the form at this step (live, size 100 * 74); 17.58 once PCB Assembly is on and the size is 100 * 84, 17.55 for the 110 x 74 mm panel. Never click **Copper paste Filled & Capped**, not even to look: it costs 337.56 USD (live, at the 110 x 74 mm size) and upsets the row **Confirm Production file** below |
| **Via Plating Method** | nothing to click. The page sets **Horizontal Electroless Copper Plating** by itself when "Epoxy Filled & Capped" is chosen and greys out the other two ("Not Specified", "Conductive Adhesive") | +3.40 USD at this step, 3.41 once PCB Assembly is on (live); it belongs to the filled vias. Form trap (live): this row stays switched on when another via covering is clicked afterwards. For this order it has to be on, so there is nothing to undo; the price box must show its line (3.5) |
| **Min via hole size/diameter** | **0.3mm/(0.4/0.45mm)** | all 294 small holes are 0.30 mm; this is the tier without surcharge, and 0.30 mm is also the largest hole in a pad that gets filled (help text of **Via Covering**: "only untented vias ≤ 0.3mm will be filled with epoxy resin"). Do not click the smaller sizes even for a test: they switch on "FR4 TG155" (+3.49 USD) and "4-Wire Kelvin Test" (+17.03 USD), and both stay on when you go back (seen on 2026-11-12) |
| **Board Outline Tolerance** | **±0.2mm(Regular)** | default; "±0.1mm(Precision)" is greyed out as soon as PCB Assembly is on |
| **Confirm Production file** | **Yes**. A dialog opens ("please confirm within 48 hours ... Otherwise, your order will be automatically confirmed"). Tick **Do not confirm automatically**, then **Confirm** | +1.05 USD. You see JLCPCB's production data before the boards are made, and production waits for you (section 7). Form trap (live): if "Copper paste Filled & Capped" was clicked at any time, this row was locked on Yes and falls back to **No** without a notice as soon as another via covering is chosen. Set this row after **Via Covering**, and check it once more at the end (4.3) |
| **Mark on PCB** | **Remove Mark** | no order number is printed on the board; 0 USD; it is the default |
| **Electrical Test** | **Flying Probe Fully Test** | only choice, included |
| **Gold Fingers** | **No** | the board has none |
| **Castellated Holes** | **No** | the radio module has castellated pads, the board itself has none |
| **Press-Fit Hole** | **No** | none |
| **Edge Plating** | **No** | none |
| **Blind Slots** | **No** | the 4 slots of the USB-C connector go through the board |
| **UL Marking** | **No** | not needed |
| **Backdrill** | **No** | not needed |
| **Humidity Indicator Card** | **No** | not needed (greyed out with PCB Assembly) |

### 3.4 Advanced Options (click the grey bar to open it) and PCB Remark

| Option | Select | Why |
|---|---|---|
| **4-Wire Kelvin Test** | **No** | if it shows "Yes" you clicked a smaller via size before; set it back to No |
| **Paper between PCBs** | **No** | not needed |
| **Appearance Quality** | **IPC Class 2 Standard** | standard |
| **Silkscreen Technology** | **Ink-jet Printing Silkscreen** | default; the smallest silkscreen line of the board is 0.15 mm, text 1.0 mm |
| **Package Box** | **With JLCPCB logo** | default |
| **Inspection Report** | **No** | not needed |
| **PCB Remark** (pencil icon) | paste the PCB remark from section 6.1 | tells the engineers which holes to fill and which two holes must stay open |

### 3.5 Check the price box before you go on

Right column, **Charge Details**. With the options above and PCB Assembly still off, the live form showed on 2026-11-12 and again on 2026-11-20 (23:06 UTC):

| Line | Amount |
|---|---|
| Special Offer | $8.00 |
| Via Covering | $17.46 |
| Surface Finish | $17.40 |
| Via Plating Method | $3.40 |
| Confirm Production file | $1.05 |
| **Calculated Price** | **$47.31** |

What a wrong box tells you:

| You see | What is wrong |
|---|---|
| **Calculated Price** $26.45; the line **Via Covering** says $0.00 or is missing, and there is no line **Via Plating Method** | **Via Covering** is still on the preselected "Plugged" (live: 26.45 USD). Go back to 3.3 |
| the line **Via Covering** says $0.00, but the line **Via Plating Method** $3.40 is still there; **Calculated Price** about $29.85 (26.45 + 3.40) | "Epoxy Filled & Capped" was clicked once and "Plugged" after it: the via covering is the free one again, but the plating row stayed switched on (form trap of 3.3). Seen live at the 110 x 74 mm size only ($52.06 instead of $48.65, with "Via Plating Method $3.41"); the amount for 100 x 74 mm is arithmetic, not read. Go back to 3.3 and click **Epoxy Filled & Capped** again |
| the line **Confirm Production file** is missing ($46.26 = 47.31 - 1.05) | **Confirm Production file** is on "No". Go back to 3.3 |
| other lines (**Material Type**, **4-Wire Kelvin Test**, **Min via hole size/diameter**, **Impedance Control**, **Stackup fee**) | an option is set wrongly - go back through 3.2 to 3.4 |

More than one row can apply at the same time, for example a **Via Covering** of $0.00 and no line **Confirm Production file**. Judge by the lines, not by the total alone.

The badges "Save $30.00 / Save $20.00" next to **Coupons** are not a discount on this order (section 7).

---

## 4. The PCB Assembly block, option by option

Below the PCB options is the block **PCB Assembly**. Switch it on with the toggle at the right of its header. (It only opens after a Gerber upload; without one it shows "Please upload Gerber files before proceeding to PCB Assembly".)

### 4.1 Main options

| Option | Select | Why |
|---|---|---|
| pictures **Assemble top side** / **Assemble bottom side** | both ticked | the board has parts on both sides (after choosing Both Sides below, both were ticked in the live form) |
| **PCBA Type** | **Standard** | "Economic" is greyed out: it cannot do two sides, the 0.4 mm pitch chip U9 or this stack-up |
| **Assembly Side** | **Both Sides** | 132 parts on top, 4 on the bottom (SW1, D7, D8, D9). The choices are "Top Side", "Bottom Side", "Both Sides"; "Top Side" is preselected |
| **PCBA Qty** | type **2** into the field next to the button "5" (hint: "Qty from 2 to 5") | 2 assembled boards; the other 3 are delivered without parts |
| **Edge Rails/Fiducials** | **Added by JLCPCB** (it is preselected). The form offers no choice of edges; the request for the edges is in the remarks (6.1 item 4 and 6.2 item 4) | Standard assembly needs 5 mm rails and fiducial marks; JLCPCB adds them. The page then says "The board size is modified to be 100mm*84mm due to adding two 5mm edge rails on the shorter sides." and **Dimensions** changes to 100 * 84 (seen on 2026-11-12): the form assumes rails on the two 100 mm edges. This board needs them on the two 74 mm edges (panel 110 x 74 mm): J6 overhangs the rear 100 mm edge by about 2.5 to 2.85 mm, the radio module U11 is flush with the front 100 mm edge and small parts sit 0.95 to 2.6 mm from it (pad copper to the edge, measured in the A3 board file: C23 0.95 mm, Q2 and Q3 1.16 mm, D10 1.33 mm, D7 to D9 1.58 mm, MK1 2.6 mm), so a rail scored off along these edges is a risk. JLCPCB's engineer changes the panel after reading the remark. Until then the form keeps showing 100 * 84 and the price for it (section 4.3) |
| **Confirm Parts Placement** | **Yes** ("No" is preselected). A dialog opens ("please confirm within 72 hours ... Otherwise, your order will be automatically confirmed"). Tick **Do not confirm automatically**, then **Confirm** | 0.45 USD (list). JLCPCB shows you its final placement drawing before it solders (section 7) |
| **Stencil Storage** | **No** | only useful for a repeat order within 3 months ("$4.96 one-time fee") |
| **Fixture Storage** | **No** | same |
| **Parts Selection** | **By Customer (Self-Service)** | the BOM already carries the JLCPCB part number of every line; "By JLCPCB (Manual Match)" costs $10 and takes 1 to 2 business days |

### 4.2 Advanced Options of the assembly block (twelve lists)

| Option | Select | Why |
|---|---|---|
| **Bake Components** | **No** | the parts come from JLCPCB's own dry storage |
| **Photo Confirmation** | **No** | "$7.5 per order"; the placement is already checked with **Confirm Parts Placement**. Runner-up: **Yes** - JLCPCB then shows photos of the assembled boards in the order history and waits for your answer before shipping |
| **Board Cleaning** | **Caution for Special Parts** ("No" is preselected) | MK1 and MK2 are bottom-port microphones with a sound hole through the board; washing would push liquid and flux into them (the silkscreen next to both says "MIC - NO WASH"). JLCPCB's own option text: "If your order contains sensitive components such as ... microphones ... we recommend that you select 'Caution for Special Parts' and clearly indicate the designators or part number in the remarks." Never choose "Dry-ice cleaning" or "Solvent-based Cleaning". The option text names a price for those two (about $0.16 and $0.25 per piece) and none for this choice |
| **Conformal Coating (cleaning included)** | **No** | includes a wash - forbidden for the microphones |
| **Packaging** | **Antistatic bubble film** | default; the cardboard choices add weight and shipping cost |
| **Special stencil** | **No** | JLCPCB's engineers decide themselves whether a step stencil is needed and write to you (section 7) |
| **Depanel boards & edge rail before delivery** | **Yes** ("No" is preselected) | JLCPCB removes the rails; otherwise the boards arrive with rails attached. "$1.4 service fee and $0.3 per panel", one more day |
| **Solder Paste** | **High temp.** | default, no charge. The other choice, "Medium temp.", costs $31.4 |
| **Flying Probe Test** | **No** | needs other file formats |
| **Nitrogen reflow soldering** | **No** | not needed |
| **Function test** | **No** | not possible without the CM4 and firmware |
| **Assembly remark** | **Yes**, and paste the assembly remark from section 6.2 | names the microphones, the polarity marks, the two edges for the rails and the two hand-soldered parts |

Below the lists: the box **I agree to the Terms and Conditions of JLCPCB assembly Service.** must be ticked (it is by default).
Leave the block **Stencil** ("Order together with PCB") below it switched off - the assembly stencil is part of the assembly fees and stays at JLCPCB.

### 4.3 Check the price box again, then NEXT

1. **PCB Build Time**: **3 days** with the tag "PCBA Only", $0.00, must be selected (the live form selected it by itself). Never choose "2-3 days" ($66.20).
2. **Charge Details** in the live form on 2026-11-12 and again on 2026-11-20 (23:10 UTC, size 100 x 84) with everything above:

   | Line | Amount |
   |---|---|
   | Special Offer | $8.00 |
   | Via Covering | $17.58 |
   | Surface Finish | $17.60 |
   | Via Plating Method | $3.41 |
   | Confirm Production file | $1.05 |
   | **Calculated Price** (Web Price) | **$47.64** |

   The lines under **Standard PCBA Price** (Components, Feeders Loading fee, SMT Assembly, Hand-soldering labor fee, Manual Assembly) show "-" at this point; they are filled in after the parts list. "Desktop Price: From $45.64" next to it is the price in JLCPCB's desktop program; ignore it.
   If the box shows $26.65, with **Via Covering** at $0.00 or missing and without the line **Via Plating Method**, the via covering is on "Plugged" (live); go back to 3.3.
   The same is true if **Via Covering** says $0.00 while the line **Via Plating Method** $3.41 is still there (about $30.06 = 26.65 + 3.41; arithmetic, this state was read at the 110 x 74 mm size only): "Plugged" was clicked after "Epoxy Filled & Capped", and the plating row stayed switched on (second row of the table in 3.5). Go back to 3.3.

   $47.64 is the price for rails on the 100 mm edges. For the panel that the remarks ask for (110 x 74 mm) the same form, with the same options and the size typed in by hand, showed $69.61 on 2026-11-12 and again on 2026-11-20 (23:14 UTC): Engineering fee $25.00, Board $5.10, Via Covering $17.55, Surface Finish $17.50, Via Plating Method $3.41, Confirm Production file $1.05. The size no longer falls under "Special Offer". You cannot select this on the form. Expect the difference of about 22 USD to appear when JLCPCB has reviewed the order (section 7.2).
3. Scroll up once more and check three rows, because the form can change them by itself (the cases are named at the start of section 3 and in 3.3): **Surface Finish** is still **ENIG**, **Via Covering** is still **Epoxy Filled & Capped**, **Confirm Production file** is still **Yes**.
4. Click **NEXT** (the button replaces "SAVE TO CART" when PCB Assembly is on). The login page appears; sign in.

---

## 5. BOM / CPL upload, parts list, placement preview

Everything in this section is behind the login. The labels are taken from JLCPCB's help articles, all updated 9 Sep 2026 and fetched on 2026-11-12; the pages themselves were not seen. Four of the articles (the order steps, the parts list, the marks of the placement preview, the expedite fee) were fetched again on 2026-11-20 and are unchanged; the error messages in 5.2, the yellow mark in 5.3, **Edit Order** in 5.4 and the shortage preference in 5.5 are in none of the four and are as read on 2026-11-12 (row "help" of the table at the top). If a button is named slightly differently, use the one with the same meaning.

### 5.1 Board views

1. JLCPCB shows the top and the bottom of the board. Top: the text "VoxHub CM4  rev A3". Bottom: the texts "VoxHub CM4 rev A3 - this side faces the top cover", "MUTE", "USB-C PD 9-20V" and twice "MIC - NO WASH". If you read "rev A2", you uploaded an old `gerbers.zip`: stop and start again at section 3 with the file of this commit.
2. Click **Next**.

### 5.2 Upload

1. BOM file: `fab/jlcpcb/bom_jlcpcb.csv`. CPL file: `fab/jlcpcb/cpl_jlcpcb.csv`.
2. Click **Process BOM&CPL**.
3. If the message "Inconsistent Reference Designators Between BOM and CPL" appears: do **not** click **Continue**. Both files contain the same 136 designators; the message means a wrong file was uploaded. Upload again.
4. If "Parameter Error", "The Uploaded File Format Is Incorrect" or "File Processing Failed" appears: try another browser or a private window (JLCPCB's own advice). Do not edit the files.

### 5.3 The parts list page ("Matched Parts")

The page lists the 44 rows of the BOM with the part JLCPCB matched to each. **Only rows with a ticked check box are placed and paid for.** At the end every one of the 44 rows must be ticked.

| What you see | What it means | What you do |
|---|---|---|
| row ticked, JLCPCB part number equals the number in column `LCSC Part #` of `bom_jlcpcb.csv` | matched, in stock | nothing |
| **yellow exclamation mark**, row not ticked | JLCPCB wants your confirmation; hover over the mark to read why (for example: the matched part name is not literally the BOM text, or the package differs from the footprint name). None is expected for this BOM: every part number stands in one row only and the column `Comment` is JLCPCB's own part name. The footprint names are KiCad's, so a package warning cannot be ruled out | compare the JLCPCB part number in the row with the C number in `bom_jlcpcb.csv`. If equal, tick the row |
| **Shortfall** | JLCPCB's stock is lower than the quantity needed. Needed = 2 x parts per board plus a loss allowance, and at least a minimum quantity (for example 20 pieces for a 0402 resistor). On 2026-11-21 no line was short | for U9, U11, J6, the microphones and U4 see section 2.4. For any other line: stop, do not order, report the part to the maintainer |
| **No Part Selected** (the help article writes "No Parts Selected") / listed under unmatched components | nothing was matched | click **Search**, enter the C number from `bom_jlcpcb.csv`, select the part, tick the row |
| the rows of U9 and U11 | should show that the pieces come from your private stock (section 2.3) | if one shows a shortfall although **My Parts Lib** holds 3 pieces, stop and ask JLCPCB's support chat |
| a window that says some components are not selected, with the choice **Do Not Place** | you clicked **Next** while a row was unticked | never click **Do Not Place**. Go back and tick or fix the row |

Hover over a JLCPCB part number to see the full part record (value, package, voltage) if you want to compare it with `hardware/outputs/bom.csv`.

Parts that are missing from the list on purpose (they are in neither file, so they do not appear at all):

| Footprint on the board | Why it stays empty |
|---|---|
| C13 (22 pF, x 3.8 / y 28.2) | optional capacitor, "do not populate" |
| J5 (3 holes in a row, x 80 to 85 / y 21.5, text "J5: GND TX RX") | debug header, "do not populate" |
| J8 (6 small pads and 3 holes, x 36.5 / y 46) | contact field for a Tag-Connect cable, no part |
| JP1 (two half-round pads, x 84.6 / y 69.7) | solder jumper, no part |
| TP1, TP2, TP3 (three round pads at x 84.0 / y 12.0, x 80.8 / y 12.0 and x 84.0 / y 8.8, with the texts "5V", "3V3" and "GND" near them) | test pads, no part |
| FID1 to FID3, H1 to H4 | fiducial marks and the four corner mounting holes |

These are simply absent on the delivered boards. JLCPCB does not send unplaced parts along.

When all 44 rows are ticked, click **Next**.

### 5.4 The placement preview ("Component Placements")

JLCPCB draws every part on its pads, top view and bottom view. In its drawing a **red dot** marks the orientation mark of an IC, and "+" / "-" mark the anode / cathode of diodes and the plus terminal of polarised capacitors (help: "there will be a dot on the component itself, and there will also be a dot on the PCB (silkscreen), when they match, that means the component is placed correctly").

How to use `fab/jlcpcb/placement_report.csv` (open a copy):

- Column **Status**: all 136 rows say `ok`. JLCPCB's library has a footprint drawing for every part of this parts list, also for the USB-A socket J6 (in revision A2 that row said `check`). For J6 the `ok` confirms position, rotation and pin 1, and nothing more. JLCPCB's footprint record of the new socket (read on 2026-11-21) has its two pin rows 2.71 mm apart. On the board, which was drawn for the Wurth socket of revision A2, the two rows of holes are 2.62 mm apart; the positions along the rows and the four shell holes are the same as in the record. At the placement point of the CPL file each pin row of the record therefore lies 0.045 mm beside its row of holes, which are 0.92 mm wide; 0.045 mm is the value of J6 in the column **Worst pad mismatch mm**. J6 is soldered by hand, so no machine places it by these figures. That the real part fits the holes rests on the drawing of its maker Jing alone (`DECISIONS.md`, F-2 and R-23).
- Column **JLCPCB rotation** is the angle that is in the CPL file. If the preview shows an angle per part, it must be this value.
- Column **Worst pad mismatch mm** is how far JLCPCB's footprint and the board's pads differ at the worst pad (largest value: 0.36 mm for C38 / C41). In the preview every part must sit on its pads, not beside them.
- Column **Matched by** says how the board's pads were laid onto JLCPCB's footprint. For the two red LEDs D4 and D9 it says "pad numbers, terminals swapped by pin name": JLCPCB's drawing of this LED numbers its two pads the other way round than the board, so the angle in the CPL was fitted by the pin names (anode, cathode) and not by the numbers. Nothing to do; check D4 and D9 in the preview like the other LEDs.

The marks on the board are white silkscreen:

- **filled triangle** or **filled dot** next to a pad = pin 1 (ball A1) of that part;
- **bracket with three sides** around one end of a two-pin part = that end is the **cathode** of a diode or LED, or the **plus** terminal of C38 / C41.

Check every row of the following tables in the preview. "Towards the rear edge" and so on are the board directions defined at the top of this guide. Only four parts are on the bottom side: SW1, D7, D8, D9. The bottom view is a mirror image: there left and right are swapped, front edge and rear edge are not.
JLCPCB calls its red dot "a marking only", not pin 1. If a red dot is not where the table says, treat the part as "looks rotated" (procedure after the tables) - it does not have to be an error.
Every row was compared with `placement_report.csv` and with the A3 board file (position, angle, pin 1, silkscreen mark). The positions and marks are those of revision A2; what changed is named in the rows of U4, MK1, MK2, J6 and the four LEDs D4, D6, D9 and D10.

The column **x / y** of the tables is the placement point of the part in the CPL file, turned into the directions of this guide and rounded: column `JLCPCB X` of `placement_report.csv` minus 100, and column `JLCPCB Y` without its minus sign, minus 60. It is the point on which the origin of JLCPCB's own footprint has to lie. That JLCPCB puts the origin there, and not the middle of the pads, is assumed; it matters for the four parts named after the following list. For most parts the point is the middle of the part. For seven parts it is not (the origin lies roughly in the middle of the pads, and the body reaches further to one side):

- U11: the middle of the module is at 21.5 / 59.0; the antenna end has no pads.
- J1: the middle of the socket is at 13.0 / 3.67.
- J4: the middle of the socket is 0.4 mm nearer the rear edge than the point.
- J6: the point (y 10.665) lies 0.175 mm in front of the pin row at y 10.49; the other pin row, with pin 1 at 38.75 / 13.11, is at y 13.11, and the body reaches out over the rear edge.
- J7: the point lies midway between the two pins; pin 1 is at 4.2 / 58.5.
- MK1 and MK2: the middle of the microphone is at 9.5 / 70.2 and at 92.0 / 10.0. These are the positions that `fab/ASSEMBLY_AND_TEST.md` gives. The sound holes are at 10.2 / 70.2 and 92.7 / 10.0.

For the four transistors the point is 0.07 mm off the middle, towards the single pin; that does not show.

Look at four parts first in the preview: **J1, J4, MK1 and MK2**. Their placement point depends on where the origin of JLCPCB's footprint is. In JLCPCB's footprint records of these three part numbers the origin is not the middle of the pads: the two points are 0.162 mm apart for J1, 0.075 mm and 0.175 mm in the two directions for J4, and 0.098 mm for the microphones. In the records of the other part numbers they are less than 0.02 mm apart (JLCPCB's public footprint data, read on 2026-11-21 in the review of the order package). If JLCPCB puts the origin on the point, as the CPL file assumes, the contacts of J4, MK1 and MK2 lie exactly on the pads of the board and those of J1 within 0.15 mm. If JLCPCB put the middle of the pads on the point instead, each of the four parts would sit shifted by the distance named above, the worst pad of J4 by 0.19 mm. Which of the two JLCPCB does cannot be seen without the preview, and the preview was not seen. If one of the four sits beside its pads, treat it as "looks shifted" (procedure after the tables).

**ICs, module, microphones, crystal (all on the top side)**

| Part | What it is | x / y (mm) | CPL rotation | Mark on the board | In the preview |
|---|---|---|---|---|---|
| U1 | CYPD3177-24LQXQT, QFN-24 | 19.5 / 16.6 | 90 | four corner brackets; triangle outside the side that faces the front edge, at its left end | red dot at the front-left corner |
| U2 | LMR33640ADDAR, 8 pins and a large centre pad | 8.5 / 25.5 | 270 | a line along the left and the right side; triangle right of the pin at the right end of the row that faces the rear edge | red dot at that pin (rear-right corner) |
| U3 | TPS2553DBVR, SOT-23-6 | 68.5 / 9.0 | 180 | triangle at the corner that is left and towards the rear edge | red dot at that corner |
| U4 | USB2514BT-I/M2, QFN-36 (same chip as in A2, on tape and reel) | 33.5 / 26.5 | 180 | four corner brackets; triangle outside the side that faces the rear edge, at its right end | red dot at the rear-right corner |
| U5 | TPS2553DBVR, SOT-23-6 | 45.8 / 10.5 | 270 | triangle at the corner that is left and towards the front edge | red dot at that corner |
| U6 | TPS2553DBVR, SOT-23-6 | 45.8 / 4.0 | 270 | triangle at the corner that is left and towards the front edge | red dot at that corner |
| U7 | USBLC6-2SC6, SOT-23-6 | 35.25 / 18.6 | 180 | triangle at the corner that is right and towards the rear edge | red dot at that corner |
| U8 | USBLC6-2SC6, SOT-23-6 | 31.75 / 17.8 | 180 | triangle at the corner that is right and towards the rear edge | red dot at that corner |
| U9 | ADAU7002ACBZ-R7, 8 solder balls, 0.76 x 1.56 mm | 40.0 / 61.0 | 270 | one small dot (0.3 mm), left of the part at the end towards the rear edge. No outline | red dot at that corner; long side of the chip points from rear edge to front edge |
| U10 | MAX98357AETE+T, TQFN-16 | 9.0 / 49.0 | 270 | four corner brackets; triangle left of the part, at the end towards the rear edge | red dot at the rear-left corner |
| U11 | RF-BM-2652P2 radio module, 16.5 x 30 mm | 21.5 / 56.5 | 180 | line across the module end that faces the rear edge; dot (0.5 mm) right of the last pad of the right-hand pad row, at x 31.3 / y 62.0 | the end without pads (antenna) lies on the front edge of the board; pin 1 at the dot |
| MK1 | IM72D128V01XTMA1 microphone (new part, same footprint as in A2) | 9.4 / 70.2 | 90 | rectangle around the part; small triangle outside its corner that is left and towards the rear edge; the round sound-hole pad is in the right half | red dot at the triangle corner; the round port of the part over the hole |
| MK2 | IM72D128V01XTMA1 microphone | 91.9 / 10.0 | 90 | same as MK1 | same as MK1 |
| Y1 | 24 MHz crystal, 4 pads | 42.4 / 25.0 | 180 | an L-shaped line round the corner that is right and towards the rear edge | part covers all four pads. Turned by 180 degrees it is electrically the same |

**Transistors (top side).** A three-pin part cannot be reversed without missing its pads; check that the body covers all three pads.

| Part | x / y (mm) | CPL rotation | Two pins on the side facing | Triangle (between the two pins) points at |
|---|---|---|---|---|
| Q1 (AO3401A) | 8.9 / 13.4 | 90 | the rear edge | the right-hand pin |
| Q2 (2N7002) | 34.1 / 71.6 | 180 | left | the pin nearer the rear edge |
| Q3 (2N7002) | 38.7 / 71.6 | 180 | left | the pin nearer the rear edge |
| Q4 (2N7002) | 34.0 / 50.6 | 0 | right | the pin nearer the front edge |

**Polarised two-pin parts**

| Part | What it is | Side | x / y (mm) | CPL rotation | Closed end of the bracket points | In the preview |
|---|---|---|---|---|---|---|
| C38 | 100 uF polymer capacitor | top | 44.85 / 17.76 | 180 | left | "+" at that end |
| C41 | 100 uF polymer capacitor | top | 40.05 / 18.46 | 90 | towards the rear edge | "+" at that end |
| D1 | SMBJ22A protection diode | top | 4.2 / 12.25 | 270 | towards the rear edge | "-" (cathode) at that end |
| D2 | SD24C-01FTG protection diode (bidirectional) | top | 20.15 / 11.82 | 180 | right | "-" at that end |
| D3 | SD24C-01FTG protection diode (bidirectional) | top | 24.25 / 14.62 | 270 | towards the rear edge | "-" at that end |
| D4 | red LED KT-0603R (new part, matched by pin name) | top | 17.53 / 21.35 | 0 | left | "-" at that end |
| D5 | MM3Z10VT1G Zener diode | top | 13.7 / 12.15 | 270 | towards the rear edge | "-" at that end |
| D6 | green LED KT-0603G (new part) | top | 13.21 / 23.6 | 270 | towards the rear edge | "-" at that end |
| D10 | green LED KT-0603G (new part) | top | 84.4 / 72.2 | 0 | left | "-" at that end |
| D7 | green LED KT-0603G | **bottom** | 34.0 / 71.2 | 90 | towards the front edge | "-" at that end |
| D8 | blue LED KT-0603B | **bottom** | 38.6 / 71.2 | 90 | towards the front edge | "-" at that end |
| D9 | red LED KT-0603R (new part, matched by pin name) | **bottom** | 43.2 / 71.2 | 90 | towards the front edge | "-" at that end |

**Connectors, switch, spacers**

| Part | What it is | Side | x / y (mm) | CPL rotation | Mark on the board | In the preview |
|---|---|---|---|---|---|---|
| J1 | USB-C socket USB4105-GF-A | top | 13.0 / 5.0 | 180 | a short line left and right of the body | opening at the rear edge, the row of small pads towards the board |
| J2 | CM4 socket DF40C-100DS-0.4V(51), 100 pins | top | 74.0 / 65.0 | 0 | a bracket at each short end; small open triangle outside the left end of the pad row that faces the front edge | the part covers both pad rows. It is symmetric: turned by 180 degrees it is the same |
| J3 | CM4 socket, same part | top | 74.0 / 31.0 | 0 | same as J2 | same as J2 |
| J4 | microSD socket DM3AT-SF-PEJM5 | top | 56.1 / 8.9 | 180 | lines along the sides of the body | card slot opens at the rear edge, the row of contact pads towards the front edge |
| J6 | stacked USB-A socket 907-112A1022D10200 (new part), **through-hole, soldered by hand** | top | 35.25 / 10.67 | 180 | a line along the body side that faces the front edge and a short line at the left and at the right side; 8 pin holes in two rows, 4 large holes for the shell; the square pad (pin 1) is the right-hand hole of the row nearer the front edge | JLCPCB has a footprint drawing for this part now: it must lie on the 12 holes, with pin 1 on the square pad (this checks position, rotation and pin 1; see the note on column **Status** above). Its two pin rows are 0.045 mm off the centres of the holes; that does not show. The real part fits its 12 holes in one way only: both USB openings face outward and the body overhangs the rear edge by about 2.5 to 2.85 mm |
| J7 | speaker socket B2B-PH-K-S (JST PH, 2 pins), **through-hole, soldered by hand** | top | 4.2 / 57.5 | 270 | outline of the housing, an L-shaped corner mark at its front-left corner, text "SPK" to the right | the part sits on both holes; pin 1 is the hole nearer the front edge; the wider part of the housing points right, towards "SPK": the housing reaches 2.8 mm to the right of the pins and 1.7 mm to the left (its white outline is drawn 0.1 mm outside it, so 2.9 mm and 1.8 mm) |
| SW1 | slide switch JS202011JCQN | **bottom** | 33.5 / 54.0 | 180 | rectangle, text "MUTE" | the part covers all six pads. It is symmetric |
| H5, H6, H7, H8 | threaded spacers 9774015151R for the CM4 | top | 95.5 / 64.5, 95.5 / 31.5, 47.5 / 64.5, 47.5 / 31.5 | 0 | none | each sits centred on its 3.7 mm hole |

All other parts (resistors, ceramic capacitors, the inductor L1) have no polarity. Check only that each sits on its two pads and none lies across two footprints.

**When a part looks rotated or shifted**

1. Do not edit the CPL file and do not turn the part in the preview.
2. Write down the designator and what you see (for example "U7 turned by 90 degrees").
3. Go on with **Next**. JLCPCB's engineers correct rotation and polarity from the silkscreen marks before assembly (help: "our engineers will review and fix the rotation and polarity of the components based on the silkscreen markings before assembly"; if silkscreen and CPL disagree, "we will make the placement according to the silkscreen layer by default").
4. Write it in the assembly remark: add a line such as "Preview: U7 appears turned by 90 degrees - please place by the silkscreen mark." The remark field is on the order form (section 4.2); JLCPCB's help says an order in the cart can be reopened with **Edit Order** (whether the remark can still be changed there could not be verified). Items 2 and 3 of the remark in section 6.2 already tell the engineers to follow the silkscreen, so the order is safe even if you cannot add the line.
5. Because **Confirm Parts Placement** is **Yes**, JLCPCB sends you its corrected placement before it solders. Check your noted parts there first (section 7.3). If one is still wrong there, do not confirm; answer with the designator and the sentence "please place according to the silkscreen mark".

### 5.5 Quote & Order

1. The page shows the complete price list of the assembly. Compare it with section 8. The number of feeder lines should be near 42, X-ray 2 pieces.
2. Choose a **product description** (help: "you need to select the product description and then save it to the cart"). Take the entry that fits a consumer electronics / smart-home device best. The list itself could not be retrieved.
3. Do not select the SMT expedite option ("USD 47.83 per day").
4. If the page offers a **Shortage Preference**, leave **Require Full Quantity** (the other choice is **Accept Shortages**).
   Where this comes from: the step stood in the guide for revision A2 (2026-11-12). None of the help articles that were fetched on 2026-11-20 mentions it; the index of JLCPCB's help centre lists an article "How to Set up Shortage Preference?", which was not fetched. The three labels are in the public script of JLCPCB's order site (read on 2026-11-21 at 00:40 UTC, not seen on a page). The same script explains the first choice with "If any shortages occur during PCB production, we will automatically remake the missing pieces and ship the exact ordered quantity." and holds the sentence "Shortage preference is set to 'Require Full Quantity' for full PCBA assembly." - so the choice may already be made for you, or not be shown at all.
5. Click **Save to Cart**.

---

## 6. Remarks to paste

### 6.1 PCB Remark (section 3.4)

```
1. Via Covering = Epoxy Filled & Capped: please fill and cap ALL 0.30 mm holes (294 holes: 286 vias and 8 thermal holes that are drawn as pads inside one exposed pad). 13 of them are via-in-pad inside the exposed pads of four ICs - fill and cap these as well.
2. All holes of 0.60 mm and larger are component or mounting holes and must stay open.
3. The two non-plated 0.80 mm holes at X110.18 Y-130.20 and X192.68 Y-70.00 (Gerber coordinates, mm) are sound ports of MEMS microphones: keep them open, no solder mask ink, no resin. The copper ring around each of these two holes is the solder land of the microphone and starts 0.21 mm from the hole edge, which meets your 0.2 mm hole-to-copper clearance: please do not trim or remove the ring.
4. Edge rails for the assembly: please add them to the two 74 mm edges (panel 110 x 74 mm), NOT to the two 100 mm edges. Connectors overhang one 100 mm edge and a module ends flush with the other. Copper keeps 0.45 mm from both 74 mm edges.
5. Stack-up JLC04161H-3313 as selected. No impedance test required.
```

### 6.2 Assembly remark (section 4.2)

```
1. MK1 and MK2 (C5119248, IM72D128V01XTMA1) are bottom-port MEMS microphones. Each has a 0.8 mm sound hole through the PCB; the bottom silkscreen says "MIC - NO WASH" next to it. Board Cleaning = Caution for Special Parts: no washing, no solvent, no dry ice, no conformal coating, no liquid or flux into these two holes, no compressed air into them.
2. The silkscreen carries no reference designators (they are in the CPL only). Polarity marks on the silkscreen: filled triangle or dot = pin 1 / A1 (ICs, module U11, microphones, transistors). Three-sided bracket around one end of a two-pin part = cathode of D1-D10, plus terminal of C38 and C41.
3. If a CPL rotation disagrees with the silkscreen mark, the silkscreen is right. Please send the placement for my confirmation before assembly.
4. EDGE RAILS - REQUEST: please add the 5 mm edge rails to the two 74 mm edges (panel 110 x 74 mm), NOT to the two 100 mm edges. Reason: J6 (stacked USB-A, through-hole) overhangs one 100 mm edge by 2.5 to 2.85 mm, J1 (USB-C) and J4 (microSD) end at the same edge; U11 ends flush with the other 100 mm edge and the pads of small parts start 0.95 mm from it. The two 74 mm edges have no overhanging parts and copper keeps 0.45 mm from them. I accept the price difference for the larger panel.
5. J6 (C29780026) and J7 (C131337) are through-hole parts for hand soldering. J6: USB openings face outward over the board edge, body flat on the board. J7: follow the silkscreen outline.
6. Not populated on purpose: C13, J5, J8 (bare pads), JP1 (solder jumper), TP1-TP3 (test pads).
7. Please do not replace any part without asking me.
```

If a remark field does not take the whole text, keep the items in the order given and drop from the end - but never drop item 4 of either remark (the edge rails).
If you took an alternate part from section 2.4, change the part number in item 1 or item 5 and add the line given there.

---

## 7. Payment, "Review Before Payment", confirmation e-mails

### 7.1 Cart and checkout (help; pages not seen)

1. Open the cart, expand the order and check: PCB Qty 5, PCBA Qty 2, ENIG, JLC04161H-3313, Epoxy Filled & Capped.
2. Click **Secure Checkout**.
3. Enter the delivery address as a private person, no company name.
4. Shipping method: select **DHL Express (DDP)** first. Live price for Austria on 2026-11-20 and 2026-11-21: $23.40 for a parcel up to 0.5 kg ($26.84 above 0.5 kg), 2-4 business days. It costs the same as plain "DHL Express". With (DDP) JLCPCB collects the import VAT, the carrier's fee and the EU handling fee at checkout, and nothing is paid at the door. The checkout sorts the methods into two groups, "CPT" and "DDP" (labels from the public script of JLCPCB's order site); take a method from the DDP group only.
5. The checkout now shows the tax lines (summary line "Customs duties & taxes"; inside it "Value-Added Tax", "Duty & Tax Disbursement Fee", "Union Handling Fee" - labels from the same script, not seen on a real checkout). Expect about 20 % of goods plus shipping as VAT and about 19 EUR of fees (section 8). These lines could not be retrieved in advance. Write down the grand total: goods, shipping and taxes together.
6. Compare with **FedEx Express (DDP)**: select it and write down its grand total. Live price: $27.51 up to 0.5 kg ($31.85 above), 4-6 business days. JLCPCB's shipping page says for this method and Austria (live 2026-11-21): "You will enjoy a waiver of Duty & Tax Disbursement Fee with minimun charge of EUR 15 when selecting FedEx Express DDP". If that means what it seems to, FedEx is up to 11.55 USD cheaper in total although its shipping price is higher; if JLCPCB charges no such fee for DHL either ("may be discounted", help), FedEx is 4.93 USD dearer (arithmetic in section 8.3). Only the two totals on your screen can tell.
   **Rule:** take **FedEx Express (DDP)** if its grand total is lower than that of DHL Express (DDP) and two more days of delivery do not matter to you. In every other case take **DHL Express (DDP)**.
7. Only if **EuroPacket** is in the list (forum users report that it is not offered for orders with assembly; JLCPCB's own pages say nothing): select it and look at its total. Its shipping price is lower ($15.73 at 0.3 to 0.4 kg, $17.01 at 0.4 to 0.5 kg, live), and JLCPCB states that it carries no Union Handling Fee. How it is taxed for an order above 150 EUR is not stated anywhere.
   **Rule:** take EuroPacket only if all four are true: (a) it is listed; (b) its line "Customs duties & taxes" is there and is about 20 % of goods plus shipping, so that the VAT is paid at checkout; (c) its grand total is lower than both others; (d) you accept what comes with it: 5-8 business days (6-12 in JLCPCB's delivery time table), a complaint rate for Austria of 327.87 per ten thousand parcels against 26.11 for DHL Express (order form, live), no change to another method afterwards, no payment from JLCPCB balance. If one of the four is not true, or if you are in doubt, do not take it.
8. Coupon: the page lists the coupons your account can use. One coupon per order. A new account normally has a "$10 New User SMT Coupon"; select it if it is offered.
9. Payment method: select **Review Before Payment**.
10. Submit the order. You do not pay now.

If the checkout does not offer **Review Before Payment**, pay in the normal way. The review then happens after payment, and a fee that changes in the review arrives as a separate payment request; the order stands still until it is paid.
That can happen. JLCPCB's two help texts disagree: "PCB Assembly FAQs (Part 2)" (updated 9 Sep 2026, fetched again on 2026-11-20) still has the item "Why PCBA order does not support Review Before Payment?" with the answer "So the assembly order needs to be paid first", while the article that section 7.2 follows (updated 23 Sep 2026, fetched 2026-11-12) describes Review Before Payment with reserved parts. Only the checkout shows which of the two holds.

### 7.2 What "Review Before Payment" does (help article updated 23 Sep 2026, fetched 2026-11-12 and not again)

| Step | Status shown | What happens |
|---|---|---|
| 1 | **File Review**: Pending Review, then Reviewing, then Review Completed | JLCPCB's engineers check the files, the parts and the advanced options. The parts are reserved for you from the moment you submit, for up to 7 days |
| 2 | **Approved** / **Awaiting Payment** | the amount is final. The price difference for the larger panel with rails on the 74 mm edges (about 22 USD, section 4.3) and any other fee the review changed (a step stencil, a fixture, special handling of a part) are already included. An approved order cannot be changed any more |
| 3 | you pay | PayPal, card, Google Pay, Apple Pay, Klarna or JLCPCB balance. Compare the amount with section 8 first. If it is above the "high" column, ask JLCPCB's support what was added before you pay |
| 4 | **Confirmed** | the normal production process starts |

Pay within the 7 days, otherwise the reserved parts are released.

### 7.3 Messages after payment and what to look at

Check your e-mail and the order page (**ACCOUNT** menu, order history) at least once a day until the order has shipped. A status **Pending** means JLCPCB waits for you and the clock is stopped.

| Message | When | Look at | Then |
|---|---|---|---|
| **Confirm Production file** (the PCB data JLCPCB will manufacture) | when the production file is ready; you have 48 hours, and with "Do not confirm automatically" it waits for you | 1. Size 100 x 74 mm plus the rails, and the rails are on the two 74 mm edges (panel 110 x 74 mm). 2. Four copper layers; layer 2 is an almost solid plane. 3. Stack-up JLC04161H-3313. 4. The two 0.8 mm holes under the microphones exist (x 10.2 / y 70.2 and x 92.7 / y 10.0). 5. The four slots of the USB-C socket and the four corner holes exist. 6. Both "MIC - NO WASH" texts are there, and the revision text says "rev A3". 7. No order number was added to the board | confirm if all seven points are right. If the rails are on the 100 mm edges, do not confirm; answer "please move the edge rails to the two 74 mm edges as requested in the remarks". If the engineers changed something you do not understand (track widths, removed pads, moved holes), do not confirm either; ask them what and why, and ask the maintainer. No change is expected at the two microphone holes: the ring-shaped pad around each of them starts 0.21 mm from the hole edge (0.61 mm from the hole centre, section 1), and JLCPCB keeps 0.2 mm around a hole without plating free of copper (its capabilities page, read on 2026-11-20: "a 0.2 mm ring of copper to be removed around the hole"), so there is nothing to cut back. Item 3 of the PCB remark asks JLCPCB not to trim the ring. A cut of a few hundredths of a millimetre does not show in a picture; if JLCPCB writes that it changed or wants to change this ring, do not confirm and answer as in the row about copper near a hole without plating below. Do not confirm either if a ring is gone, or if one of the two holes is smaller, moved or plated |
| **Confirm Parts Placement** (JLCPCB's placement drawing after its own corrections) | some hours after the order is confirmed; you have 72 hours, and with "Do not confirm automatically" it waits for you | go through the tables of section 5.4 once more, top and bottom; look at J1, J4, MK1 and MK2 first (why: section 5.4). JLCPCB: "For SMD parts, please check the placement and polarity in 2D production file. For through-hole parts, please check the placement in 3D production file." Check J6 and J7 in the 3D file: J6 openings outward, both on their holes. Count: 132 parts top, 4 bottom, nothing on C13, J5, J8, JP1, TP1 to TP3 | confirm if everything matches. Otherwise answer with the designator and what is wrong |
| question about a part: unclear polarity, footprint mismatch, parts too close | any time during data preparation | the designator they name, in section 5.4 | answer the same day. The standard answer for polarity is "follow the silkscreen mark" |
| question or note that copper is too close to a hole without plating, or a proposal to trim copper there | not expected; during review or data preparation | section 1, row "Copper to holes without plating": the copper keeps 0.2 mm or more from all 15 such holes, and the ring at each of the two 0.8 mm microphone holes starts 0.21 mm from the hole edge | no change is wanted. Answer: "In the Gerber files the copper keeps 0.2 mm or more from every non-plated hole (0.21 mm at the two 0.8 mm microphone holes). Please do not change the copper there; keep the ring around each microphone hole and keep both holes 0.8 mm, non-plated and open." If JLCPCB still wants a change, do not agree and do not confirm; ask which hole and which distance it means, and ask the maintainer |
| proposal for a **step stencil** with a price | during review | - | accept it. The board mixes 0.4 mm pitch parts (U9, J2, J3) with large parts; JLCPCB refunds the fee if the stencil later turns out to be unnecessary (help) |
| price difference for the 110 x 74 mm panel, or a request for a **fixture**, with a price | during review | - | accept it. The panel difference (about 22 USD) is in the "expected" column of section 8, the fixture in the "high" column |
| a message that the rails stay on the 100 mm edges | during review | - | do not accept; repeat item 4 of the assembly remark. If JLCPCB insists, ask the maintainer before you confirm anything |
| a supplement after you have paid | rare with Review Before Payment | the reason given | pay it only if the reason is in this guide; otherwise ask |
| tax or duty demand from the carrier (DHL or FedEx) at delivery | delivery | - | with a (DDP) shipment do not pay. JLCPCB: "If customer who has prepaid tax (VAT) receives the tax payment notice from the logistics supplier, please refuse to pay and contact us." Its shipping page names the address for this case: logistics@jlcpcb.com |

---

## 8. Cost estimate

All amounts in USD unless marked. Which figure is of which day: the PCB form and the assembly price list were read again on 2026-11-20, the shipping prices on 2026-11-20 and 2026-11-21 (00:30 to 01:00 UTC); they were not read again after that. The part prices are those of 2026-11-21, 09:57 UTC (the second of the two reads of the parts list; row "live" of the table at the top). The estimate for revision A2 in section 8.2 is that of 2026-11-12 and is unchanged. EUR values use the rate of 2026-11-20 given at the top.

### 8.1 The estimate for revision A3

"Low" assumes everything goes as planned, the new-customer coupon applies and JLCPCB does not charge for the larger panel; "high" adds every supplement that JLCPCB's review can plausibly ask for.

| Line | Low | Expected | High | Source and assumption |
|---|---|---|---|---|
| PCB, 5 pieces, ENIG, JLC04161H-3313, epoxy filled and capped vias, panel 110 x 74 mm (rails on the 74 mm edges) | 47.64 | **69.61** | 69.61 | live quote of 2026-11-20 (23:10 and 23:14 UTC), the same as on 2026-11-12. 69.61 is what the form shows for 110 x 74 mm with the options of section 3 when the size is typed in by hand: 25.00 Engineering fee + 5.10 Board + 17.50 Surface Finish + 17.55 Via Covering + 3.41 Via Plating Method + 1.05 Confirm Production file. 47.64 is what the form shows during the order (rails on the 100 mm edges, 100 x 84 mm: 8.00 + 17.60 + 17.58 + 3.41 + 1.05); low: the difference is not charged |
| Assembly setup, both sides | 51.12 | **51.12** | 51.12 | list |
| Stencil, both sides | 16.42 | **16.42** | 16.42 | list |
| SMT joints at 0.0016 | 2.08 | **2.08** | 2.40 | list; 649 SMD pads per board in the board file (637 on parts of the top side, 12 on parts of the bottom side) x 2 = 1,298. High: 1,500 if JLCPCB counts differently |
| Feeder loading at 1.53 per part type | 64.26 | **64.26** | 67.32 | list ("$1.53 Basic/Extend": Basic and Extended parts cost the same here); `bom_jlcpcb.csv` has 44 rows = 44 part numbers, 42 of them machine-placed and 2 hand-soldered (J6, J7): 42 x 1.53. High: 44 x 1.53 if the two hand-soldered parts are charged too |
| Hand-soldering labor, per order | 3.58 | **3.58** | 3.58 | list |
| Manual assembly at 0.0164 per joint | 0.46 | **0.46** | 0.59 | list; J6 has 12 joints (8 pins, 4 shell posts), J7 has 2: 14 x 2 boards = 28. High: 36 if the 4 shell posts of the USB-C socket J1 are hand-soldered too |
| X-ray at 1.64 per piece (0.82 from 11 pieces) | 3.28 | **3.28** | 9.84 | list; only ADAU7002ACBZ-R7 carries JLCPCB's X-ray flag (live): 2 pieces. High: all six leadless parts per board (U1, U4, U9, U10, MK1, MK2) = 12 x 0.82 |
| Packing | 0.50 | **0.50** | 0.50 | list |
| Confirm Parts Placement | 0.45 | **0.45** | 0.45 | list |
| Depanel boards & edge rail before delivery | 1.70 | **2.90** | 2.90 | form text "$1.4 service fee and $0.3 per panel": 1 panel or 5 panels - JLCPCB's count is not known |
| Board Cleaning "Caution for Special Parts" | 0 | **0** | 0 | no fee is named in the form text - assumed 0 |
| Fixture, 2 pieces | 0 | **0** | 16.42 | list; only if the engineers ask for a carrier |
| Step stencil | 0 | **0** | 61.79 | form text: $0.008 per pin + $9.4 + $47.2 labour, with 649 pins; only if the engineers recommend it |
| Exchange-rate drift of the listed assembly fees | 0 | **0** | 7.00 | 3 % of the fee lines above (233.33 in this column); the list says prices "may vary slightly due to exchange rate fluctuations". It also covers the amounts in the help texts of the form that differ from the list: $1.50 per feeder, $0.02 per manual joint |
| Parts for 2 boards, with one spare each of the two thin parts | 94.38 | **96.15** | 120.19 | live prices of all 44 parts, read on 2026-11-21 (`hardware/outputs/order_cost.json`): 84.99 with JLCPCB's minimum and loss quantities (83.22 if only the minimum quantities are billed, 79.68 for the needed pieces alone), plus 11.16 for the two spares of step 2.3 (2.4754 + 8.6843). 84.99 is the sum of the unrounded lines (84.9866); the 44 lines of `hardware/outputs/order_cost.csv`, each rounded to the cent, add up to 84.96. These are unit prices only; the one fee that a part record carries on top of its price is the next row. High: expected + 25 % for a substitute, a sourced part or price changes |
| Special component fee of the USB-C socket J1 | 0.03 | **0.06** | 0.06 | live: JLCPCB's record of USB4105-GF-A (C3020560) carries a "special component fee" of 0.03 USD (`hardware/gen/sourcing_jlc.json`, field `special_fee`); the other 43 lines carry none. No text that was read explains this fee or says what it is charged per, and `order_cost.json` does not contain it. Expected: per piece, 2 x 0.03. Low: once for the line |
| Coupon | -10.00 | **0** | 0 | "$10 New User SMT Coupon", one coupon per order, not guaranteed |
| **Goods total** | **275.90** | **310.87** | **430.19** | |
| Shipping DHL Express (DDP) to Austria | 23.40 | **23.40** | 26.84 | live; parcel up to 0.5 kg, high: above 0.5 kg. JLCPCB's weight for the 5 PCBs alone: 0.26 kg; with the parts of two boards and packing about 0.35 to 0.45 kg (estimate) |
| Austrian import VAT, 20 % of goods + shipping | 59.86 | **66.85** | 91.41 | estimate; EU customs duty for printed circuits and electronic assemblies is 0 % |
| Import handling: carrier's disbursement fee + EU "Union Handling Fee" | 4.40 | **20.88** | 28.57 | expected: 15 EUR (JLCPCB's table for DHL and Austria: "3% of the advanced amount, Minimum 15.00 EUR"; 3 % of the VAT is about 2 USD, so the minimum counts) + 2 declaration lines x 2 EUR = 19 EUR. Low: fee waived by JLCPCB ("may be discounted"), 2 x 2 EUR. High: 20 EUR (the top of the range "Minimum Charge: USD (or EUR) 10-20" in the checkout text) + 3 x 2 EUR = 26 EUR |
| **Total, USD** | **363.56** | **422.00** | **577.01** | |
| **Total, EUR** | **330.80** | **383.98** | **525.02** | x 0.9099 |

### 8.2 Old and new: revision A2 on 2026-11-12 against revision A3 now

The "expected" column of the guide for revision A2 (prices of 2026-11-12) against the "expected" column above (part prices of 2026-11-21, all other prices as read on 2026-11-20 and 2026-11-21; top of this section). Lines that are 0 in both are left out.

| Line | A2, 2026-11-12 | A3, now | Difference | Reason |
|---|---|---|---|---|
| PCB | 69.61 | 69.61 | 0 | same board size, same options; the form price was read again on 2026-11-20 and is unchanged to the cent. The via covering was not changed (8.3) |
| Assembly setup, both sides | 51.12 | 51.12 | 0 | same price list |
| Stencil, both sides | 16.42 | 16.42 | 0 | same price list |
| SMT joints | 2.08 | 2.08 | 0 | same 649 pads per board |
| Feeder loading | 78.03 | 64.26 | -13.77 | the fee is 1.53 USD per machine-placed part type: 51 then, 42 now. The BOM had 53 rows and has 44: 6 resistor values, 2 capacitor lines and 1 LED line less. 9 x 1.53 = 13.77 |
| Hand-soldering labor | 3.58 | 3.58 | 0 | still J6 and J7 |
| Manual assembly | 0.46 | 0.46 | 0 | same 28 joints |
| X-ray | 3.28 | 3.28 | 0 | same 2 pieces |
| Packing | 0.50 | 0.50 | 0 | same price list |
| Confirm Parts Placement | 0.45 | 0.45 | 0 | same price list |
| Depanel boards & edge rail | 2.90 | 2.90 | 0 | same form text |
| Parts for 2 boards with spares | 103.21 | 96.15 | -7.06 | then 89.91 for 53 lines plus 13.30 for three spares; now 84.99 for 44 lines (`hardware/outputs/order_cost.json`, prices of 2026-11-21) plus 11.16 for two spares. Behind it: the USB-A socket costs 0.73 instead of 5.52 for two, ADAU7002ACBZ-R7 4.95 instead of 7.81 (its price fell), RF-BM-2652P2 17.37 instead of 13.27 (its price rose from 6.6325 to 8.6843), the microphones 12.77 instead of 12.56, and there is no spare USB-A socket any more |
| Special component fee of J1 | 0 | 0.06 | +0.06 | not a new fee: JLCPCB's record of the part carried the same 0.03 USD on 2026-11-12 (stock file of that day), but the guide for revision A2 did not count it. 2 x 0.03 |
| **Goods total** | **331.64** | **310.87** | **-20.77** | -13.77 - 7.06 + 0.06 |
| Shipping DHL Express (DDP) | 23.52 | 23.40 | -0.12 | JLCPCB's price on 2026-11-20 |
| Import VAT, 20 % | 71.03 | 66.85 | -4.18 | 20 % of 334.27 instead of 355.16 |
| Import handling | 21.14 | 20.88 | -0.26 | the same 19 EUR, at 1.0990 instead of 1.1127 USD per EUR |
| **Total, USD** | **447.33** | **422.00** | **-25.33** | |
| **Total, EUR** | **402.02** | **383.98** | **-18.04** | old total x 0.8987 (rate of 2026-11-11), new total x 0.9099 (rate of 2026-11-20). The dollar became dearer in between: at today's rate the old total is 407.03 EUR, so like for like the order is 23.05 EUR cheaper |

What the comparison does not show: revision A2 could hardly be ordered any more. Three of its lines are almost out of stock (section 2.2), one of them down to exactly the two pieces needed, and its parts line would be 104.85 USD at the prices of 2026-11-20 instead of 103.21 (stock check of that day; the parts of revision A2 were not priced again on 2026-11-21). An A2 order placed today, counted like the A3 column with the 0.06 USD fee of J1, would come to 448.97 USD (goods 333.34, shipping 23.40, VAT 71.35, handling 20.88): 26.97 USD more than revision A3.

### 8.3 Evaluated and not taken

Four ways to make the order cheaper were looked at and left out of the plan.

| What | It would have saved | Why it was not taken |
|---|---|---|
| **Via Covering** "Plugged" instead of "Epoxy Filled & Capped" | 20.96 USD (PCB 48.65 instead of 69.61, live 2026-11-20); 25.15 USD with VAT | JLCPCB never plugs a hole that sits in a pad, and this board has 13 of them under four chips. Moving them out was worked out to the end (a thermal model, a layout variant that was built and passed all checks): the regulator would run 2.9 to 5.5 K hotter at the theoretical peak, the amplifier 13 K at continuous full power, and the hub and the power controller would sit on solder mask strips of unknown height - a chip that lifts is a dead board, and nobody can rework these two boards. The variant stays the fallback for a later, larger run (`DECISIONS.md`, C-11) |
| Edge rails on the two 100 mm edges, as the form assumes | 21.97 USD (PCB 47.64 instead of 69.61; 22.00 USD with "Plugged" vias); 26.36 USD with VAT | the 110 x 74 mm panel is above 102 x 102 mm and loses JLCPCB's "Special Offer". But J6 overhangs the rear 100 mm edge, U11 is flush with the front 100 mm edge and small parts sit 0.95 to 2.6 mm from it (section 4.1): rails scored off along these edges put the parts at risk |
| Assembly on one side only | 33.77 USD ((51.12 - 25.56) setup + (16.42 - 8.21) stencil, list); 40.52 USD with VAT | the bottom side carries the mute switch SW1 and the three status LEDs D7, D8, D9. They face the top cover of the enclosure and cannot move to the other side; without them the device has no mute switch and no status light, and nobody solders them on afterwards |
| A cheaper shipping method | FedEx Express (DDP): up to 11.55 USD, if its fee waiver applies: (27.51 - 23.40) x 1.2 = 4.932 more for shipping and VAT, 15 x 1.0990 = 16.485 less for the fee. EuroPacket: 28.55 to 30.08 USD on paper (shipping 17.01 or 15.73 instead of 23.40, with VAT, and no handling fees) | neither could be verified without a login: no tax line of any method is shown before checkout. FedEx is 4.93 USD dearer if JLCPCB waives the fee for DHL as well. EuroPacket is probably not offered for orders with assembly, and how it is taxed above 150 EUR is not stated. So DHL Express (DDP) stays the plan, and the comparison is a step at checkout (section 7.1) |

### 8.4 Notes on the tables

- 33.48 USD of the parts line (3 pieces each of the two thin parts) is paid earlier, in step 2.3. The rest is one payment after the review.
- The largest part lines for 2 boards: RF-BM-2652P2 17.37, the four microphones 12.77, LMR33640ADDAR 5.81, ADAU7002ACBZ-R7 4.95, USB2514BT 4.77, the eight spacers 4.46, the four CM4 sockets 4.30, CYPD3177 3.41 USD. The USB-A socket, 5.52 USD in revision A2, is now 0.73.
- About 132 USD of the goods are fixed assembly fees (setup 51.12, stencil 16.42, feeders 64.26) that do not depend on the number of boards.
- If you choose the runner-up **Photo Confirmation: Yes**, add 7.50 USD.
- If you take FedEx Express (DDP) in step 7.1, the shipping line is 27.51 instead of 23.40; whether the total is lower depends on the fee lines of the checkout.
- The goods value (310.87 USD = 282.86 EUR) is above 150 EUR and above JLCPCB's own limit of 170 USD for the simplified IOSS scheme (help, article updated 16 Nov 2026). VAT is collected by JLCPCB at checkout because of the (DDP) shipping method.
- Paying in EUR: JLCPCB converts at its own rate. On 2026-11-12 it was 0.9000 EUR per USD against the ECB's 0.8987; it was not read again. Your bank or PayPal may add a conversion fee.

---

## 9. Delivery time

| Stage | Time | Source |
|---|---|---|
| Review before payment | not stated by JLCPCB | - |
| PCB production, option "3 days PCBA Only" (also offered with filled vias) | 3 days | live |
| SMT assembly | "over 90% of PCB assembly orders complete the entire SMT process within 24-48 hours after PCB fabrication is finished" | help |
| Through-hole parts J6, J7 | 1 more day | help |
| Removing the rails | 1 more day | form text |
| Your two confirmations and any question | the clock stops until you answer | help |
| DHL Express (DDP) to Austria | 2-4 business days on the form; 3-6 business days in JLCPCB's delivery time table for Europe ("based on 90% of our history orders") | live, help |
| FedEx Express (DDP) to Austria, if you took it in step 7.1 | 4-6 business days on the form; 6-8 in the same table | live, help |

In revision A2 JLCPCB had to create a library footprint for J6 first ("typically completed within 48 hours"). That step is gone: the new connector has one.

Estimate: **9 to 13 calendar days from payment to delivery** with DHL if you answer every message on the same day (two days more with FedEx); the review before payment comes on top. Each day a confirmation waits adds a day. Parcels that reach JLCPCB's shipping centre after 11 am on a Saturday leave on Monday.

---

## 10. Incoming inspection - before anything is plugged in

The parcel contains 5 boards: **2 assembled boards and 3 boards without parts** (called "empty boards" below).
Pictures of the design to compare with: `hardware/outputs/render_top.png` and `hardware/outputs/render_bottom.png`.

### 10.1 Parcel and handling

1. Look at the box before you accept it. If it is crushed or wet, photograph it before opening. JLCPCB's shipping page asks for damage to be reported within 7 days after receipt.
2. Pay nothing at the door (section 7.3, last row).
3. Before touching a board, touch an earthed metal object (for example the bare metal of a radiator). Hold boards by the edges. Lay them on the antistatic film they came in.
4. Do not blow into, poke or wash the two small holes in opposite corners of the board, and do not press on the two small metal cans above them. They are the microphones and their sound ports.

### 10.2 The 3 empty boards

| Check | Good |
|---|---|
| Count and colour | 3 boards, green, white print, gold pads |
| Size | 100 x 74 mm, thickness about 1.6 mm (1.44 to 1.76 mm is within JLCPCB's tolerance) |
| Edges | the rails are gone. Small rough spots on the two 74 mm edges (left and right), where the rails were broken off, are normal: JLCPCB separates by hand and does not grind the edges |
| Text, top | "VoxHub CM4  rev A3", "SPK", "J5: GND TX RX", and "5V", "3V3", "GND" at the three test pads. A board that says "rev A2" was made from old files: report it to the maintainer before you go on |
| Text, bottom | "VoxHub CM4 rev A3 - this side faces the top cover", the address of this repository, "MUTE", "USB-C PD 9-20V", twice "MIC - NO WASH". No order number anywhere |
| Filled vias | hold a board against a lamp: no light comes through the 0.3 mm holes. The large pads in the middle of the footprints of U1, U2, U4 and U10 are flat gold without open holes |
| Microphone holes | light passes through the two 0.8 mm holes at x 10.2 / y 70.2 and x 92.7 / y 10.0 |
| Gold pads | even colour, no bare copper, no green solder-mask ink on pads |

If light passes through many of the small holes, the option "Epoxy Filled & Capped" was not carried out: report it to JLCPCB before you use the assembled boards.

Keep the empty boards. They show what every footprint looks like without its part.

### 10.3 The 2 assembled boards

Use a magnifier or the zoom of a phone camera. Go through the tables of section 5.4 on the real board: each IC has a dot or a notch on its body, and it must be at the white triangle or dot of the board.

| Check | Good |
|---|---|
| Top side, large parts present | USB-C socket J1, double USB-A socket J6 and microSD socket J4 at the rear edge; radio module U11 (the largest part, 16.5 x 30 mm, its end without pads at the front edge); the two long CM4 sockets J2 and J3; four threaded spacers H5 to H8; speaker socket J7 at the left edge; inductor L1; microphone MK1 in the front-left corner and MK2 in the rear-right corner |
| Bottom side | slide switch SW1 next to "MUTE"; three LEDs in a row near the front edge; nothing else. With the board turned over and the rear edge still away from you they are, from left to right, D9 (red), D8 (blue) and D7 (green); the colours show only when the LEDs are lit (`fab/ASSEMBLY_AND_TEST.md`) |
| Empty on purpose | C13, J5 (3 holes), J8 (6 pads, 3 holes), JP1, the three test pads TP1 to TP3 - compare with an empty board |
| J6 (USB-A) | sits flat on the board, not tilted; all 12 pins are soldered on the bottom side; both openings are free and look outward over the rear edge. The plastic inside the two openings is black (maker's drawing of the new part; the part of revision A2 was white) |
| J7 (speaker socket) | sits flat; 2 pins soldered on the bottom side |
| J2, J3 (CM4 sockets) | no solder between neighbouring contacts (0.4 mm apart), no bent contact, nothing inside the socket |
| U11 (radio module) | every half-round pad along its two long sides has solder; the module lies flat |
| U1, U2, U4, U10 | no solder bridge between pins; the part lies flat and is not shifted |
| Diodes and LEDs | the cathode mark of each part is at the closed end of the white bracket: a bar on the diodes, a small green mark on the top face of the six LEDs (D4, D6 to D10). The mark of the LEDs is read from the KENTO data sheets of KT-0603R, KT-0603G and KT-0603B (page 2: the cathode end carries a green mark on the top face; the underside, which a soldered part does not show, has a green T-shaped mark); it was not looked at on a part. D2 and D3 work in both directions. All six LEDs also show in the tests of `fab/ASSEMBLY_AND_TEST.md` whether they light |
| C38, C41 | the bar on the capacitor body (plus) is at the closed end of the bracket |
| Microphone holes, seen from the bottom | open and round; no solder, flux or dirt in them |
| Spacers H5 to H8 | stand upright; the thread is clean; a fillet of solder is visible at the foot of each spacer. Look at each one all the way round: the paste is printed in four segments, so there are four places per spacer. The ring pad reaches 0.45 mm beyond the foot (pad 6.0 mm in diameter on the board, foot 5.1 mm in the Wurth data sheet), and that is where the fillet sits. Where it is missing at one of the four places, solder is added there by hand: the board gives these four parts less solder paste than their maker suggests (section 1, paragraph "Solder paste") |
| SW1 | slides in both directions and stays there |
| Loose solder | no solder balls; nothing rattles when you tilt the board |
| Flux | a clear, slightly sticky film around the pins of J6 and J7 is normal (JLCPCB's own description); these boards are not washed |

### 10.4 If something is wrong

1. Do not plug in the CM4, a charger or a USB device.
2. Photograph the fault sharply, and the whole board in a second picture.
3. Report it to JLCPCB through the order page before you use the boards, and tell the maintainer of this repository.

When both assembled boards pass 10.3, continue with `fab/ASSEMBLY_AND_TEST.md`. Its electrical tests come before the CM4 is plugged in.

---

## What could not be verified

| Point | Why | Where you will see the real answer |
|---|---|---|
| Every page after **NEXT** (BOM / CPL upload, parts list, placement preview, Quote & Order, cart, checkout): exact button and tab names; whether a row of the parts list gets a yellow mark; how the preview draws each part, where its red dot is and whether it shows an angle; whether it puts the origin of JLCPCB's footprint or the middle of its pads on the placement point, which matters for J1, J4, MK1 and MK2 (5.4); how it draws J6 (JLCPCB has a footprint record for the new connector, read live on 2026-11-20 and 2026-11-21, but its drawing was not seen) and the red LEDs D4 and D9, whose JLCPCB footprint numbers the pads the other way round; the entries of the "product description" list; on which page the shortage preference is shown and whether it can be changed for an order with assembly; whether the assembly remark can still be changed through **Edit Order** | login required; documented from JLCPCB's help articles of 9 and 23 Sep 2026: five of them were fetched again on 2026-11-20 and are unchanged, the others are as fetched on 2026-11-12 (which is which: row "help" of the table at the top). The shortage preference is in none of the articles fetched on 2026-11-20; its labels come from the public script of the order site (5.5) | on the pages themselves |
| The **Parts Manager** pages: where the menu entry is, the exact clicks on **Order Parts**, price and tax of the two parts there (step 2.3) | login required; documented from the help article (fetched 2026-11-12, not again) | Parts Manager |
| Stock and price of every part on the day you order | the figures are those of 2026-11-21, 09:57 UTC (alternates: 2026-11-20, unless section 2.4 says 2026-11-21); three lines lost most of their stock within eight days | `https://jlcpcb.com/partdetail/` with the C number, and the parts list page |
| What the form detects from the real `gerbers.zip` | the live quotes of 2026-11-12 were made with a neutral test Gerber of the same size, layer count and hole sizes, those of 2026-11-20 with the size typed in and no file; the real design has not been uploaded to JLCPCB by anyone | the line "Detected 4 layer board of ..." after the upload |
| The block **PCB Assembly** for this board: that the form changes 100 * 74 to 100 * 84 and accepts **PCBA Qty** 2 | seen on 2026-11-12 with the test file. On 2026-11-20 the block could be operated on JLCPCB's demo board only (80 x 70 mm); the option names and fee texts of section 4 were read there | the form after your upload |
| Whether JLCPCB puts the rails on the two 74 mm edges as requested, and what it then charges: 69.61 USD is the form price for a 110 x 74 mm board, but how and when the difference to the 47.64 USD of the form is collected is not documented | decided by JLCPCB's engineers in the review | review result and **Confirm Production file** |
| Whether JLCPCB's data preparation leaves the copper next to the holes without plating as it is. JLCPCB asks for 0.2 mm and the margin is small: the filled copper areas keep the 0.2 mm of the board's own design rule and no more, the ring pads at the two microphone holes start 0.21 mm from the hole (section 1) | done in JLCPCB's data preparation. Its capabilities page says that 0.2 mm of copper is removed around such a hole; no text that was read says how JLCPCB measures this distance or whether the customer is asked. KiCad's own check does not test the microphone ring against the hole of its own footprint (why, was not investigated), so the 0.21 mm rests on the dimensions of the land pattern and on a measurement in the Gerber files, not on that check | a question from JLCPCB, **Confirm Production file** (section 7.3), the delivered boards |
| The assembly fee lines of this very order: number of feeders, joints and X-ray pieces; whether a feeder is billed at 1.53 USD (list) or 1.50 USD (help text of the form) and a manual joint at 0.0164 or 0.02 USD; whether removing the rails is charged for 1 or 5 panels (1.70 or 2.90 USD); fee and extra time of **Board Cleaning: Caution for Special Parts**; whether the "special component fee" in the part record of the USB-C socket J1 (0.03 USD) is charged per piece, once or not at all, and on which line it appears; whether JLCPCB asks for a step stencil or a fixture | computed after the BOM upload and in the review; before login the lines show "-" | Quote & Order page and review result, before you pay |
| The checkout: whether **Review Before Payment** and the "$10 New User SMT Coupon" are offered for this order; which shipping methods are offered for an order with assembly (EuroPacket probably not); the tax lines of a (DDP) shipment (VAT base, number of 2 EUR handling-fee lines); the disbursement fee JLCPCB charges with DHL Express (DDP), between 0 and 15 EUR; whether the note on FedEx Express (DDP) means that this fee is waived in full; how long the review takes | checkout needs login and address; no tax line of any method is shown before it; JLCPCB's help texts disagree on whether an order with assembly can use Review Before Payment (section 7.1); JLCPCB says coupons "may also depend on the shipping address and payment method" and states no review time | checkout page, order status |
| The customs tariff number JLCPCB declares for assembled boards | it is on the invoice only; the duty is 0 % for all plausible numbers | invoice of the order |
| Surcharge of the "±10%" impedance option and of the smaller via sizes | read on 2026-11-12 at 100 x 74 mm only, not read again; not selected in this order | - |
| The new connector J6 and the alternates of section 2.4 | none of them was ordered or measured. The dimensions of the USB-A sockets come from single-page copies of the makers' drawings; four dimensions of the fitted Jing part and most of the Hroparts part are measured from the drawing, not dimensioned. JLCPCB's footprint record of J6 has the hole positions of the board, except that its two pin rows are 2.71 instead of 2.62 mm apart; where the 2.71 mm come from was not checked, and the record does not show that the Jing part fits (section 5.4). The effect of the more sensitive IM73D122 on the voice software was simulated, not tested; the two gain values of section 2.4 are arithmetic | the delivered boards; the maintainer |
| The solder paste on the delivered boards: whether JLCPCB cuts its stencil from the paste layer of `gerbers.zip` or from its own footprint library, how thick its stencil is, and how much solder the four spacers H5 to H8 get | not looked up. The paste volumes of section 1 are calculated for assumed stencil thicknesses of 0.10 and 0.12 mm; no board was soldered | the four spacer joints of the delivered boards (section 10.3); a proposal for a step stencil in the review |
| How long JLCPCB accepts complaints about the boards themselves | not in the research notes. For the parcel JLCPCB's shipping page says: damage within 7 days after receipt, loss within 60 days after dispatch | JLCPCB's terms |
| The inspection criteria of section 10 | no board has been built; written from the board file, JLCPCB's option texts, the makers' drawings and data sheets and general handling practice. The cathode mark of the LEDs is read from the KENTO data sheets and was not seen on a part. What the solder joint of a spacer looks like with the paste of this board is not known | the delivered boards |
