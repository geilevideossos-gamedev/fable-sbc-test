# VoxHub CM4 carrier, revision A2 - ordering at JLCPCB, click by click

Applies to commit `6776424` (hardware revision A2, the board as rebuilt after the review) and the files in `fab/jlcpcb/`.
Order: 5 PCBs, 2 of them fully assembled on both sides, delivery to Austria. You do not solder anything.

Read the whole guide once before you start. Then work through sections 2 to 7 in order.

**Where the facts come from**

| Mark in this guide | Meaning |
|---|---|
| live | read on 2026-11-12 from JLCPCB's order form https://cart.jlcpcb.com/quote without login, or from JLCPCB's parts database. The form prices of the chosen configuration (3.5, 4.3, 8) were read at 09:05 and again at 10:06 UTC, all stock figures and part prices between 10:06 and 10:08 UTC |
| help | JLCPCB help-centre article as fetched on 2026-11-12. Everything after the button **NEXT** needs a login and was documented from these articles only |
| list | JLCPCB's assembly price list "PCB Assembly Cost: What Does the Price Include?", last updated 22 Oct 2026 |
| estimate | arithmetic from the above; the real figure appears on JLCPCB's pages before you pay |

Text in **bold** is a label exactly as it appears on the screen. Prices are in USD as JLCPCB shows them.
EUR values use the ECB reference rate of 2026-11-11 (the latest one published on 2026-11-12): 1 EUR = 1.1127 USD, 1 USD = 0.8987 EUR.

Directions on the board, used in the whole guide (the same as in `fab/ASSEMBLY_AND_TEST.md`): hold the board with the parts up
and the edge with the three connectors (USB-C, double USB-A, microSD) away from you. That edge is the **rear edge**, the opposite
edge is the **front edge**, left and right are as you see them. Positions are given as x / y in millimetres: x from the left
edge, y from the rear edge (the board is 100 x 74 mm).
JLCPCB calls the side with almost all parts **Top** and the other side **Bottom**; this guide uses the same words.

---

## 1. What is in `fab/jlcpcb`

| File | Content | Where it goes |
|---|---|---|
| `gerbers.zip` | 13 files: 4 copper layers (`voxhub-F_Cu.gtl`, `voxhub-In1_Cu.g1`, `voxhub-In2_Cu.g2`, `voxhub-B_Cu.gbl`), 2 solder mask, 2 solder paste, 2 silkscreen, the outline (`voxhub-Edge_Cuts.gm1`), 2 drill files (`voxhub-PTH.drl`, `voxhub-NPTH.drl`) | **Add gerber file** on the order form (section 3) |
| `bom_jlcpcb.csv` | parts list: 53 rows, one row per JLCPCB part number, 136 parts per board. Columns `Comment, Designator, Footprint, LCSC Part #`; `Comment` is JLCPCB's own name of the part | BOM upload (section 5) |
| `cpl_jlcpcb.csv` | position and rotation of the same 136 parts: 132 on the top side, 4 on the bottom side. Columns `Designator, Mid X, Mid Y, Layer, Rotation` | CPL upload (section 5) |
| `placement_report.csv` | one row per part: the rotation that was written into the CPL and how well JLCPCB's own footprint fits the pads of the board | not uploaded - it is your check list for the placement preview (section 5.4) |

Nothing needs editing. Upload the three files exactly as they are.
The counts and positions in this guide belong to the files generated on 2026-11-12 at 10:00 UTC (commit `6776424`). If the files in `fab/jlcpcb/` are newer than that, a count in sections 1, 5 or 8 may differ by a few; the procedure stays the same.

- Do not open the CSV files in a spreadsheet program and save them again. If you want to look at them, open a copy.
- Do not rename the files inside `gerbers.zip` and do not re-pack the archive.

Facts about the board that the form will ask for or show:

| Property | Value |
|---|---|
| Size | 100 x 74 mm, corners rounded |
| Layers | 4 |
| Small holes | 294 holes of 0.30 mm: 286 vias (pads 0.5 mm and 0.6 mm) and 8 thermal holes in one exposed pad. Five of the vias lie inside the exposed pads of U1, U4 and U10; no other via lies in or touches a pad (`hardware/outputs/via_in_pad.txt`) |
| Other holes | plated: 4 slots 0.6 mm wide, 2 x 0.75 mm, 8 x 0.92 mm, 3 x 1.0 mm, 4 x 2.3 mm; not plated: 2 x 0.65 mm, 2 x 0.8 mm (microphone sound ports), 3 x 0.99 mm, 4 x 2.7 mm, 4 x 3.7 mm |
| Copper to the board edge | 0.45 mm on all four layers, along the straight edges and around the four rounded corners (JLCPCB asks for 0.4 mm at an edge where a rail is scored off). Closer only at two shield pads of the microSD socket on the rear edge (0.37 mm) |
| Silkscreen | polarity marks and a few texts only; every line is 0.15 mm or wider, text is 1.0 mm high or more. There are **no reference designators** (R1, U4 ...) printed on the board; they exist only in the CPL file |

---

## 2. Before ordering: account and the parts that are short

### 2.1 Account

1. Open https://jlcpcb.com and click **Sign In** (top right). You can register a JLCPCB account or sign in with Google or Apple (the login page offers these three ways).
2. When you enter your address later, enter it as a private person: your name, no company name. JLCPCB decides from the name and the address whether the parcel is a private (B2C) or a business (B2B) import (help).

### 2.2 The thin parts today

Rule of this project: a BOM line with fewer than 200 pieces in JLCPCB's assembly stock is "thin".
`hardware/outputs/bom.csv` and `bom_summary.json` list three such lines; the live check gave the same numbers.

| Part | Designator | JLCPCB Part # | JLCPCB stock (live 2026-11-12, 10:08 UTC) | Needed for 2 boards | Unit price (live) |
|---|---|---|---|---|---|
| ADAU7002ACBZ-R7 (microphone interface IC) | U9 | C481886 | 104 | 2 | 3.9059 USD |
| RF-BM-2652P2 (Zigbee radio module) | U11 | C5440064 | 126 | 2 | 6.6325 USD |
| 61400826021 (stacked USB-A connector) | J6 | C5366339 | 116 | 2 | 2.7594 USD |

