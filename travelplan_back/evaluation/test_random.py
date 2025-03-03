# evaluation/test_random.py

from evaluation.random_generator import RandomScheduleGenerator
from evaluation.metrics import ScheduleMetrics
from statistics import mean, stdev

def test_random_generator():
    """测试随机行程生成器"""
    # 使用与之前相同的测试数据
    places = [
        {
            "geometry": {
                "location": {
                    "lat": 48.8566,
                    "lng": 2.3522
                }
            },
            "place_id": "hotel_paris_center",
            "name": "Paris Center Hotel",
            "types": ["lodging", "hotel"],
            "rating": 4.5,
            "user_ratings_total": 2000,
            "vicinity": "Central Paris",
            "formatted_address": "Central Paris, France",
            "opening_hours": {"open_now": True},
            "price_level": 3
        },
        {
            "geometry": {
                "location": {
                    "lat": 48.8584,
                    "lng": 2.2945
                }
            },
            "place_id": "ChIJLU7jZClu5kcR4PcOOO6p3I0",
            "name": "Eiffel Tower",
            "types": ["tourist_attraction", "point_of_interest"],
            "rating": 4.6,
            "user_ratings_total": 375000,
            "vicinity": "Champ de Mars",
            "formatted_address": "Champ de Mars, Paris, France",
            "opening_hours": {"open_now": True},
            "price_level": 2
        },
        {
            "geometry": {
                "location": {
                    "lat": 48.8629,
                    "lng": 2.3386
                }
            },
            "place_id": "ChIJ3Qp9_FJu5kcRv3QrZZl4qqk",
            "name": "Le Bistrot Vivienne",
            "types": ["restaurant", "point_of_interest", "food"],
            "rating": 4.4,
            "user_ratings_total": 1500,
            "vicinity": "Galerie Vivienne",
            "formatted_address": "4 Rue des Petits Champs, Paris, France",
            "opening_hours": {"open_now": True},
            "price_level": 2
        },
        {
            "geometry": {
                "location": {
                    "lat": 48.8606,
                    "lng": 2.3376
                }
            },
            "place_id": "ChIJATr1n-Fx5kcRjQb6q6cdQDY",
            "name": "Louvre Museum",
            "types": ["museum", "tourist_attraction", "point_of_interest"],
            "rating": 4.7,
            "user_ratings_total": 270000,
            "vicinity": "Rue de Rivoli",
            "formatted_address": "Rue de Rivoli, Paris, France",
            "opening_hours": {"open_now": True},
            "price_level": 2
        }
    ]

    # 创建随机生成器
    generator = RandomScheduleGenerator(
        places=places,
        start_date="2024-02-08",
        end_date="2024-02-10",
        transport_mode="walking"
    )

    print("=== Testing Random Schedule Generator ===")
    print("Generating 5 random schedules...")

    # 存储所有评分用于统计分析
    all_scores = {
        'distance': [],
        'time_window': [],
        'distribution': [],
        'clustering': [],
        'total': []
    }

    for i in range(5):
        print(f"\nRandom Schedule #{i+1}")
        result = generator.generate_random_schedule()
        
        if result['success']:
            schedule = result['events']
            metrics = ScheduleMetrics(schedule, places)
            
            print("\nSchedule Details:")
            current_day = -1
            for event in schedule:
                if event['type'] == 'place':
                    if event['day'] != current_day:
                        current_day = event['day']
                        print(f"\nDay {current_day + 1}:")
                    print(f"  {event['title']} at {event.get('startTime', 'N/A')} - {event.get('endTime', 'N/A')}")
            
            # 计算各项指标
            distance_score = metrics.calculate_distance_score()
            time_score = metrics.calculate_time_window_score()
            distribution_score = metrics.calculate_distribution_score()
            clustering_score = metrics.calculate_clustering_score()
            
            # 计算总分
            total_score = (
                distance_score * 0.3 +
                time_score * 0.3 +
                distribution_score * 0.2 +
                clustering_score * 0.2
            )
            
            # 存储分数
            all_scores['distance'].append(distance_score)
            all_scores['time_window'].append(time_score)
            all_scores['distribution'].append(distribution_score)
            all_scores['clustering'].append(clustering_score)
            all_scores['total'].append(total_score)
            
            print("\nMetrics:")
            print(f"Distance Score: {distance_score:.2f}")
            print(f"Time Window Score: {time_score:.2f}")
            print(f"Distribution Score: {distribution_score:.2f}")
            print(f"Clustering Score: {clustering_score:.2f}")
            print(f"Total Score: {total_score:.2f}")
        else:
            print(f"Failed to generate schedule: {result.get('error', 'Unknown error')}")

    # 打印统计信息
    print("\n=== Statistical Analysis ===")
    for metric, scores in all_scores.items():
        if scores:
            print(f"\n{metric.replace('_', ' ').title()}:")
            print(f"  Average: {mean(scores):.2f}")
            if len(scores) > 1:
                print(f"  Std Dev: {stdev(scores):.2f}")
            print(f"  Min: {min(scores):.2f}")
            print(f"  Max: {max(scores):.2f}")

if __name__ == "__main__":
    test_random_generator()