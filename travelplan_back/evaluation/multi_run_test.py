# evaluation/multi_run_test.py

import asyncio
import django
django.setup()

import numpy as np
from evaluation.comprehensive_test import ComprehensiveTest
from evaluation.test_data import TestDataGenerator
import time
import os
from pathlib import Path
import json

async def run_single_test(run_id, output_dir):
    """运行单次测试并返回结果"""
    print(f"Starting test run #{run_id}")
    
    # 创建测试实例
    test_data_generator = TestDataGenerator()
    tester = ComprehensiveTest(test_data_generator, output_dir=str(output_dir / f"run_{run_id}"))
    
    # 运行测试
    await tester.run_comprehensive_tests()
    
    # 读取结果
    summary_path = output_dir / f"run_{run_id}" / "summary_report.json"
    if summary_path.exists():
        with open(summary_path, 'r') as f:
            summary = json.load(f)
            
        total_scenarios = summary['overview']['total_scenarios']
        better_than_random = summary['overview']['better_than_random']
        significantly_better = summary['overview']['significantly_better']
        
        success_rate = better_than_random / total_scenarios * 100
        significant_rate = significantly_better / total_scenarios * 100
        
        return {
            'run_id': run_id,
            'total_scenarios': total_scenarios,
            'success_rate': success_rate,
            'significant_rate': significant_rate
        }
    else:
        print(f"Warning: No summary report found for run #{run_id}")
        return None

async def run_multiple_tests(num_runs=10):
    """运行多次测试并汇总结果"""
    print(f"Starting {num_runs} test runs")
    
    # 创建结果目录
    timestamp = int(time.time())
    output_dir = Path(f"evaluation/multi_test_results_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    # 运行多次测试
    for i in range(1, num_runs + 1):
        result = await run_single_test(i, output_dir)
        if result:
            results.append(result)
    
    if not results:
        print("No valid results obtained")
        return
    
    # 计算统计数据
    success_rates = [r['success_rate'] for r in results]
    significant_rates = [r['significant_rate'] for r in results]
    
    # 输出简洁结果
    print("\n===== Results Summary =====")
    print(f"Number of successful runs: {len(results)}")
    
    print("\nSuccess Rate (better than random):")
    print(f"Min: {min(success_rates):.1f}%")
    print(f"Max: {max(success_rates):.1f}%")
    print(f"Mean: {np.mean(success_rates):.1f}%")
    print(f"Median: {np.median(success_rates):.1f}%")
    if len(success_rates) > 1:
        print(f"Std Dev: {np.std(success_rates):.1f}%")
    
    print("\nSignificant Success Rate (significantly better):")
    print(f"Min: {min(significant_rates):.1f}%")
    print(f"Max: {max(significant_rates):.1f}%")
    print(f"Mean: {np.mean(significant_rates):.1f}%")
    print(f"Median: {np.median(significant_rates):.1f}%")
    if len(significant_rates) > 1:
        print(f"Std Dev: {np.std(significant_rates):.1f}%")
    
    # 保存汇总结果
    summary = {
        'num_runs': len(results),
        'success_rate': {
            'min': float(min(success_rates)),
            'max': float(max(success_rates)),
            'mean': float(np.mean(success_rates)),
            'median': float(np.median(success_rates)),
            'std_dev': float(np.std(success_rates)) if len(success_rates) > 1 else None
        },
        'significant_rate': {
            'min': float(min(significant_rates)),
            'max': float(max(significant_rates)),
            'mean': float(np.mean(significant_rates)),
            'median': float(np.median(significant_rates)),
            'std_dev': float(np.std(significant_rates)) if len(significant_rates) > 1 else None
        },
        'individual_runs': results
    }
    
    with open(output_dir / "multi_run_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nDetailed results saved to {output_dir}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run multiple evaluation tests")
    parser.add_argument("-n", "--num-runs", type=int, default=3, 
                        help="Number of test runs to perform")
    args = parser.parse_args()
    
    asyncio.run(run_multiple_tests(args.num_runs))