Every other line has more than 200 pieces. The next thinnest ones, for information: 9774015151R spacers (C5353804) 230, need 8;
IM69D130V01 microphones (C536262) 372, need 4 (427 at 08:51 UTC); CYPD3177-24LQXQT (C2952489) 806; DF40C-100DS-0.4V(51) (C597931) 1,047, need 4; USB2514B-I/M2 (C220679) 1,182 (1,683 at 08:51 UTC).
Stock moves during the day. Look at the three thin parts again on the day you order.

To see the stock of a part right now, open `https://jlcpcb.com/partdetail/C481886` (replace the C number).

### 2.3 Reserve the three thin parts first

JLCPCB lets you buy parts into a private stock that only your own assembly orders can use. Do this before anything else; it takes a few minutes.
(Source: help article "What is JLCPCB Parts Pre-order Service?", updated 9 Sep 2026. The pages themselves need a login and were not seen.)

1. Sign in. Open **Parts Manager**. It has three functions: **My Parts Lib**, **Order Parts**, **New parts request**.
2. Click **Order Parts**. Search for `C481886`. Enter quantity **3**. Add it to the cart.
3. Do the same for `C5440064` (quantity **3**) and `C5366339` (quantity **3**). Two pieces of each are needed, the third is a spare.
   The help article says: "In-stock extended parts can be pre-ordered, no minimum quantity required."
4. Pay within one hour. The article says the parts order stays in the cart for 1 hour and is cancelled after that.
5. Open **Parts Order History** and then **My Parts Lib**. For parts that were in stock the article says they are "shown in your own library immediately after you make the payment". Continue only when all three parts are listed with quantity 3.

