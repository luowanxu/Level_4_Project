# evaluation/evaluate.py

import json
from datetime import datetime
import numpy as np
from typing import Dict, List
import asyncio
from statistics import mean, stdev
from travelplan.services.schedule_service import ScheduleService
from evaluation.random_generator import RandomScheduleGenerator
from evaluation.metrics import ScheduleMetrics

class EvaluationPipeline:
    def __init__(self, places: List[Dict], start_date: str, end_date: str, transport_mode: str = 'walking'):
        """
        Initialize evaluation pipeline
        """
        self.places = places
        self.start_date = start_date
        self.end_date = end_date
        self.transport_mode = transport_mode
        self.schedule_service = ScheduleService()
        self.random_generator = RandomScheduleGenerator(
            places=places,
            start_date=start_date,
            end_date=end_date,
            transport_mode=transport_mode
        )

    async def evaluate(self, num_random_solutions: int = 100) -> Dict:
        """
        Run complete evaluation process
        
        Args:
            num_random_solutions: Number of random solutions to generate
            
        Returns:
            Dictionary containing evaluation results
        """
        # 1. Generate algorithm solution
        algo_result = await self.schedule_service.generate_schedule(
            places=self.places,
            start_date=self.start_date,
            end_date=self.end_date,
            transport_mode=self.transport_mode
        )
        
        if not algo_result['success']:
            return {
                'success': False,
                'error': f"Algorithm failed: {algo_result.get('error', 'Unknown error')}"
            }
            
        algo_schedule = algo_result['events']
        algo_metrics = ScheduleMetrics(algo_schedule, self.places)
        algo_scores = self._calculate_scores(algo_metrics)
        
        # 2. Generate random solutions
        random_scores = []
        for i in range(num_random_solutions):
            random_result = self.random_generator.generate_random_schedule()
            if random_result['success']:
                metrics = ScheduleMetrics(random_result['events'], self.places)
                scores = self._calculate_scores(metrics)
                random_scores.append(scores)
        
        # 3. Calculate statistics
        stats = self._calculate_statistics(algo_scores, random_scores)
        
        # 4. Generate report
        return {
            'success': True,
            'evaluation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'parameters': {
                'num_places': len(self.places),
                'start_date': self.start_date,
                'end_date': self.end_date,
                'transport_mode': self.transport_mode,
                'num_random_solutions': num_random_solutions
            },
            'algorithm_solution': {
                'scores': algo_scores,
                'schedule': algo_schedule
            },
            'random_solutions': {
                'statistics': stats['random_stats'],
                'percentiles': stats['percentiles']
            },
            'comparative_analysis': {
                'ranking_percentile': stats['ranking_percentile'],
                'statistical_significance': stats['statistical_significance']
            }
        }
    
    def _calculate_scores(self, metrics: ScheduleMetrics) -> Dict[str, float]:
        """Calculate all metrics scores"""
        return {
            'distance': metrics.calculate_distance_score(),
            'time_window': metrics.calculate_time_window_score(),
            'distribution': metrics.calculate_distribution_score(),
            'clustering': metrics.calculate_clustering_score(),
            'total': self._calculate_total_score(metrics)
        }
    
    def _calculate_total_score(self, metrics: ScheduleMetrics) -> float:
        """Calculate weighted total score"""
        return (
            metrics.calculate_distance_score() * 0.3 +
            metrics.calculate_time_window_score() * 0.3 +
            metrics.calculate_distribution_score() * 0.2 +
            metrics.calculate_clustering_score() * 0.2
        )
    
    def _calculate_statistics(self, algo_scores: Dict[str, float], 
                            random_scores: List[Dict[str, float]]) -> Dict:
        """Calculate comprehensive statistics"""
        metrics = ['distance', 'time_window', 'distribution', 'clustering', 'total']
        stats = {'random_stats': {}, 'percentiles': {}, 'ranking_percentile': {}}
        
        for metric in metrics:
            random_values = [scores[metric] for scores in random_scores]
            algo_value = algo_scores[metric]
            
            # Calculate basic statistics
            stats['random_stats'][metric] = {
                'mean': mean(random_values),
                'std_dev': stdev(random_values) if len(random_values) > 1 else 0,
                'min': min(random_values),
                'max': max(random_values)
            }
            
            # Calculate percentile of algorithm solution
            percentile = sum(1 for x in random_values if x < algo_value) / len(random_values) * 100
            stats['ranking_percentile'][metric] = percentile
            
            # Calculate percentile distribution
            percentiles = np.percentile(random_values, [25, 50, 75])
            stats['percentiles'][metric] = {
                'p25': percentiles[0],
                'p50': percentiles[1],
                'p75': percentiles[2]
            }
        
        # Calculate statistical significance
        stats['statistical_significance'] = {}
        for metric in metrics:
            random_values = [scores[metric] for scores in random_scores]
            algo_value = algo_scores[metric]
            mean_val = mean(random_values)
            std_val = stdev(random_values) if len(random_values) > 1 else 0
            
            if std_val > 0:
                z_score = (algo_value - mean_val) / std_val
                stats['statistical_significance'][metric] = {
                    'z_score': z_score,
                    'is_significant': abs(z_score) > 1.96  # 95% confidence level
                }
        
        return stats

def print_evaluation_report(results: Dict):
    """Print formatted evaluation report"""
    print("\n=== Travel Schedule Evaluation Report ===")
    print(f"Evaluation Time: {results['evaluation_time']}")
    print("\nParameters:")
    for key, value in results['parameters'].items():
        print(f"  {key}: {value}")
    
    print("\nAlgorithm Solution Scores:")
    for metric, score in results['algorithm_solution']['scores'].items():
        print(f"  {metric.replace('_', ' ').title()}: {score:.2f}")
    
    print("\nRandom Solutions Statistics:")
    for metric, stats in results['random_solutions']['statistics'].items():
        print(f"\n  {metric.replace('_', ' ').title()}:")
        print(f"    Mean: {stats['mean']:.2f}")
        print(f"    Std Dev: {stats['std_dev']:.2f}")
        print(f"    Range: [{stats['min']:.2f} - {stats['max']:.2f}]")
    
    print("\nPerformance Analysis:")
    for metric, percentile in results['comparative_analysis']['ranking_percentile'].items():
        print(f"  {metric.replace('_', ' ').title()}: {percentile:.1f}th percentile")
    
    print("\nStatistical Significance:")
    for metric, stats in results['comparative_analysis']['statistical_significance'].items():
        significant = "Significant" if stats['is_significant'] else "Not significant"
        print(f"  {metric.replace('_', ' ').title()}: {significant} (z={stats['z_score']:.2f})")

async def run_evaluation(places: List[Dict], start_date: str, end_date: str, 
                        transport_mode: str = 'walking', num_random_solutions: int = 100):
    """Run evaluation pipeline"""
    pipeline = EvaluationPipeline(places, start_date, end_date, transport_mode)
    results = await pipeline.evaluate(num_random_solutions)
    
    if results['success']:
        print_evaluation_report(results)
        return results
    else:
        print(f"Evaluation failed: {results.get('error', 'Unknown error')}")
        return None