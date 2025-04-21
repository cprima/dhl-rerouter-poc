import warnings

# Suppress undetected_chromedriver distutils deprecation warning
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message="distutils Version classes are deprecated.*"
)
