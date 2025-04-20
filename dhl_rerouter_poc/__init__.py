# dhl_rerouter_poc/__init__.py

import undetected_chromedriver as uc

# disable Chrome.__del__ to avoid WinError 6 on garbage collection
uc.Chrome.__del__ = lambda self: None
