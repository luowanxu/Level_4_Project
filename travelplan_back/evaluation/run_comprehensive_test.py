# evaluation/run_comprehensive_test.py

import asyncio
import django
django.setup()

from evaluation.comprehensive_test import ComprehensiveTest
from evaluation.test_data import TestDataGenerator

async def main():
    print("=== Starting Comprehensive Travel Planner Evaluation ===")
    print("Initializing test environment...")
    
    test_data_generator = TestDataGenerator()
    tester = ComprehensiveTest(test_data_generator)
    
    print("Running comprehensive tests...")
    await tester.run_comprehensive_tests()
    
    print("\nEvaluation completed. Results have been saved to the test_results directory.")

if __name__ == "__main__":
    asyncio.run(main())