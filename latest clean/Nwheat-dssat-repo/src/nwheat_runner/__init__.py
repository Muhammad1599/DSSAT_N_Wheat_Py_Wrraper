"""
NWheat DSSAT Experiment Runner

A Python package for running and analyzing NWheat (CROPSIM-Wheat) experiments
with DSSAT, including model validation and results analysis.
"""

__version__ = "1.0.0"
__author__ = "Research Team"
__email__ = "research@university.edu"

try:
    from .runner import NWheatRunner
    from .analyzer import ResultsAnalyzer
    from .validator import ModelValidator
    
    __all__ = [
        "NWheatRunner",
        "ResultsAnalyzer", 
        "ModelValidator",
    ]
except ImportError:
    # Handle case where dependencies might not be installed
    __all__ = []
