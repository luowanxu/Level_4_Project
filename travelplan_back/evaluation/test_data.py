# evaluation/test_data.py

import random
from typing import List, Dict, Tuple
from datetime import datetime, timedelta

class TestDataGenerator:
    def __init__(self):
        # 基础城市数据
        self.city_centers = {
            'Paris': (48.8566, 2.3522),
            'London': (51.5074, -0.1278),
            'Tokyo': (35.6762, 139.6503),
            'New York': (40.7128, -74.0060)
        }
        
    def generate_hotel(self, city_center: Tuple[float, float], radius: float = 0.01) -> Dict:
        """生成酒店数据"""
        lat, lng = self._generate_location(city_center, radius)
        return {
            "geometry": {
                "location": {
                    "lat": lat,
                    "lng": lng
                }
            },
            "place_id": f"hotel_{lat}_{lng}",
            "name": f"Hotel in {lat}, {lng}",
            "types": ["lodging", "hotel"],
            "rating": round(random.uniform(3.5, 5.0), 1),
            "user_ratings_total": random.randint(100, 5000),
            "vicinity": "City Center",
            "formatted_address": "City Center",
            "opening_hours": {"open_now": True},
            "price_level": random.randint(2, 4)
        }

    def generate_attraction(self, city_center: Tuple[float, float], radius: float = 0.02) -> Dict:
        """生成景点数据"""
        lat, lng = self._generate_location(city_center, radius)
        types = random.choice([
            ["tourist_attraction", "point_of_interest"],
            ["museum", "tourist_attraction"],
            ["park", "point_of_interest"]
        ])
        return {
            "geometry": {
                "location": {
                    "lat": lat,
                    "lng": lng
                }
            },
            "place_id": f"attr_{lat}_{lng}",
            "name": f"Attraction at {lat}, {lng}",
            "types": types,
            "rating": round(random.uniform(3.5, 5.0), 1),
            "user_ratings_total": random.randint(1000, 50000),
            "vicinity": "Tourist Area",
            "formatted_address": "Tourist Area",
            "opening_hours": {"open_now": True},
            "price_level": random.randint(1, 3)
        }

    def generate_restaurant(self, city_center: Tuple[float, float], radius: float = 0.015) -> Dict:
        """生成餐厅数据"""
        lat, lng = self._generate_location(city_center, radius)
        return {
            "geometry": {
                "location": {
                    "lat": lat,
                    "lng": lng
                }
            },
            "place_id": f"rest_{lat}_{lng}",
            "name": f"Restaurant at {lat}, {lng}",
            "types": ["restaurant", "food", "point_of_interest"],
            "rating": round(random.uniform(3.5, 5.0), 1),
            "user_ratings_total": random.randint(100, 3000),
            "vicinity": "Dining Area",
            "formatted_address": "Dining Area",
            "opening_hours": {"open_now": True},
            "price_level": random.randint(1, 4)
        }

    def generate_test_scenario(self, 
                             city: str, 
                             num_attractions: int, 
                             num_restaurants: int) -> List[Dict]:
        """生成完整的测试场景"""
        if city not in self.city_centers:
            raise ValueError(f"City {city} not supported")
            
        places = []
        city_center = self.city_centers[city]
        
        # 添加一个酒店
        places.append(self.generate_hotel(city_center))
        
        # 添加景点
        for _ in range(num_attractions):
            places.append(self.generate_attraction(city_center))
            
        # 添加餐厅
        for _ in range(num_restaurants):
            places.append(self.generate_restaurant(city_center))
            
        return places

    def _generate_location(self, center: Tuple[float, float], radius: float) -> Tuple[float, float]:
        """在给定中心点周围生成随机位置"""
        lat, lng = center
        dlat = random.uniform(-radius, radius)
        dlng = random.uniform(-radius, radius)
        return (round(lat + dlat, 6), round(lng + dlng, 6))

    def generate_test_suite(self) -> List[Dict]:
        """生成完整的测试套件"""
        scenarios = []
        
        # 标准测试场景
        size_configs = {
            'small': (3, 2),    # 3个景点，2个餐厅
            'medium': (8, 4),   # 8个景点，4个餐厅
            'large': (15, 6)    # 15个景点，6个餐厅
        }
        
        duration_configs = {
            'short': (1, 2),    # 1-2天
            'medium': (3, 5),   # 3-5天
            'long': (6, 8)      # 6-8天
        }
        
        transport_modes = ['walking', 'transit', 'driving']
        
        # 生成不同组合的测试场景
        for city in self.city_centers.keys():
            for size, (num_attr, num_rest) in size_configs.items():
                for duration_type, (min_days, max_days) in duration_configs.items():
                    for mode in transport_modes:
                        days = random.randint(min_days, max_days)
                        start_date = datetime.now().strftime('%Y-%m-%d')
                        end_date = (datetime.now() + timedelta(days=days-1)).strftime('%Y-%m-%d')
                        
                        scenarios.append({
                            'name': f"{city}_{size}_{duration_type}_{mode}",
                            'type': 'standard',
                            'places': self.generate_test_scenario(city, num_attr, num_rest),
                            'start_date': start_date,
                            'end_date': end_date,
                            'transport_mode': mode,
                            'duration_days': days
                        })
        
        return scenarios