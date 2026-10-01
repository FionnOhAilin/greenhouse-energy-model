from uncertainties import ufloat

x = ufloat(2, 0.2)

y = ufloat(6, 0.3)

z = ufloat(3,0.5)

eq1 = x+y
eq2 = x-y
eq3 = x*y
eq4 = y/z
eq5 = x**2
eq6 = 2**x
eq7 = 10**z
eq8 = (x)**z

print(f"eq1 {eq1:.6f}\neq2 {eq2:.6f}\neq3 {eq3:.6f}\neq4 {eq4:.6f}\neq5 "
      f"{eq5:.6f}\neq6 {eq6:.6f}\neq7 {eq7:.6f}\neq8 {eq8:.6f}")

