"""Part catalogue: one entry per distinct purchasable part.

key -> (Manufacturer, MPN, description, footprint)
The parts are the ones the JLCPCB assembly library had in stock on the day of the check (sourcing_jlc.json holds the
LCSC numbers, stock and prices); sourcing.py names the DigiKey second source of every line.
"""
R0402 = "Resistor_SMD:R_0402_1005Metric"
C0402 = "Capacitor_SMD:C_0402_1005Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"
LED0603 = "LED_SMD:LED_0603_1608Metric"
SOT23 = "Package_TO_SOT_SMD:SOT-23"
SOT236 = "Package_TO_SOT_SMD:SOT-23-6"


def _ohms(v):
    mult = {"k": 1e3, "M": 1e6}.get(v[-1])
    return float(v[:-1]) * mult if mult else float(v)


def _ucode(v):
    ohms = _ohms(v)
    if ohms == 0:
        return "0000"
    mant, exp = ohms, 0
    while mant >= 999.5:
        mant /= 10.0; exp += 1
    while mant < 99.95:
        mant *= 10.0; exp -= 1
    return "%d%s" % (round(mant), {-1: "J", -2: "K"}.get(exp, str(exp)))


PARTS = {
    "C_100n":  ("Samsung Electro-Mechanics", "CL05B104KO5NNNC", "CAP CER 100nF 16V X7R 0402", C0402),
    "C_1u":    ("Samsung Electro-Mechanics", "CL10B105KA8NNNC", "CAP CER 1uF 25V X7R 0603", C0603),
    "C_4u7":   ("Samsung Electro-Mechanics", "CL10A475KA8NQNC", "CAP CER 4.7uF 25V X5R 0603", C0603),
    "C_1u_35": ("Samsung Electro-Mechanics", "CL10A105KB8NNNC", "CAP CER 1uF 50V X5R 0603", C0603),
    "C_100n_50": ("Yageo", "CC0603KRX7R9BB104", "CAP CER 100nF 50V X7R 0603", C0603),
    "C_220n_50": ("Murata", "GRM188R71H224KAC4D", "CAP CER 220nF 50V X7R 0603", C0603),
    "C_10u_35": ("Samsung Electro-Mechanics", "CL31B106KBHNNNE", "CAP CER 10uF 50V X7R 1206", C1206),
    "C_22u":   ("Samsung Electro-Mechanics", "CL31A226KAHNNNE", "CAP CER 22uF 25V X5R 1206", C1206),
    "C_xtal":  ("FH (Guangdong Fenghua)", "0402CG150J500NT", "CAP CER 15pF 50V C0G 0402", C0402),
    "C_22p":   ("FH (Guangdong Fenghua)", "0402CG220J500NT", "CAP CER 22pF 50V C0G 0402", C0402),
    "C_10n":   ("Samsung Electro-Mechanics", "CL05B103KB5NNNC", "CAP CER 10nF 50V X7R 0402", C0402),
    "C_100u_poly": ("KEMET", "T520B107M006ATE040", "CAP POLYMER TANT 100uF 6.3V 40mOhm 3528",
                    "Capacitor_Tantalum_SMD:CP_EIA-3528-21_Kemet-B"),
    "L_6u8":   ("Sunltech", "SLO0630H6R8MTT", "IND 6.8uH 4.5A(rms) 8A(sat) 54mOhm shielded 7.1x6.6x3.0mm",
                "Inductor_SMD:L_Bourns_SRP7028A_7.3x6.6mm"),
    "Y_24M":   ("YXC", "X322524MOB4SI", "XTAL 24MHz 12pF 10ppm 3.2x2.5mm",
                "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm"),
    "U_PD":    ("Infineon", "CYPD3177-24LQXQT", "USB-C PD sink controller (EZ-PD BCR) QFN-24",
                "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.75x2.75mm"),
    "U_BUCK":  ("Texas Instruments", "LMR33640ADDAR", "Buck 3.8-36V 4A 400kHz HSOIC-8",
                "Package_SO:Texas_HSOP-8-1EP_3.9x4.9mm_P1.27mm_ThermalVias"),
    "U_HUB":   ("Microchip", "USB2514B-I/M2", "USB 2.0 hi-speed 4-port hub QFN-36",
                "Package_DFN_QFN:QFN-36-1EP_6x6mm_P0.5mm_EP3.7x3.7mm"),
    "U_SW":    ("Texas Instruments", "TPS2553DBVR", "Current-limited power switch, adj. 0.075-1.7A, EN active high, SOT-23-6", SOT236),
    "U_AMP":   ("Analog Devices", "MAX98357AETE+T", "I2S class-D mono amplifier 3.2W TQFN-16",
                "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm"),
    "U_PDM":   ("Analog Devices", "ADAU7002ACBZ-R7", "Stereo PDM to I2S converter WLCSP-8", "voxhub:ADAU7002_WLCSP-8_0.76x1.56mm_P0.4mm"),
    "MK_PDM":  ("Infineon", "IM69D130V01XTSA1", "MEMS microphone PDM 69dB SNR bottom port LLGA-5",
                "Sensor_Audio:Infineon_PG-LLGA-5-1"),
    "U_ZB":    ("RF-star", "RF-BM-2652P2", "CC2652P Zigbee/Thread module +20dBm, PCB antenna, 16.5x30mm",
                "voxhub:RFstar_RF-BM-2652P2"),
    "U_ESD":   ("STMicroelectronics", "USBLC6-2SC6", "USB ESD protection SOT-23-6", SOT236),
    "Q_P":     ("Alpha & Omega Semiconductor", "AO3401A", "MOSFET P-CH 30V 4A SOT-23", SOT23),
    "Q_N":     ("Nexperia", "2N7002,215", "MOSFET N-CH 60V 300mA SOT-23", SOT23),
    "D_TVS":   ("Littelfuse", "SMBJ22A", "TVS 22V 600W unidirectional SMB", "Diode_SMD:D_SMB"),
    "D_CC":    ("Littelfuse", "SD24C-01FTG", "ESD diode 24V bidirectional SOD-323", "Diode_SMD:D_SOD-323"),
    "D_Z10":   ("onsemi", "MM3Z10VT1G", "Zener 10V 300mW SOD-323", "Diode_SMD:D_SOD-323"),
    "LED_R":   ("Lite-On", "LTST-C191KRKT", "LED red 631nm 0603, 30mA", LED0603),
    "LED_G":   ("Wurth Elektronik", "150060VS75000", "LED green 570nm 0603, 30mA", LED0603),
    "LED_UG":  ("Hubei KENTO", "KT-0603G", "LED green 520nm 0603, 30mA (status, side B)", LED0603),
    "LED_UB":  ("Hubei KENTO", "KT-0603B", "LED blue 468nm 0603, 30mA (status, side B)", LED0603),
    "J_CM4":   ("Hirose", "DF40C-100DS-0.4V(51)", "CONN mezzanine 100pos 0.4mm receptacle (CM4 socket)", None),
    "J_USBC":  ("GCT", "USB4105-GF-A", "USB-C receptacle 16-pin USB 2.0, top mount",
                "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal"),
    "J_USBA":  ("Wurth Elektronik", "61400826021", "USB-A dual stacked receptacle THT",
                "Connector_USB:USB_A_Wuerth_61400826021_Horizontal_Stacked"),
    "J_SD":    ("Hirose", "DM3AT-SF-PEJM5", "microSD push-push socket", "Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5"),
    "J_SPK":   ("JST", "B2B-PH-K-S(LF)(SN)", "CONN header PH 2pos 2mm vertical THT",
                "Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical"),
    "J_DBG":   ("Wurth Elektronik", "61300311121", "Pin header 1x3 2.54mm (DNP)",
                "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"),
    "SW_MUTE": ("C&K", "JS202011JCQN", "Slide switch DPDT SMT vertical actuator",
                "Button_Switch_SMD:SW_DPDT_CK_JS202011JCQN"),
    "H_CM4":   ("Wurth Elektronik", "9774015151R", "SMT spacer M2.5 internal thread, 1.5mm",
                "Mounting_Wuerth:Mounting_Wuerth_WA-SMSI-M2.5_H1.5mm_9774015151"),
}


def res(v):
    return ("UNI-ROYAL (Uniroyal Electronics)", "0402WGF%sTCE" % _ucode(v), "RES %s 1%% 1/16W 0402" % v, R0402)
