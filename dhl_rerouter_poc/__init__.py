# dhl_rerouter_poc/__init__.py
import warnings
import undetected_chromedriver as uc

# Suppress DeprecationWarning for distutils Version classes (repo-wide)
warnings.filterwarnings(
    "ignore",
    message="distutils Version classes are deprecated. Use packaging.version instead.",
    category=DeprecationWarning,
)

# disable Chrome.__del__ to avoid WinError 6 on garbage collection
uc.Chrome.__del__ = lambda self: None
