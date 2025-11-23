"""Statistical analysis utilities."""

import math
from typing import Dict, List, Tuple

import numpy as np
from scipy import stats


def calculate_confidence_interval(
    data: List[float],
    confidence: float = 0.95
) -> Tuple[float, float]:
    """Calculate confidence interval for data.
    
    Args:
        data: List of values
        confidence: Confidence level (default 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if len(data) < 2:
        return (0.0, 0.0)
    
    arr = np.array(data)
    mean = np.mean(arr)
    se = stats.sem(arr)
    margin = se * stats.t.ppf((1 + confidence) / 2, len(data) - 1)
    
    return (mean - margin, mean + margin)


def proportion_test(
    successes_a: int,
    total_a: int,
    successes_b: int,
    total_b: int,
) -> Dict[str, float]:
    """Compare two proportions (e.g., actionability rates).
    
    Args:
        successes_a: Successes in group A
        total_a: Total trials in group A
        successes_b: Successes in group B
        total_b: Total trials in group B
        
    Returns:
        Dictionary with test statistics
    """
    if total_a == 0 or total_b == 0:
        return {"chi2": 0.0, "p_value": 1.0, "significant": False}
    
    # Chi-square test for proportions
    contingency = np.array([
        [successes_a, total_a - successes_a],
        [successes_b, total_b - successes_b],
    ])
    
    chi2, p_value, dof, expected = stats.chi2_contingency(contingency)
    
    return {
        "chi2": float(chi2),
        "p_value": float(p_value),
        "significant": p_value < 0.05,
        "dof": int(dof),
    }


def wilcoxon_test(data_a: List[float], data_b: List[float]) -> Dict[str, float]:
    """Wilcoxon signed-rank test for paired samples.
    
    Args:
        data_a: Measurements from system A
        data_b: Measurements from system B
        
    Returns:
        Dictionary with test statistics
    """
    if len(data_a) != len(data_b) or len(data_a) < 3:
        return {"statistic": 0.0, "p_value": 1.0, "significant": False}
    
    statistic, p_value = stats.wilcoxon(data_a, data_b)
    
    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": p_value < 0.05,
    }


def mann_whitney_test(data_a: List[float], data_b: List[float]) -> Dict[str, float]:
    """Mann-Whitney U test for independent samples.
    
    Args:
        data_a: Measurements from system A
        data_b: Measurements from system B
        
    Returns:
        Dictionary with test statistics
    """
    if len(data_a) < 3 or len(data_b) < 3:
        return {"statistic": 0.0, "p_value": 1.0, "significant": False}
    
    statistic, p_value = stats.mannwhitneyu(data_a, data_b)
    
    return {
        "statistic": float(statistic),
        "p_value": float(p_value),
        "significant": p_value < 0.05,
    }


def cohens_kappa(
    rater_a: List[int],
    rater_b: List[int],
    num_categories: int,
) -> float:
    """Calculate Cohen's kappa for inter-rater reliability.
    
    Args:
        rater_a: Ratings from rater A
        rater_b: Ratings from rater B
        num_categories: Number of rating categories
        
    Returns:
        Cohen's kappa value
    """
    if len(rater_a) != len(rater_b):
        raise ValueError("Rater arrays must have same length")
    
    n = len(rater_a)
    if n == 0:
        return 0.0
    
    # Calculate observed agreement
    po = sum(1 for a, b in zip(rater_a, rater_b) if a == b) / n
    
    # Calculate expected agreement
    pe = 0.0
    for category in range(num_categories):
        pa = sum(1 for a in rater_a if a == category) / n
        pb = sum(1 for b in rater_b if b == category) / n
        pe += pa * pb
    
    # Cohen's kappa
    if pe == 1.0:
        return 1.0
    
    kappa = (po - pe) / (1 - pe)
    return kappa


def effect_size_cohens_d(data_a: List[float], data_b: List[float]) -> float:
    """Calculate Cohen's d effect size.
    
    Args:
        data_a: Data from group A
        data_b: Data from group B
        
    Returns:
        Cohen's d value
    """
    if len(data_a) < 2 or len(data_b) < 2:
        return 0.0
    
    mean_a = np.mean(data_a)
    mean_b = np.mean(data_b)
    
    std_a = np.std(data_a, ddof=1)
    std_b = np.std(data_b, ddof=1)
    
    n_a = len(data_a)
    n_b = len(data_b)
    
    # Pooled standard deviation
    pooled_std = math.sqrt(((n_a - 1) * std_a ** 2 + (n_b - 1) * std_b ** 2) / (n_a + n_b - 2))
    
    if pooled_std == 0:
        return 0.0
    
    d = (mean_a - mean_b) / pooled_std
    return d

