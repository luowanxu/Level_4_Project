# evaluation/test_metrics.py

import asyncio
import json
from datetime import datetime
import django
django.setup()
from evaluation.metrics import ScheduleMetrics
from travelplan.services.schedule_service import ScheduleService
from travelplan.services.clustering import preprocess_places, hierarchical_clustering
from travelplan.services.utils import calculate_distance_matrix

def create_sample_schedule():
    """创建一个示例行程用于测试"""
    return [
        {
            "day": 0,
            "type": "place",
            "startTime": "09:00 AM",
            "endTime": "10:30 AM",
            "place": {
                "geometry": {
                    "location": {
                        "lat": 40.7128,
                        "lng": -74.0060
                    }
                },
                "types": ["tourist_attraction"],
                "name": "Attraction 1"
            }
        },
        {
            "day": 0,
            "type": "place",
            "startTime": "12:00 PM",
            "endTime": "01:30 PM",
            "place": {
                "geometry": {
                    "location": {
                        "lat": 40.7129,
                        "lng": -74.0061
                    }
                },
                "types": ["restaurant"],
                "name": "Restaurant 1"
            }
        },
        {
            "day": 0,
            "type": "place",
            "startTime": "02:00 PM",
            "endTime": "04:00 PM",
            "place": {
                "geometry": {
                    "location": {
                        "lat": 40.7130,
                        "lng": -74.0062
                    }
                },
                "types": ["museum"],
                "name": "Museum 1"
            }
        }
    ]

def create_sample_places():
    """创建示例地点列表"""
    return [
        {
            "geometry": {
                "location": {
                    "lat": 40.7128,
                    "lng": -74.0060
                }
            },
            "types": ["tourist_attraction"],
            "name": "Attraction 1"
        },
        {
            "geometry": {
                "location": {
                    "lat": 40.7129,
                    "lng": -74.0061
                }
            },
            "types": ["restaurant"],
            "name": "Restaurant 1"
        },
        {
            "geometry": {
                "location": {
                    "lat": 40.7130,
                    "lng": -74.0062
                }
            },
            "types": ["museum"],
            "name": "Museum 1"
        }
    ]

def test_with_sample_data():
    """使用示例数据测试"""
    schedule = create_sample_schedule()
    places = create_sample_places()
    
    metrics = ScheduleMetrics(schedule, places)
    print("\n=== Testing with Sample Data ===")
    print_metrics_results(metrics)

def test_with_real_data():
    """使用真实数据测试"""
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
            "vicinity": "Champ de Mars, 5 Avenue Anatole France",
            "formatted_address": "Champ de Mars, 5 Avenue Anatole France, 75007 Paris, France",
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
            "formatted_address": "4 Rue des Petits Champs, 75002 Paris, France",
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
            "formatted_address": "Rue de Rivoli, 75001 Paris, France",
            "opening_hours": {"open_now": True},
            "price_level": 2
        }
    ]

    print("\n=== Testing with Real Data ===")
    print(f"Number of places: {len(places)}")
    print("Places to process:")
    for place in places:
        print(f"- {place['name']} ({', '.join(place['types'])})")

    try:
        # 1. 预处理地点
        processed_places, hotel = preprocess_places(places)
        print("\nPreprocessed places:")
        print(f"Hotel: {hotel['name'] if hotel else 'No hotel'}")
        print(f"Number of processed places: {len(processed_places)}")
        for place in processed_places:
            print(f"- {place['name']} (Type: {place['type']}, Duration: {place.get('visit_duration', 'N/A')} min)")

        # 2. 获取距离矩阵
        all_places = [hotel] + processed_places
        distance_matrix, time_matrix = calculate_distance_matrix(
            all_places,
            "walking",
            use_api=False
        )
        print("\nDistance matrix shape:", distance_matrix.shape)

        # 3. 尝试聚类
        num_days = 3  # 改为3天
        try:
            clusters = hierarchical_clustering(
                processed_places,
                num_days,
                "walking"
            )
            print(f"\nGenerated {len(clusters)} clusters:")
            for i, cluster in enumerate(clusters):
                print(f"Cluster {i}: {len(cluster)} places")
                for place in cluster:
                    print(f"  - {place['name']}")
        except Exception as e:
            print(f"\nClustering error: {str(e)}")
            raise

        # 4. 继续原有的schedule generation流程
        schedule_service = ScheduleService()
        result = asyncio.run(schedule_service.generate_schedule(
            places=places,
            start_date="2024-02-08",
            end_date="2024-02-10",  # 改为3天
            transport_mode="walking"
        ))
        
        if result['success']:
            schedule = result['events']
            metrics = ScheduleMetrics(schedule, places)
            print("\nSchedule generated successfully!")
            print_metrics_results(metrics)
            
            print("\nGenerated Schedule Details:")
            for event in schedule:
                if event['type'] == 'place':
                    print(f"- {event.get('title', 'Unnamed')} at {event.get('startTime', 'No time')} - {event.get('endTime', 'No time')}")
        else:
            print(f"\nFailed to generate schedule: {result.get('error', 'Unknown error')}")
            if 'schedule_status' in result:
                print("\nSchedule Status:")
                print(f"Is reasonable: {result['schedule_status'].get('is_reasonable', False)}")
                for warning in result['schedule_status'].get('warnings', []):
                    print(f"- {warning.get('message', 'No message')}")
                    print(f"  Suggestion: {warning.get('suggestion', 'No suggestion')}")
    
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()

def print_metrics_results(metrics):
    """打印评估结果"""
    distance_score = metrics.calculate_distance_score()
    time_score = metrics.calculate_time_window_score()
    distribution_score = metrics.calculate_distribution_score()
    clustering_score = metrics.calculate_clustering_score()
    
    print(f"Distance Score: {distance_score:.2f}")
    print(f"Time Window Score: {time_score:.2f}")
    print(f"Distribution Score: {distribution_score:.2f}")
    print(f"Clustering Score: {clustering_score:.2f}")
    
    total_score = (
        distance_score * 0.3 +     # 路程优化权重 30%
        time_score * 0.3 +         # 时间窗口权重 30%
        distribution_score * 0.2 +  # 分布均匀性权重 20%
        clustering_score * 0.2      # 聚类紧凑度权重 20%
    )
    print(f"\nTotal Score: {total_score:.2f}")

if __name__ == "__main__":
    # 运行两种测试
    test_with_sample_data()
    test_with_real_data()