from pint import UnitRegistry
from pint.facets.plain.quantity import PlainQuantity

def _quantity_repr(self):
    return f"{self:.3g~P}"

PlainQuantity.__repr__ = _quantity_repr

ureg = UnitRegistry()
ureg.formatter.default_format = "~P"


# --- force ---
N = ureg.newton
kN = ureg.kilonewton
MN = ureg.meganewton

# --- pressure ---
Pa = ureg.pascal
kPa = ureg.kilopascal
MPa = ureg.megapascal
GPa = ureg.gigapascal

# --- length ---
m = ureg.meter
mm = ureg.millimeter
cm = ureg.centimeter
km = ureg.kilometer

# --- area / volume ---
m2 = ureg.meter**2
m3 = ureg.meter**3

# --- mass ---
kg = ureg.kilogram
t = ureg.tonne

# --- time ---
s = ureg.second

# --- temperature ---
K = ureg.kelvin
degC = ureg.degC
delta_degC = ureg.delta_degC

# --- angle ---
deg = ureg.degree

degF = ureg.degF
delta_degF = ureg.delta_degF