What it costs: 3 x (3.9059 + 6.6325 + 2.7594) = 39.89 USD (estimate at today's library prices; the price shown on the **Order Parts** page and whether tax is added there could not be verified).
The parts stay at JLCPCB. They are never shipped to you ("the parts you store in JLCPCB can only be used for assembly orders").
When you place the board order, JLCPCB takes these parts automatically: "If there are enough pieces in 'My Parts' for the assembly order, the system will use 'My Parts' by default." (help article "How to use my own parts for PCB assembly order", fetched 2026-11-12).

### 2.4 If one of the three is gone

"Gone" means: stock 0, or less than 2. Do not place the board order with a missing part - an owner who does not solder cannot add it later.

| Part gone | What `hardware/outputs/bom.csv` names | What you do |
|---|---|---|
| 61400826021 (J6) | Jing Extension **907-112A1022D10200**, JLCPCB C29780026: same hole pattern within 0.12 mm, shell 0.26 mm taller, passes the enclosure window, no temperature range on its drawing. Live today: 2,959 in stock, 0.3638 USD, minimum 2. Second alternate: Korean Hroparts **U-A-28DD-Y-1**, C530601, identical pattern, +85 C; live today only 168 in stock | Use C29780026. On the parts list page (section 5.3) click the magnifier icon in the row of J6, search `C29780026`, select it. Add to the PCBA remark: "J6: C29780026 is used instead of C5366339 (same footprint)." |
| ADAU7002ACBZ-R7 (U9) | "ADAU7002ACBZ-RL (13 inch reel, JLCPCB C654434): same part. No other PDM-to-I2S converter exists at JLCPCB". Live today C654434: 0 in stock. Second source in the BOM: DigiKey 505-ADAU7002ACBZ-R7CT-ND (7,888 in stock on 2026-11-11, 2.66 USD) | There is no substitute. Use JLCPCB's Global Sourcing service (help article "How to use JLCPCB Global Sourcing Parts Service?") to let JLCPCB buy ADAU7002ACBZ-R7 from a distributor: review 1 to 3 business days, then "9-15 days" on one help page and "normally 9-20 business days" on another; it cannot be cancelled. Place the board order only when the part is listed in **My Parts Lib** |
| RF-BM-2652P2 (U11) | "no drop-in in stock: RF-star RF-BM-2652P4 (CC2652P7, same outline, other firmware build); Ebyte E72-2G4M20S1E needs another footprint". Not carried by DigiKey. Live today RF-BM-2652P4 (C5441193): 0 in stock | There is no substitute you can order today. Do not order the boards. Report it to the maintainer of this repository; the possible ways (JLCPCB **Pre-order** of C5440064 with a minimum quantity, or the P4 module with a different firmware file) need a decision |

---

## 3. The PCB form, option by option

Page: https://cart.jlcpcb.com/quote, tab **Standard PCB/PCBA**. You can fill in this page without being logged in.

Do these two things first, in this order:

1. Set the country. In the right column find **Shipping Estimate**, click the shipping method name, choose **Austria** in the country list (default: "United States Of America"), close the dialog. Do this first: when the country was changed later in a test, the page reset **Surface Finish** to "HASL(with lead)".
2. Click **Add gerber file** and choose `fab/jlcpcb/gerbers.zip`. Wait until the box shows the two board pictures and a line like "Detected 4 layer board of 74x100mm(2.913x3.937 inches)." (this is what the form showed for a test file of the same size). **Layers** and **Dimensions** are then filled in.

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
| **Material Type** | **FR4 TG135** | 0 USD. If "FR4 TG155" is selected here, you clicked a smaller via size by mistake (see 3.3) |
| **Surface Finish** | **ENIG** | flat gold pads; required for the 0.22 mm pads of U9 and for the 0.4 mm pitch connectors. Default is "HASL(with lead)" - change it |
| **Gold Thickness** (appears with ENIG) | **1 U"** | the standard thickness; 2 U" costs more and is not needed |

### 3.3 High-spec Options

| Option | Select | Why |
|---|---|---|
| **Outer Copper Weight** | **1 oz** | as designed |
| **Inner Copper Weight** | **0.5 oz** | as designed; the stack-up JLC04161H-3313 is the one for 0.5 oz inner copper |
| **Specify Layer Sequence** | **Yes**. A dialog **Layer Sequence** opens with four lists. Choose **L1(Top layer)** = `voxhub-F_Cu.gtl`, **L2(Inner layer1)** = `voxhub-In1_Cu.g1`, **L3(Inner layer2)** = `voxhub-In2_Cu.g2`, **L4(Bottom layer)** = `voxhub-B_Cu.gbl`, then **Confirm** | In1 is the ground plane directly under the USB tracks of the top layer; this removes any doubt about the order. Live: the lists show the file names of the uploaded archive; until you confirm, the row shows "This option is required." in red |
| **Specify Stackup** | **Yes**. A dialog **Layer Stackup** opens. Choose **JLC04161H-3313**, then **Confirm** | the board was designed for this layer structure (0.0994 mm prepreg between top layer and ground plane). 0.00 USD (live). The dialog notes "This is a special stackup, and it doesn't support economic PCB assembly" - correct, this order is Standard assembly |
| **Impedance Control** (appears after the stack-up is chosen) | **No requirement** | Naming the stack-up already makes JLCPCB build the exact layer structure of its own impedance calculator, in which the board's USB 2.0 pair (0.14 mm tracks, 0.16 mm gap) is 89.96 ohm; USB 2.0 accepts 76.5 to 103.5 ohm and the three USB runs are only 11 to 32 mm long. The paid choice "±10% (±5Ω if value≤50Ω)" (+33.08 USD, and it forces **Confirm Production file**) would add a guaranteed and tested impedance: JLCPCB's engineers adjust the track widths and need a table of the impedance tracks inside the Gerber archive - it does not give a different board |
| **Via Covering** | **Epoxy Filled & Capped** | The board has thermal vias inside the exposed pads of U1, U2, U4 and U10 (5 vias and 8 thermal holes; no other via touches a pad). The free choice "Plugged" does not close vias that sit inside pads; they stay open and can draw solder away from the part during soldering, and nobody can rework these prototypes. Filled and capped vias are flat and closed. +17.58 USD on the form (live; 17.55 for the 110 x 74 mm panel). Runner-up: **Plugged** at 0 USD |
| **Via Plating Method** | nothing to click. The page sets **Horizontal Electroless Copper Plating** by itself when "Epoxy Filled & Capped" is chosen and greys out the other two | +3.41 USD (live); it belongs to the filled vias |
| **Min via hole size/diameter** | **0.3mm/(0.4/0.45mm)** | all 294 small holes are 0.30 mm; this is the tier without surcharge. Do not click the smaller sizes even for a test: they switch on "FR4 TG155" (+3.49 USD) and "4-Wire Kelvin Test" (+17.03 USD), and both stay on when you go back |
| **Board Outline Tolerance** | **±0.2mm(Regular)** | default; "±0.1mm(Precision)" is greyed out as soon as PCB Assembly is on |
| **Confirm Production file** | **Yes**. A dialog opens ("please confirm within 48 hours ... Otherwise, your order will be automatically confirmed"). Tick **Do not confirm automatically**, then **Confirm** | +1.05 USD. You see JLCPCB's production data before the boards are made, and production waits for you (section 7) |
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

Right column, **Charge Details**. With the options above and PCB Assembly still off, the live form showed on 2026-11-12:

| Line | Amount |
|---|---|
| Special Offer | $8.00 |
| Via Covering | $17.46 |
| Surface Finish | $17.40 |
| Via Plating Method | $3.40 |
| Confirm Production file | $1.05 |
| **Calculated Price** | **$47.31** |

If you see other lines (**Material Type**, **4-Wire Kelvin Test**, **Min via hole size/diameter**, **Impedance Control**, **Stackup fee**), an option is set wrongly - go back through 3.2 to 3.4.
The badges "Save $30.00 / Save $20.00" next to **Coupons** are not a discount on this order (section 7).

---

## 4. The PCB Assembly block, option by option

Below the PCB options is the block **PCB Assembly**. Switch it on with the toggle at the right of its header. (It only opens after a Gerber upload.)

### 4.1 Main options

| Option | Select | Why |
|---|---|---|
| pictures **Assemble top side** / **Assemble bottom side** | both ticked | the board has parts on both sides (after choosing Both Sides below, both were ticked in the live form) |
| **PCBA Type** | **Standard** | "Economic" is greyed out: it cannot do two sides, the 0.4 mm pitch chip U9 or this stack-up |
| **Assembly Side** | **Both Sides** | 132 parts on top, 4 on the bottom (SW1, D7, D8, D9) |
| **PCBA Qty** | type **2** into the field next to the button "5" (hint: "Qty from 2 to 5") | 2 assembled boards; the other 3 are delivered without parts |
| **Edge Rails/Fiducials** | **Added by JLCPCB** (it is preselected). The form offers no choice of edges; the request for the edges is in the remarks (6.1 item 4 and 6.2 item 4) | Standard assembly needs 5 mm rails and fiducial marks; JLCPCB adds them. The page then says "The board size is modified to be 100mm*84mm due to adding two 5mm edge rails on the shorter sides." and **Dimensions** changes to 100 * 84: the form assumes rails on the two 100 mm edges. This board needs them on the two 74 mm edges (panel 110 x 74 mm): J6 overhangs the rear 100 mm edge by 2.5 mm, the radio module U11 is flush with the front 100 mm edge and small parts (C23, Q2, Q3, D7 to D10, MK1) sit 1 to 2 mm from it, so a rail scored off along these edges is a risk. JLCPCB's engineer changes the panel after reading the remark. Until then the form keeps showing 100 * 84 and the price for it (section 4.3) |
| **Confirm Parts Placement** | **Yes**. A dialog opens ("please confirm within 72 hours ... Otherwise, your order will be automatically confirmed"). Tick **Do not confirm automatically**, then **Confirm** | 0.45 USD (list). JLCPCB shows you its final placement drawing before it solders (section 7) |
| **Stencil Storage** | **No** | only useful for a repeat order within 3 months |
| **Fixture Storage** | **No** | same |
| **Parts Selection** | **By Customer (Self-Service)** | the BOM already carries the JLCPCB part number of every line; "By JLCPCB (Manual Match)" costs $10 and takes 1 to 2 business days |

### 4.2 Advanced Options of the assembly block (twelve lists)

| Option | Select | Why |
|---|---|---|
| **Bake Components** | **No** | the parts come from JLCPCB's own dry storage |
| **Photo Confirmation** | **No** | "$7.5 per order"; the placement is already checked with **Confirm Parts Placement**. Runner-up: **Yes** - JLCPCB then shows photos of the assembled boards in the order history and waits for your answer before shipping |
| **Board Cleaning** | **Caution for Special Parts** | MK1 and MK2 are bottom-port microphones with a sound hole through the board; washing would push liquid and flux into them (the silkscreen next to both says "MIC - NO WASH"). JLCPCB's own option text: "If your order contains sensitive components such as ... microphones ... we recommend that you select 'Caution for Special Parts' and clearly indicate the designators or part number in the remarks." Never choose "Dry-ice cleaning" or "Solvent-based Cleaning". The fee of this choice is not shown before login |
| **Conformal Coating (cleaning included)** | **No** | includes a wash - forbidden for the microphones |
| **Packaging** | **Antistatic bubble film** | default; the cardboard choices add weight and shipping cost |
| **Special stencil** | **No** | JLCPCB's engineers decide themselves whether a step stencil is needed and write to you (section 7) |
| **Depanel boards & edge rail before delivery** | **Yes** | JLCPCB removes the rails; otherwise the boards arrive with rails attached. "$1.4 service fee and $0.3 per panel", one more day |
| **Solder Paste** | **High temp.** | default, no charge |
| **Flying Probe Test** | **No** | needs other file formats |
| **Nitrogen reflow soldering** | **No** | not needed |
| **Function test** | **No** | not possible without the CM4 and firmware |
| **Assembly remark** | **Yes**, and paste the PCBA remark from section 6.2 | names the microphones, the rear edge and the polarity marks |

Below the lists: the box **I agree to the Terms and Conditions of JLCPCB assembly Service.** must be ticked (it is by default).
Leave the block **Stencil** ("Order together with PCB") below it switched off - the assembly stencil is part of the assembly fees and stays at JLCPCB.

### 4.3 Check the price box again, then NEXT

1. **PCB Build Time**: **3 days** with the tag "PCBA Only", $0.00, must be selected (the live form selected it by itself). Never choose "2-3 days" ($66.20).
2. **Charge Details** in the live form on 2026-11-12 with everything above:

   | Line | Amount |
   |---|---|
   | Special Offer | $8.00 |
   | Via Covering | $17.58 |
   | Surface Finish | $17.60 |
   | Via Plating Method | $3.41 |
   | Confirm Production file | $1.05 |
   | **Calculated Price** (Web Price) | **$47.64** |

   The lines under **Standard PCBA Price** (Components, Feeders Loading fee, SMT Assembly, Hand-soldering labor fee, Manual Assembly) show "-" at this point; they are filled in after the parts list. "Desktop Price: From $45.64" next to it is the price in JLCPCB's desktop program; ignore it.

   $47.64 is the price for rails on the 100 mm edges. For the panel that the remarks ask for (110 x 74 mm) the same form, with the same options and the size typed in by hand, showed $69.61 on 2026-11-12: Engineering fee $25.00, Board $5.10, Via Covering $17.55, Surface Finish $17.50, Via Plating Method $3.41, Confirm Production file $1.05. The size no longer falls under "Special Offer". You cannot select this on the form. Expect the difference of about 22 USD to appear when JLCPCB has reviewed the order (section 7.2).
3. Scroll up once more and check that **Surface Finish** is still **ENIG**.
4. Click **NEXT** (the button replaces "SAVE TO CART" when PCB Assembly is on). The login page appears; sign in.

---

## 5. BOM / CPL upload, parts list, placement preview

Everything in this section is behind the login. The labels are taken from JLCPCB's help articles (all updated 9 Sep 2026); the pages themselves were not seen. If a button is named slightly differently, use the one with the same meaning.

### 5.1 Board views

1. JLCPCB shows the top and the bottom of the board. Top: the text "VoxHub CM4  rev A2". Bottom: the texts "VoxHub CM4 rev A2 - this side faces the top cover", "MUTE", "USB-C PD 9-20V" and twice "MIC - NO WASH".
2. Click **Next**.

### 5.2 Upload

1. BOM file: `fab/jlcpcb/bom_jlcpcb.csv`. CPL file: `fab/jlcpcb/cpl_jlcpcb.csv`.
2. Click **Process BOM&CPL**.
3. If the message "Inconsistent Reference Designators Between BOM and CPL" appears: do **not** click **Continue**. Both files contain the same 136 designators; the message means a wrong file was uploaded. Upload again.
4. If "Parameter Error", "The Uploaded File Format Is Incorrect" or "File Processing Failed" appears: try another browser or a private window (JLCPCB's own advice). Do not edit the files.

### 5.3 The parts list page ("Matched Parts")

The page lists the 53 rows of the BOM with the part JLCPCB matched to each. **Only rows with a ticked check box are placed and paid for.** At the end every one of the 53 rows must be ticked.

| What you see | What it means | What you do |
|---|---|---|
| row ticked, JLCPCB part number equals the number in column `LCSC Part #` of `bom_jlcpcb.csv` | matched, in stock | nothing |
| **yellow exclamation mark**, row not ticked | JLCPCB wants your confirmation; hover over the mark to read why (for example: the matched part name is not literally the BOM text, or the package differs from the footprint name). None is expected for this BOM: every part number stands in one row only and the column `Comment` is JLCPCB's own part name. The footprint names are KiCad's, so a package warning cannot be ruled out | compare the JLCPCB part number in the row with the C number in `bom_jlcpcb.csv`. If equal, tick the row |
| **Shortfall** | JLCPCB's stock is lower than the quantity needed. Needed = 2 x parts per board plus a loss allowance, and at least a minimum quantity (for example 20 pieces for a 0402 resistor). Today no line is short | for J6 see section 2.4. For any other line: stop, do not order, report the part to the maintainer |
| **No Part Selected** / listed under unmatched components | nothing was matched | click **Search**, enter the C number from `bom_jlcpcb.csv`, select the part, tick the row |
| the row of U9, U11 or J6 | should show that the pieces come from your private stock (section 2.3) | if it shows a shortfall although **My Parts Lib** holds 3 pieces, stop and ask JLCPCB's support chat |
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

When all 53 rows are ticked, click **Next**.

### 5.4 The placement preview ("Component Placements")

JLCPCB draws every part on its pads, top view and bottom view. In its drawing a **red dot** marks the orientation mark of an IC, and "+" / "-" mark the anode / cathode of diodes and the plus terminal of polarised capacitors (help: "there will be a dot on the component itself, and there will also be a dot on the PCB (silkscreen), when they match, that means the component is placed correctly").

How to use `fab/jlcpcb/placement_report.csv` (open a copy):

- Column **Status**: 135 rows say `ok`. One row says `check`: **J6**, because JLCPCB's library has no footprint drawing for this connector. J6 may be drawn as a plain box, in the wrong place, or not at all. That is expected (see the table below).
- Column **JLCPCB rotation** is the angle that is in the CPL file. If the preview shows an angle per part, it must be this value.
- Column **Worst pad mismatch mm** is how far JLCPCB's footprint and the board's pads differ at the worst pad (largest value: 0.36 mm for C38 / C41). In the preview every part must sit on its pads, not beside them.

The marks on the board are white silkscreen:

- **filled triangle** or **filled dot** next to a pad = pin 1 (ball A1) of that part;
- **bracket with three sides** around one end of a two-pin part = that end is the **cathode** of a diode or LED, or the **plus** terminal of C38 / C41.

Check every row of the following tables in the preview. "Towards the rear edge" and so on are the board directions defined at the top of this guide. Only four parts are on the bottom side: SW1, D7, D8, D9. The bottom view is a mirror image: there left and right are swapped, front edge and rear edge are not.
JLCPCB calls its red dot "a marking only", not pin 1. If a red dot is not where the table says, treat the part as "looks rotated" (procedure after the tables) - it does not have to be an error.

**ICs, module, microphones, crystal (all on the top side)**

| Part | What it is | x / y (mm) | CPL rotation | Mark on the board | In the preview |
|---|---|---|---|---|---|
| U1 | CYPD3177-24LQXQT, QFN-24 | 19.5 / 16.6 | 90 | four corner brackets; triangle outside the side that faces the front edge, at its left end | red dot at the front-left corner |
| U2 | LMR33640ADDAR, 8 pins and a large centre pad | 8.5 / 25.5 | 270 | a line along the left and the right side; triangle right of the pin at the right end of the row that faces the rear edge | red dot at that pin (rear-right corner) |
| U3 | TPS2553DBVR, SOT-23-6 | 68.5 / 9.0 | 180 | triangle at the corner that is left and towards the rear edge | red dot at that corner |
| U4 | USB2514B-I/M2, QFN-36 | 33.5 / 26.5 | 180 | four corner brackets; triangle outside the side that faces the rear edge, at its right end | red dot at the rear-right corner |
| U5 | TPS2553DBVR, SOT-23-6 | 45.8 / 10.5 | 270 | triangle at the corner that is left and towards the front edge | red dot at that corner |
| U6 | TPS2553DBVR, SOT-23-6 | 45.8 / 4.0 | 270 | triangle at the corner that is left and towards the front edge | red dot at that corner |
| U7 | USBLC6-2SC6, SOT-23-6 | 35.25 / 18.6 | 180 | triangle at the corner that is right and towards the rear edge | red dot at that corner |
| U8 | USBLC6-2SC6, SOT-23-6 | 31.75 / 17.8 | 180 | triangle at the corner that is right and towards the rear edge | red dot at that corner |
| U9 | ADAU7002ACBZ-R7, 8 solder balls, 0.76 x 1.56 mm | 40.0 / 61.0 | 270 | one small dot (0.3 mm), left of the part at the end towards the rear edge. No outline | red dot at that corner; long side of the chip points from rear edge to front edge |
| U10 | MAX98357AETE+T, TQFN-16 | 9.0 / 49.0 | 270 | four corner brackets; triangle left of the part, at the end towards the rear edge | red dot at the rear-left corner |
| U11 | RF-BM-2652P2 radio module, 16.5 x 30 mm | 21.5 / 56.5 | 180 | line across the module end that faces the rear edge; dot (0.5 mm) right of the last pad of the right-hand pad row, at x 31.3 / y 62.0 | the end without pads (antenna) lies on the front edge of the board; pin 1 at the dot |
| MK1 | IM69D130V01 microphone | 9.4 / 70.2 | 90 | rectangle around the part; small triangle outside its corner that is left and towards the rear edge; the round sound-hole pad is in the right half | red dot at the triangle corner; the round port of the part over the hole |
| MK2 | IM69D130V01 microphone | 91.9 / 10.0 | 90 | same as MK1 | same as MK1 |
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
| D4 | red LED | top | 17.53 / 21.35 | 0 | left | "-" at that end |
| D5 | MM3Z10VT1G Zener diode | top | 13.7 / 12.15 | 270 | towards the rear edge | "-" at that end |
| D6 | green LED | top | 13.21 / 23.6 | 270 | towards the rear edge | "-" at that end |
| D10 | green LED | top | 84.4 / 72.2 | 0 | left | "-" at that end |
| D7 | green LED | **bottom** | 34.0 / 71.2 | 90 | towards the front edge | "-" at that end |
| D8 | blue LED | **bottom** | 38.6 / 71.2 | 90 | towards the front edge | "-" at that end |
| D9 | red LED | **bottom** | 43.2 / 71.2 | 90 | towards the front edge | "-" at that end |

**Connectors, switch, spacers**

| Part | What it is | Side | x / y (mm) | CPL rotation | Mark on the board | In the preview |
|---|---|---|---|---|---|---|
| J1 | USB-C socket USB4105-GF-A | top | 13.0 / 5.0 | 180 | a short line left and right of the body | opening at the rear edge, the row of small pads towards the board |
| J2 | CM4 socket DF40C-100DS-0.4V(51), 100 pins | top | 74.0 / 65.0 | 0 | a bracket at each short end; small open triangle outside the left end of the pad row that faces the front edge | the part covers both pad rows. It is symmetric: turned by 180 degrees it is the same |
| J3 | CM4 socket, same part | top | 74.0 / 31.0 | 0 | same as J2 | same as J2 |
| J4 | microSD socket DM3AT-SF-PEJM5 | top | 56.1 / 8.9 | 180 | lines along the sides of the body | card slot opens at the rear edge, the row of contact pads towards the front edge |
| J6 | stacked USB-A socket 61400826021, **through-hole, soldered by hand** | top | 35.25 / 10.6 | 180 | a line along the body side that faces the front edge; 8 pin holes in two rows, 4 large holes for the shell; the square pad (pin 1) is the right-hand hole of the row nearer the front edge | **no JLCPCB footprint drawing**: a box, a wrong position or nothing may be shown. The real part fits its 12 holes in one way only: both USB openings face outward and the body overhangs the rear edge by 2.5 mm |
| J7 | speaker socket B2B-PH-K-S (JST PH, 2 pins), **through-hole, soldered by hand** | top | 4.2 / 57.5 | 270 | outline of the housing, an L-shaped corner mark at its front-left corner, text "SPK" to the right | the part sits on both holes; pin 1 is the hole nearer the front edge; the wider part of the housing (2.9 mm from the pins) points right, towards "SPK" |
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

1. The page shows the complete price list of the assembly. Compare it with section 8. The number of feeder lines should be near 51, X-ray 2 pieces.
2. Choose a **product description** (help: "you need to select the product description and then save it to the cart"). Take the entry that fits a consumer electronics / smart-home device best. The list itself could not be retrieved.
3. Do not select the SMT expedite option ("USD 47.83 per day").
4. If the page offers a shortage preference, leave **Require Full Quantity**.
5. Click **Save to Cart**.

---

## 6. Remarks to paste

### 6.1 PCB Remark (section 3.4)

```
1. Via Covering = Epoxy Filled & Capped: please fill and cap ALL 0.30 mm holes (294 holes: 286 vias and 8 thermal holes that are drawn as pads inside one exposed pad). 13 of them are via-in-pad inside the exposed pads of four ICs - fill and cap these as well.
2. All holes of 0.60 mm and larger are component or mounting holes and must stay open.
3. The two non-plated 0.80 mm holes at X110.18 Y-130.20 and X192.68 Y-70.00 (Gerber coordinates, mm) are sound ports of MEMS microphones: keep them open, no solder mask ink, no resin.
4. Edge rails for the assembly: please add them to the two 74 mm edges (panel 110 x 74 mm), NOT to the two 100 mm edges. Connectors overhang one 100 mm edge and a module ends flush with the other. Copper keeps 0.45 mm from both 74 mm edges.
5. Stack-up JLC04161H-3313 as selected. No impedance test required.
```

### 6.2 Assembly remark (section 4.2)

```
1. MK1 and MK2 (C536262, IM69D130V01) are bottom-port MEMS microphones. Each has a 0.8 mm sound hole through the PCB; the bottom silkscreen says "MIC - NO WASH" next to it. Board Cleaning = Caution for Special Parts: no washing, no solvent, no dry ice, no conformal coating, no liquid or flux into these two holes, no compressed air into them.
2. The silkscreen carries no reference designators (they are in the CPL only). Polarity marks on the silkscreen: filled triangle or dot = pin 1 / A1 (ICs, module U11, microphones, transistors). Three-sided bracket around one end of a two-pin part = cathode of D1-D10, plus terminal of C38 and C41.
3. If a CPL rotation disagrees with the silkscreen mark, the silkscreen is right. Please send the placement for my confirmation before assembly.
4. EDGE RAILS - REQUEST: please add the 5 mm edge rails to the two 74 mm edges (panel 110 x 74 mm), NOT to the two 100 mm edges. Reason: J6 (stacked USB-A, through-hole) overhangs one 100 mm edge by 2.5 mm, J1 (USB-C) and J4 (microSD) end at the same edge; U11 ends flush with the other 100 mm edge and small parts sit 1 to 2 mm from it. The two 74 mm edges have no overhanging parts and copper keeps 0.45 mm from them. I accept the price difference for the larger panel.
5. J6 (C5366339) and J7 (C131337) are through-hole parts for hand soldering. J6: USB openings face outward over the board edge, body flat on the board. J7: follow the silkscreen outline.
6. Not populated on purpose: C13, J5, J8 (bare pads), JP1 (solder jumper), TP1-TP3 (test pads).
7. Please do not replace any part without asking me.
```

If a remark field does not take the whole text, keep the items in the order given and drop from the end - but never drop item 4 of either remark (the edge rails).

---

## 7. Payment, "Review Before Payment", confirmation e-mails

### 7.1 Cart and checkout (help; pages not seen)

1. Open the cart, expand the order and check: PCB Qty 5, PCBA Qty 2, ENIG, JLC04161H-3313, Epoxy Filled & Capped.
2. Click **Secure Checkout**.
3. Enter the delivery address as a private person, no company name.
4. Shipping method: **DHL Express (DDP)**. Live price for Austria on 2026-11-12: $23.52 for a parcel up to 0.5 kg ($26.97 above 0.5 kg), 2-4 business days. It costs the same as plain "DHL Express". With (DDP) JLCPCB collects the import VAT, the carrier's fee and the EU handling fee at checkout, and nothing is paid at the door.
5. The checkout now shows the tax lines. Expect about 20 % of goods plus shipping as VAT and about 19 EUR of fees (section 8). These lines could not be retrieved in advance.
6. Coupon: the page lists the coupons your account can use. One coupon per order. A new account normally has a "$10 New User SMT Coupon"; select it if it is offered.
7. Payment method: select **Review Before Payment**.
8. Submit the order. You do not pay now.

If the checkout does not offer **Review Before Payment**, pay in the normal way. The review then happens after payment, and a fee that changes in the review arrives as a separate payment request; the order stands still until it is paid.

### 7.2 What "Review Before Payment" does (help article updated 23 Sep 2026)

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
| **Confirm Production file** (the PCB data JLCPCB will manufacture) | when the production file is ready; you have 48 hours, and with "Do not confirm automatically" it waits for you | 1. Size 100 x 74 mm plus the rails, and the rails are on the two 74 mm edges (panel 110 x 74 mm). 2. Four copper layers; layer 2 is an almost solid plane. 3. Stack-up JLC04161H-3313. 4. The two 0.8 mm holes under the microphones exist (x 10.2 / y 70.2 and x 92.7 / y 10.0). 5. The four slots of the USB-C socket and the four corner holes exist. 6. Both "MIC - NO WASH" texts are there. 7. No order number was added to the board | confirm if all seven points are right. If the rails are on the 100 mm edges, do not confirm; answer "please move the edge rails to the two 74 mm edges as requested in the remarks". If the engineers changed something you do not understand (track widths, removed pads, moved holes), do not confirm either; ask them what and why, and ask the maintainer |
| **Confirm Parts Placement** (JLCPCB's placement drawing after its own corrections) | some hours after the order is confirmed; you have 72 hours, and with "Do not confirm automatically" it waits for you | go through the tables of section 5.4 once more, top and bottom. JLCPCB: "For SMD parts, please check the placement and polarity in 2D production file. For through-hole parts, please check the placement in 3D production file." Check J6 and J7 in the 3D file: J6 openings outward, both on their holes. Count: 132 parts top, 4 bottom, nothing on C13, J5, J8, JP1, TP1 to TP3 | confirm if everything matches. Otherwise answer with the designator and what is wrong |
| question about a part: unclear polarity, footprint mismatch, parts too close | any time during data preparation | the designator they name, in section 5.4 | answer the same day. The standard answer for polarity is "follow the silkscreen mark" |
| proposal for a **step stencil** with a price | during review | - | accept it. The board mixes 0.4 mm pitch parts (U9, J2, J3) with large parts; JLCPCB refunds the fee if the stencil later turns out to be unnecessary (help) |
| price difference for the 110 x 74 mm panel, or a request for a **fixture**, with a price | during review | - | accept it. The panel difference (about 22 USD) is in the "expected" column of section 8, the fixture in the "high" column |
| a message that the rails stay on the 100 mm edges | during review | - | do not accept; repeat item 4 of the assembly remark. If JLCPCB insists, ask the maintainer before you confirm anything |
| a supplement after you have paid | rare with Review Before Payment | the reason given | pay it only if the reason is in this guide; otherwise ask |
| tax or duty demand from DHL at delivery | delivery | - | with a (DDP) shipment do not pay. JLCPCB: "If customer who has prepaid tax (VAT) receives the tax payment notice from the logistics supplier, please refuse to pay and contact us." |

---

## 8. Cost estimate

All amounts in USD unless marked. Date of all prices: 2026-11-12. "Low" assumes everything goes as planned, the new-customer coupon applies and JLCPCB does not charge for the larger panel; "high" adds every supplement that JLCPCB's review can plausibly ask for.

| Line | Low | Expected | High | Source and assumption |
|---|---|---|---|---|
| PCB, 5 pieces, ENIG, JLC04161H-3313, epoxy filled and capped vias, panel 110 x 74 mm (rails on the 74 mm edges) | 47.64 | **69.61** | 69.61 | live quote, 10:06 UTC. 69.61 is what the form shows for 110 x 74 mm with the options of section 3 when the size is typed in by hand: 25.00 Engineering fee + 5.10 Board + 17.50 Surface Finish + 17.55 Via Covering + 3.41 Via Plating Method + 1.05 Confirm Production file. 47.64 is what the form shows during the order (rails on the 100 mm edges, 100 x 84 mm: 8.00 + 17.60 + 17.58 + 3.41 + 1.05); low: the difference is not charged |
| Assembly setup, both sides | 51.12 | **51.12** | 51.12 | list |
| Stencil, both sides | 16.42 | **16.42** | 16.42 | list |
| SMT joints at 0.0016 | 2.08 | **2.08** | 2.40 | list; 649 SMD pads per board in the board file (637 top, 12 bottom) x 2 = 1,298. High: 1,500 if JLCPCB counts differently |
| Feeder loading at 1.53 per part type | 78.03 | **78.03** | 81.09 | list; `bom_jlcpcb.csv` has 53 rows = 53 part numbers, 51 of them machine-placed and 2 hand-soldered (J6, J7): 51 x 1.53. High: 53 x 1.53 if the two hand-soldered parts are charged too |
| Hand-soldering labor, per order | 3.58 | **3.58** | 3.58 | list |
| Manual assembly at 0.0164 per joint | 0.46 | **0.46** | 0.59 | list; J6 has 12 joints (8 pins, 4 shell posts), J7 has 2: 14 x 2 boards = 28. High: 36 if the 4 shell posts of the USB-C socket J1 are hand-soldered too |
| X-ray at 1.64 per piece (0.82 from 11 pieces) | 3.28 | **3.28** | 9.84 | list; only ADAU7002ACBZ-R7 carries JLCPCB's X-ray flag (live): 2 pieces. High: all six leadless parts per board (U1, U4, U9, U10, MK1, MK2) = 12 x 0.82 |
| Packing | 0.50 | **0.50** | 0.50 | list |
| Confirm Parts Placement | 0.45 | **0.45** | 0.45 | list |
| Depanel boards & edge rail before delivery | 1.70 | **2.90** | 2.90 | form text "$1.4 service fee and $0.3 per panel": 1 panel or 5 panels - JLCPCB's count is not known |
| Board Cleaning "Caution for Special Parts" | 0 | **0** | 0 | fee not shown before login - assumed 0 |
| Fixture, 2 pieces | 0 | **0** | 16.42 | list; only if the engineers ask for a carrier |
| Step stencil | 0 | **0** | 61.79 | form text: $0.008 per pin + $9.4 + $47.2 labour, with 649 pins; only if the engineers recommend it |
| Exchange-rate drift of the listed assembly fees | 0 | **0** | 7.41 | 3 % of the fee lines above; the list says prices "may vary slightly due to exchange rate fluctuations" |
| Parts for 2 boards, with one spare each of the three thin parts | 101.29 | **103.21** | 129.01 | live prices of all 53 parts (10:06 UTC): 89.91 with JLCPCB's minimum and loss quantities (87.99 if only the minimum quantities are billed), plus 13.30 for the three spares of step 2.3. High: expected + 25 % for a substitute, a sourced part or price changes |
| Coupon | -10.00 | **0** | 0 | "$10 New User SMT Coupon", one coupon per order, not guaranteed |
| **Goods total** | **296.55** | **331.64** | **453.13** | |
| Shipping DHL Express (DDP) to Austria | 23.52 | **23.52** | 26.97 | live; parcel up to 0.5 kg, high: 0.5 to 1 kg. JLCPCB's weight for the 5 PCBs alone: 0.26 kg; with the parts of two boards and packing about 0.35 to 0.45 kg (estimate) |
| Austrian import VAT, 20 % of goods + shipping | 64.01 | **71.03** | 96.02 | estimate; EU customs duty for printed circuits and electronic assemblies is 0 % |
| Import handling: carrier's disbursement fee + EU "Union Handling Fee" | 4.45 | **21.14** | 26.71 | expected: 15 EUR (DHL Austria minimum) + 2 declaration lines x 2 EUR. Low: fee waived by JLCPCB ("may be discounted"), 2 x 2 EUR. High: 18 EUR + 3 x 2 EUR |
| **Total, USD** | **388.53** | **447.33** | **602.83** | |
| **Total, EUR** | **349.17** | **402.02** | **541.76** | x 0.8987 |

Notes on the table:

- 39.89 USD of the parts line (3 pieces each of the three thin parts) is paid earlier, in step 2.3. The rest is one payment after the review.
- The largest part lines for 2 boards: RF-BM-2652P2 13.27, the four microphones 12.56, ADAU7002ACBZ-R7 7.81, LMR33640ADDAR 5.81, USB-A socket 5.52, USB2514B 4.82, the eight spacers 4.49, the four CM4 sockets 3.87 USD.
- About 146 USD of the goods are fixed assembly fees (setup 51.12, stencil 16.42, feeders 78.03) that do not depend on the number of boards.
- If you choose the runner-up **Photo Confirmation: Yes**, add 7.50 USD.
- The goods value is above 150 EUR. The order is therefore not handled under the simplified IOSS scheme; VAT is collected by JLCPCB at checkout because of the (DDP) shipping method.
- Paying in EUR: JLCPCB converts at 0.9000 EUR per USD today (ECB: 0.8987). Your bank or PayPal may add a conversion fee.

---

## 9. Delivery time

| Stage | Time | Source |
|---|---|---|
| Review before payment | not stated by JLCPCB | - |
| PCB production, option "3 days PCBA Only" (also offered with filled vias) | 3 days | live |
| SMT assembly | "over 90% of PCB assembly orders complete the entire SMT process within 24-48 hours after PCB fabrication is finished" | help |
| Through-hole parts J6, J7 | 1 more day | help |
| Removing the rails | 1 more day | form text |
| JLCPCB creates a library footprint for J6 | "typically completed within 48 hours"; runs in parallel with PCB production | help |
| Your two confirmations and any question | the clock stops until you answer | help |
| DHL Express to Austria | 2-4 business days | live |

Estimate: **9 to 13 calendar days from payment to delivery** if you answer every message on the same day; the review before payment comes on top. Each day a confirmation waits adds a day. Parcels that reach JLCPCB's shipping centre after 11 am on a Saturday leave on Monday.

---

## 10. Incoming inspection - before anything is plugged in

The parcel contains 5 boards: **2 assembled boards and 3 boards without parts** (called "empty boards" below).
Pictures of the design to compare with: `hardware/outputs/render_top.png` and `hardware/outputs/render_bottom.png`.

### 10.1 Parcel and handling

1. Look at the box before you accept it. If it is crushed or wet, photograph it before opening.
2. Pay nothing at the door (section 7.3, last row).
3. Before touching a board, touch an earthed metal object (for example the bare metal of a radiator). Hold boards by the edges. Lay them on the antistatic film they came in.
4. Do not blow into, poke or wash the two small holes in opposite corners of the board, and do not press on the two small metal cans above them. They are the microphones and their sound ports.

### 10.2 The 3 empty boards

| Check | Good |
|---|---|
| Count and colour | 3 boards, green, white print, gold pads |
| Size | 100 x 74 mm, thickness about 1.6 mm (1.44 to 1.76 mm is within JLCPCB's tolerance) |
| Edges | the rails are gone. Small rough spots on the two 74 mm edges (left and right), where the rails were broken off, are normal: JLCPCB separates by hand and does not grind the edges |
| Text, top | "VoxHub CM4  rev A2", "SPK", "J5: GND TX RX", and "5V", "3V3", "GND" at the three test pads |
| Text, bottom | "VoxHub CM4 rev A2 - this side faces the top cover", the address of this repository, "MUTE", "USB-C PD 9-20V", twice "MIC - NO WASH". No order number anywhere |
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
| Bottom side | slide switch SW1 next to "MUTE"; three LEDs D7, D8, D9 in a row near the front edge; nothing else |
| Empty on purpose | C13, J5 (3 holes), J8 (6 pads, 3 holes), JP1, the three test pads TP1 to TP3 - compare with an empty board |
| J6 (USB-A) | sits flat on the board, not tilted; all 12 pins are soldered on the bottom side; both openings are free |
| J7 (speaker socket) | sits flat; 2 pins soldered on the bottom side |
| J2, J3 (CM4 sockets) | no solder between neighbouring contacts (0.4 mm apart), no bent contact, nothing inside the socket |
| U11 (radio module) | every half-round pad along its two long sides has solder; the module lies flat |
| U1, U2, U4, U10 | no solder bridge between pins; the part lies flat and is not shifted |
| LEDs and diodes | the cathode mark of each part (a green or coloured mark on LEDs, a bar on diodes) is at the closed end of the white bracket |
| C38, C41 | the bar on the capacitor body (plus) is at the closed end of the bracket |
| Microphone holes, seen from the bottom | open and round; no solder, flux or dirt in them |
| Spacers H5 to H8 | stand upright; the thread is clean |
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
| Every page after **NEXT** (BOM / CPL upload, parts list, placement preview, Quote & Order, cart, checkout): exact button and tab names; whether a row of the parts list gets a yellow mark; how the preview draws each part, where its red dot is and whether it shows an angle; what it shows for J6 (no JLCPCB footprint record, confirmed live); the entries of the "product description" list; where the shortage preference is shown; whether the assembly remark can still be changed through **Edit Order** | login required; documented from JLCPCB's help articles of 9 and 23 Sep 2026 | on the pages themselves |
| The **Parts Manager** pages: where the menu entry is, the exact clicks on **Order Parts**, price and tax of the three parts there (step 2.3) | login required; documented from the help article | Parts Manager |
| What the form detects from the real `gerbers.zip` | all live quotes of 2026-11-12 were made with a neutral test Gerber of the same size, layer count and hole sizes, or with the size typed in; the real design has not been uploaded to JLCPCB by anyone | the line "Detected 4 layer board of ..." after the upload |
| Whether JLCPCB puts the rails on the two 74 mm edges as requested, and what it then charges: 69.61 USD is the form price for a 110 x 74 mm board, but how and when the difference to the 47.64 USD of the form is collected is not documented | decided by JLCPCB's engineers in the review | review result and **Confirm Production file** |
| The assembly fee lines of this very order: number of feeders, joints and X-ray pieces; whether removing the rails is charged for 1 or 5 panels (1.70 or 2.90 USD); fee and extra time of **Board Cleaning: Caution for Special Parts**; whether JLCPCB asks for a step stencil or a fixture | computed after the BOM upload and in the review; the cleaning fee is not shown before login; the two research notes differ on the panel count | Quote & Order page and review result, before you pay |
| The checkout: whether **Review Before Payment** and the "$10 New User SMT Coupon" are offered for this order; the tax lines of a (DDP) shipment (VAT base, disbursement fee, number of 2 EUR handling-fee lines); how long the review takes | checkout needs login and address; JLCPCB says coupons "may also depend on the shipping address and payment method" and states no review time | checkout page, order status |
| The customs tariff number JLCPCB declares for assembled boards | it is on the invoice only; the duty is 0 % for all plausible numbers | invoice of the order |
| Surcharge of the "±10%" impedance option and of the smaller via sizes at the panel size | measured at 100 x 74 mm only; not selected in this order | - |
| How long JLCPCB accepts complaints after delivery | not in the research notes | JLCPCB's terms |
| The inspection criteria of section 10 | no board has been built; written from the board file, JLCPCB's option texts and general handling practice | the delivered boards |
