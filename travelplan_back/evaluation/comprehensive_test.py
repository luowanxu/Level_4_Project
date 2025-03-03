# evaluation/comprehensive_test.py

from typing import Dict, List
import asyncio
from datetime import datetime, timedelta
from evaluation.evaluate import EvaluationPipeline
from evaluation.test_data import TestDataGenerator
import json
import pandas as pd
import numpy as np
from pathlib import Path

class ComprehensiveTest:
    def __init__(self, data_generator: TestDataGenerator, output_dir: str = "evaluation/test_results"):
        """初始化综合测试器"""
        self.data_generator = data_generator
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def run_comprehensive_tests(self):
        """运行所有测试场景"""
        scenarios = self.data_generator.generate_test_suite()
        results = []
        
        total_scenarios = len(scenarios)
        print(f"\nTotal test scenarios: {total_scenarios}")
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\nRunning test scenario {i}/{total_scenarios}: {scenario['name']}")
            print(f"Configuration: {len(scenario['places'])} places, "
                  f"{scenario['duration_days']} days, {scenario['transport_mode']} mode")
            
            try:
                pipeline = EvaluationPipeline(
                    places=scenario['places'],
                    start_date=scenario['start_date'],
                    end_date=scenario['end_date'],
                    transport_mode=scenario['transport_mode']
                )
                
                evaluation_result = await pipeline.evaluate(num_random_solutions=50)
                
                if evaluation_result['success']:
                    result = {
                        'scenario': scenario['name'],
                        'type': scenario['type'],
                        'num_places': len(scenario['places']),
                        'duration_days': scenario['duration_days'],
                        'transport_mode': scenario['transport_mode'],
                        'algorithm_scores': evaluation_result['algorithm_solution']['scores'],
                        'random_stats': evaluation_result['random_solutions']['statistics'],
                        'percentiles': evaluation_result['comparative_analysis']['ranking_percentile']
                    }
                    results.append(result)
                    
                    # 保存详细结果（注意处理JSON序列化）
                    try:
                        self._save_scenario_result(scenario['name'], 
                                                self._make_json_serializable(evaluation_result))
                        print(f"Scenario completed successfully")
                    except Exception as e:
                        print(f"Error saving scenario result: {str(e)}")
                else:
                    print(f"Scenario failed: {evaluation_result.get('error', 'Unknown error')}")
            
            except Exception as e:
                print(f"Error in scenario {scenario['name']}: {str(e)}")
                continue
        
        # 生成汇总报告
        if results:
            self.generate_summary_report(results)
        else:
            print("No successful test results to analyze")

    def _make_json_serializable(self, obj):
        """使对象可JSON序列化"""
        if isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        elif isinstance(obj, bool):
            return str(obj)
        elif isinstance(obj, (datetime, np.datetime64)):
            return obj.isoformat()
        return obj
    
    def _save_scenario_result(self, scenario_name: str, result: Dict):
        """保存单个场景的详细结果"""
        file_path = self.output_dir / f"{scenario_name}_detailed.json"
        with open(file_path, 'w') as f:
            json.dump(result, f, indent=2)
    
    def generate_summary_report(self, results: List[Dict]):
        """生成测试汇总报告"""
        df = pd.DataFrame(results)
        
        print("\n=== Comprehensive Test Summary ===")
        
        # 1. 基本统计
        print("\n1. Basic Statistics:")
        print(f"Total scenarios tested: {len(df)}")
        print(f"Total expected scenarios: 108 (4 cities × 3 sizes × 3 durations × 3 transport modes)")
        print(f"Average algorithm total score: {df['algorithm_scores'].apply(lambda x: x['total']).mean():.2f}")
        
        # 检查缺失的场景
        print("\nMissing Scenarios Analysis:")
        # 创建所有可能的场景名称组合
        expected_scenarios = []
        cities = ['Paris', 'London', 'Tokyo', 'New York']
        sizes = ['small', 'medium', 'large']
        durations = ['short', 'medium', 'long']
        modes = ['walking', 'transit', 'driving']
        
        for city in cities:
            for size in sizes:
                for duration in durations:
                    for mode in modes:
                        expected_scenarios.append(f"{city}_{size}_{duration}_{mode}")
        
        # 找出缺失的场景
        actual_scenarios = set(df['scenario'].tolist())
        missing_scenarios = set(expected_scenarios) - actual_scenarios
        
        print(f"\nMissing {len(missing_scenarios)} scenarios:")
        
        # 按类别统计缺失
        missing_by_city = {}
        missing_by_size = {}
        missing_by_duration = {}
        missing_by_mode = {}
        
        for scenario in missing_scenarios:
            city, size, duration, mode = scenario.split('_')
            missing_by_city[city] = missing_by_city.get(city, 0) + 1
            missing_by_size[size] = missing_by_size.get(size, 0) + 1
            missing_by_duration[duration] = missing_by_duration.get(duration, 0) + 1
            missing_by_mode[mode] = missing_by_mode.get(mode, 0) + 1
        
        print("\nMissing scenarios by category:")
        print("\nBy City:")
        for city, count in missing_by_city.items():
            print(f"  {city}: {count} scenarios")
        
        print("\nBy Size:")
        for size, count in missing_by_size.items():
            print(f"  {size}: {count} scenarios")
            
        print("\nBy Duration:")
        for duration, count in missing_by_duration.items():
            print(f"  {duration}: {count} scenarios")
            
        print("\nBy Transport Mode:")
        for mode, count in missing_by_mode.items():
            print(f"  {mode}: {count} scenarios")
            
        print("\nMissing scenario list:")
        for scenario in sorted(missing_scenarios):
            print(f"  {scenario}")
        
        # 2. 性能分析
        print("\n2. Performance Analysis:")
        better_than_random = df[df['percentiles'].apply(lambda x: x['total']) > 50]
        significantly_better = df[df['percentiles'].apply(lambda x: x['total']) > 90]
        
        print(f"Better than random: {len(better_than_random)}/{len(df)} "
              f"({len(better_than_random)/len(df)*100:.1f}%)")
        print(f"Significantly better: {len(significantly_better)}/{len(df)} "
              f"({len(significantly_better)/len(df)*100:.1f}%)")
        
        # 3. 失败案例分析
        print("\n3. Cases Where Random Solutions Outperformed Algorithm:")
        worse_than_random = df[df['percentiles'].apply(lambda x: x['total']) <= 50]
        
        if not worse_than_random.empty:
            for _, case in worse_than_random.iterrows():
                print(f"\nScenario: {case['scenario']}")
                print(f"Configuration:")
                print(f"  - Places: {case['num_places']}")
                print(f"  - Duration: {case['duration_days']} days")
                print(f"  - Transport: {case['transport_mode']}")
                print("\nScores:")
                print("Algorithm scores:")
                for metric, score in case['algorithm_scores'].items():
                    print(f"  - {metric}: {score:.2f}")
                print("\nRandom solutions statistics:")
                for metric, stats in case['random_stats'].items():
                    print(f"  - {metric}:")
                    print(f"    Mean: {stats['mean']:.2f}")
                    print(f"    Best: {stats['max']:.2f}")
                print("\nPercentile rankings:")
                for metric, percentile in case['percentiles'].items():
                    print(f"  - {metric}: {percentile:.1f}th percentile")
        else:
            print("No cases where random solutions outperformed the algorithm.")
        
        # 4. 交通方式分析
        print("\n4. Performance by Transport Mode:")
        for mode in df['transport_mode'].unique():
            mode_data = df[df['transport_mode'] == mode]
            avg_score = mode_data['algorithm_scores'].apply(lambda x: x['total']).mean()
            success_rate = (mode_data['percentiles'].apply(lambda x: x['total']) > 50).mean() * 100
            print(f"\n{mode.title()}:")
            print(f"  Average score: {avg_score:.2f}")
            print(f"  Success rate: {success_rate:.1f}%")
            print(f"  Number of cases: {len(mode_data)}")
        
        # 5. 规模分析
        print("\n5. Performance by Problem Size:")
        def get_size_category(num_places):
            if num_places <= 8:
                return 'small'
            elif num_places <= 15:
                return 'medium'
            else:
                return 'large'
                
        df['size_category'] = df['num_places'].apply(get_size_category)
        for size in ['small', 'medium', 'large']:
            size_data = df[df['size_category'] == size]
            if len(size_data) > 0:
                avg_score = size_data['algorithm_scores'].apply(lambda x: x['total']).mean()
                success_rate = (size_data['percentiles'].apply(lambda x: x['total']) > 50).mean() * 100
                print(f"\n{size.title()}:")
                print(f"  Places range: {size_data['num_places'].min()}-{size_data['num_places'].max()}")
                print(f"  Average score: {avg_score:.2f}")
                print(f"  Success rate: {success_rate:.1f}%")
                print(f"  Number of cases: {len(size_data)}")

        # 保存汇总报告
        summary = {
            'overview': {
                'total_scenarios': len(df),
                'expected_scenarios': 108,
                'missing_scenarios': {
                    'total': len(missing_scenarios),
                    'by_city': missing_by_city,
                    'by_size': missing_by_size,
                    'by_duration': missing_by_duration,
                    'by_mode': missing_by_mode,
                    'full_list': sorted(list(missing_scenarios))
                },
                'better_than_random': len(better_than_random),
                'significantly_better': len(significantly_better),
                'average_score': float(df['algorithm_scores'].apply(lambda x: x['total']).mean())
            },
            'transport_mode_analysis': {
                mode: float(data['algorithm_scores'].apply(lambda x: x['total']).mean())
                for mode, data in df.groupby('transport_mode')
            },
            'failed_cases': [
                {
                    'scenario': case['scenario'],
                    'config': {
                        'num_places': int(case['num_places']),
                        'duration_days': int(case['duration_days']),
                        'transport_mode': case['transport_mode']
                    },
                    'scores': self._make_json_serializable(case['algorithm_scores']),
                    'random_stats': self._make_json_serializable(case['random_stats']),
                    'percentiles': self._make_json_serializable(case['percentiles'])
                }
                for _, case in worse_than_random.iterrows()
            ]
        }

        summary_path = self.output_dir / "summary_report.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)