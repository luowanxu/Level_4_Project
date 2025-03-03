# evaluation/random_generator.py

import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import numpy as np
from travelplan.services.clustering import PlaceConstraints, preprocess_places
from travelplan.services.utils import calculate_distance_matrix

class RandomScheduleGenerator:
    def __init__(self, places: List[Dict], start_date: str, end_date: str, transport_mode: str = 'walking'):
        """
        初始化随机行程生成器
        
        Args:
            places: 地点列表
            start_date: 开始日期
            end_date: 结束日期
            transport_mode: 交通方式
        """
        self.original_places = places
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')
        self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
        self.num_days = (self.end_date - self.start_date).days + 1
        self.transport_mode = transport_mode
        
        # 预处理地点数据
        self.processed_places, self.hotel = preprocess_places(places)
        if not self.hotel:
            raise ValueError("No hotel found in places list")
        
        # 计算距离矩阵
        all_places = [self.hotel] + self.processed_places
        self.distance_matrix, self.time_matrix = calculate_distance_matrix(
            all_places,
            transport_mode,
            use_api=False
        )

    def generate_random_schedule(self) -> Dict:
        """生成一个随机但合法的行程安排"""
        try:
            # 1. 随机分配地点到不同天数
            places_by_day = self._randomly_assign_days()
            
            # 2. 对每天的行程进行随机排序并添加用餐时间
            schedule = []
            for day in range(self.num_days):
                day_schedule = self._generate_day_schedule(
                    places_by_day.get(day, []),
                    day
                )
                schedule.extend(day_schedule)
            
            return {
                'success': True,
                'events': schedule
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _randomly_assign_days(self) -> Dict[int, List[Dict]]:
        """将地点随机分配到不同的天数"""
        places_by_day = {i: [] for i in range(self.num_days)}
        
        # 分离餐厅和其他地点
        restaurants = [p for p in self.processed_places if p.get('is_restaurant', False)]
        attractions = [p for p in self.processed_places if not p.get('is_restaurant', False)]
        
        # 随机分配非餐厅地点
        for place in attractions:
            day = random.randint(0, self.num_days - 1)
            places_by_day[day].append(place)
        
        # 分配餐厅，确保每天有用餐地点
        for day in range(self.num_days):
            # 如果有真实餐厅，随机选择
            if restaurants:
                if len(restaurants) >= 2:
                    # 随机选择两家不同的餐厅
                    day_restaurants = random.sample(restaurants, 2)
                    for r in day_restaurants:
                        places_by_day[day].append(r)
                        restaurants.remove(r)
                else:
                    # 使用所有剩余的真实餐厅
                    for r in restaurants:
                        places_by_day[day].append(r)
                    restaurants.clear()
            
            # 补充虚拟餐厅
            current_restaurants = len([p for p in places_by_day[day] if p.get('is_restaurant', False)])
            if current_restaurants < 2:
                # 添加需要的虚拟餐厅
                center = self._calculate_day_center(places_by_day[day])
                for _ in range(2 - current_restaurants):
                    meal_type = 'lunch' if _ == 0 else 'dinner'
                    virtual_restaurant = {
                        'name': f"{meal_type.title()} Break",
                        'types': ['restaurant'],
                        'rating': 0,
                        'user_ratings_total': 0,
                        'price_level': 2,
                        'visit_duration': 75,
                        'is_restaurant': True,
                        'is_virtual': True,
                        'location': center
                    }
                    places_by_day[day].append(virtual_restaurant)
        
        return places_by_day

    def _generate_day_schedule(self, places: List[Dict], day: int) -> List[Dict]:
        """为一天生成随机但合理的行程安排"""
        if not places:
            return []
            
        schedule = []
        current_time = datetime.combine(
            self.start_date + timedelta(days=day),
            PlaceConstraints.DAY_CONSTRAINTS['start']
        )
        
        # 添加酒店作为起点
        schedule.append({
            'type': 'place',
            'place': self.hotel,
            'startTime': '',
            'endTime': '',
            'day': day,
            'title': self.hotel['name']
        })
        
        # 对地点进行随机排序，但确保用餐时间在合适的时间段
        restaurants = [p for p in places if p.get('is_restaurant', False)]
        attractions = [p for p in places if not p.get('is_restaurant', False)]
        
        # 随机排序非餐厅地点
        random.shuffle(attractions)
        
        # 确定午餐和晚餐时间
        lunch_time = datetime.combine(
            current_time.date(),
            PlaceConstraints.DINING_WINDOWS['lunch']['optimal']
        )
        dinner_time = datetime.combine(
            current_time.date(),
            PlaceConstraints.DINING_WINDOWS['dinner']['optimal']
        )
        
        # 将一天分成三个时间段：上午、下午和晚上
        morning_slots = []
        afternoon_slots = []
        evening_slots = []
        
        # 分配非餐厅地点到不同时间段
        for place in attractions:
            if current_time.time() < lunch_time.time():
                morning_slots.append(place)
            elif current_time.time() < dinner_time.time():
                afternoon_slots.append(place)
            else:
                evening_slots.append(place)
        
        # 随机排序每个时间段
        random.shuffle(morning_slots)
        random.shuffle(afternoon_slots)
        random.shuffle(evening_slots)
        
        # 组合最终行程
        for slot in morning_slots + [restaurants[0]] + afternoon_slots + [restaurants[1]] + evening_slots:
            visit_duration = slot.get('visit_duration', 90)
            
            schedule.append({
                'type': 'place',
                'place': slot,
                'startTime': current_time.strftime('%I:%M %p'),
                'endTime': (current_time + timedelta(minutes=visit_duration)).strftime('%I:%M %p'),
                'day': day,
                'title': slot['name']
            })
            
            current_time += timedelta(minutes=visit_duration)
            # 添加交通时间
            current_time += timedelta(minutes=30)  # 简化的交通时间
        
        # 添加酒店作为终点
        schedule.append({
            'type': 'place',
            'place': self.hotel,
            'startTime': '',
            'endTime': '',
            'day': day,
            'title': self.hotel['name']
        })
        
        return schedule

    def _calculate_day_center(self, places: List[Dict]) -> Dict[str, float]:
        """计算一天所有地点的中心位置"""
        if not places:
            return {'lat': 0.0, 'lng': 0.0}
            
        lats = []
        lngs = []
        for place in places:
            if 'geometry' in place:
                lats.append(place['geometry']['location']['lat'])
                lngs.append(place['geometry']['location']['lng'])
            elif 'location' in place:
                lats.append(place['location']['lat'])
                lngs.append(place['location']['lng'])
        
        if not lats:  # 如果没有有效的位置数据
            return {'lat': 0.0, 'lng': 0.0}
            
        return {
            'lat': sum(lats) / len(lats),
            'lng': sum(lngs) / len(lngs)
        }