from __future__ import annotations

from bda.contracts.paramodel.shared.case_insensitive_enum import CaseInsensitiveEnum


class PrimaryTrafficTypeEnum(CaseInsensitiveEnum):
    ROAD = "road"


class TrafficLoadModelEnum(CaseInsensitiveEnum):
    HL93 = "HL-93"
    Pedestrian = "Pedestrian"


class WindExposureCategoryEnum(CaseInsensitiveEnum):
    CATEGORY_B = "Category B"
    CATEGORY_C = "Category C"
    CATEGORY_D = "Category D"


class GradientDefinitionTypeEnum(CaseInsensitiveEnum):
    CUSTOM = "custom"
    BY_ZONE = "by zone"


class DeckOverlayEnum(CaseInsensitiveEnum):
    ASPHALT = "asphalt"
    PLAIN = "plain"


class GradientZoneEnum(CaseInsensitiveEnum):
    ZONE_1 = "zone 1"
    ZONE_2 = "zone 2"
    ZONE_3 = "zone 3"
    ZONE_4 = "zone 4"


class AashtoLoadNatureEnum(CaseInsensitiveEnum):
    DC = "DC"
    DW = "DW"
    LL = "LL"
    PL = "PL"
    BR = "BR"
    CE = "CE"
    WS = "WS"
    WL = "WL"
    TU = "TU"
    TG = "TG"
    EQ = "EQ"
    PS = "PS"
    SE = "SE"
    SH = "SH"
    CR = "CR"
    CS = "CS"
