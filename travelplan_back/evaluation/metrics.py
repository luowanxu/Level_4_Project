# evaluation/metrics.py

from typing import List, Dict, Any
import numpy as np
from datetime import datetime, time
from travelplan.services.utils import haversine_distance, calculate_travel_time
from travelplan.services.clustering import PlaceConstraints

class ScheduleMetrics:
    def __init__(self, schedule: List[Dict], places: List[Dict]):
        """
        初始化评估指标计算器
        
        Args:
            schedule: 需要评估的行程安排
            places: 原始地点列表
        """
        self.schedule = schedule
        self.places = places
        self.events_by_day = self._group_events_by_day()
        
    def _group_events_by_day(self) -> Dict[int, List[Dict]]:
        """将事件按天分组"""
        events_by_day = {}
        for event in self.schedule:
            day = event.get('day', 0)
            if day not in events_by_day:
                events_by_day[day] = []
            events_by_day[day].append(event)
        return events_by_day
    
    def _get_location(self, place: Dict) -> tuple:
        """
        从地点数据中提取经纬度，处理不同的数据结构
        包括虚拟餐厅的处理
        """
        try:
            # 处理虚拟餐厅
            if place.get('name') in ['Lunch Break', 'Dinner Break']:
                # 使用其他地点的平均位置
                avg_lat = 0
                avg_lng = 0
                count = 0
                for event in self.schedule:
                    if event.get('type') == 'place' and event['place'].get('name') not in ['Lunch Break', 'Dinner Break']:
                        loc = None
                        if 'geometry' in event['place']:
                            loc = event['place']['geometry']['location']
                        elif 'location' in event['place']:
                            loc = event['place']['location']
                        
                        if loc:
                            avg_lat += float(loc['lat'])
                            avg_lng += float(loc['lng'])
                            count += 1
                
                if count > 0:
                    return (avg_lat / count, avg_lng / count)
                else:
                    # 如果没有其他地点，使用默认位置
                    return (0.0, 0.0)
            
            # 处理正常地点
            if 'geometry' in place:
                return (
                    float(place['geometry']['location']['lat']),
                    float(place['geometry']['location']['lng'])
                )
            elif 'location' in place:
                return (
                    float(place['location']['lat']),
                    float(place['location']['lng'])
                )
            else:
                raise ValueError(f"Cannot find location in place data: {place}")
        except Exception as e:
            print(f"Error getting location from place: {place}")
            raise
    
    def calculate_distance_score(self) -> float:
        """
        计算路程优化得分
        
        评分标准：
        - 计算每天行程的总距离
        - 考虑每个地点间的实际距离
        - 评估路线是否形成了合理的路径
        """
        total_distance = 0
        max_possible_distance = 0
        
        for day, events in self.events_by_day.items():
            # 过滤出地点事件（排除交通事件）
            place_events = [e for e in events if e.get('type') == 'place']
            
            # 计算当天实际距离
            day_distance = 0
            for i in range(len(place_events) - 1):
                curr_place = place_events[i]['place']
                next_place = place_events[i + 1]['place']
                
                curr_lat, curr_lng = self._get_location(curr_place)
                next_lat, next_lng = self._get_location(next_place)
                
                distance = haversine_distance(
                    curr_lat, curr_lng,
                    next_lat, next_lng
                )
                day_distance += distance
            
            total_distance += day_distance
            
            # 计算最差情况的距离（作为基准）
            locations = []
            for event in place_events:
                lat, lng = self._get_location(event['place'])
                locations.append({'lat': lat, 'lng': lng})
            
            max_day_distance = self._calculate_max_possible_distance(locations)
            max_possible_distance += max_day_distance
        
        # 返回得分（0-100），距离越短得分越高
        if max_possible_distance == 0:
            return 100
        return 100 * (1 - total_distance / max_possible_distance)
    
    def calculate_time_window_score(self) -> float:
        """
        计算时间窗口满足度得分
        """
        total_events = 0
        satisfied_events = 0
        
        for day, events in self.events_by_day.items():
            for event in events:
                if event.get('type') != 'place':
                    continue
                    
                total_events += 1
                if not event.get('startTime') or not event.get('endTime'):
                    continue
                    
                start_time = datetime.strptime(event['startTime'], '%I:%M %p').time()
                end_time = datetime.strptime(event['endTime'], '%I:%M %p').time()
                
                place_type = 'restaurant' if 'restaurant' in event['place'].get('types', []) else 'attraction'
                
                if place_type == 'restaurant':
                    if (self._is_time_in_window(start_time, end_time, 
                                              PlaceConstraints.DINING_WINDOWS['lunch']) or
                        self._is_time_in_window(start_time, end_time, 
                                              PlaceConstraints.DINING_WINDOWS['dinner'])):
                        satisfied_events += 1
                else:
                    if (PlaceConstraints.DAY_CONSTRAINTS['start'] <= start_time and
                        end_time <= PlaceConstraints.DAY_CONSTRAINTS['end']):
                        satisfied_events += 1
        
        return 100 * (satisfied_events / total_events if total_events > 0 else 1)
    
    def calculate_distribution_score(self) -> float:
        """
        计算地点分布均匀性得分
        """
        daily_counts = []
        for day, events in self.events_by_day.items():
            place_count = len([e for e in events if e.get('type') == 'place'])
            daily_counts.append(place_count)
            
        if not daily_counts:
            return 100
            
        mean_count = np.mean(daily_counts)
        if mean_count == 0:
            return 100
            
        std_dev = np.std(daily_counts)
        cv = std_dev / mean_count  # 变异系数
        
        score = 100 * (1 - min(cv, 1))
        return score
    
    def calculate_clustering_score(self) -> float:
        """
        计算聚类紧凑度得分
        """
        if not self.events_by_day:
            return 100
            
        daily_scores = []
        for day, events in self.events_by_day.items():
            place_events = [e for e in events if e.get('type') == 'place']
            if len(place_events) < 2:
                continue
                
            distances = []
            for i in range(len(place_events) - 1):
                curr_place = place_events[i]['place']
                next_place = place_events[i + 1]['place']
                
                curr_lat, curr_lng = self._get_location(curr_place)
                next_lat, next_lng = self._get_location(next_place)
                
                distance = haversine_distance(
                    curr_lat, curr_lng,
                    next_lat, next_lng
                )
                distances.append(distance)
            
            avg_distance = np.mean(distances)
            max_reasonable_distance = 5000  # 5公里作为合理距离
            
            day_score = 100 * (1 - min(avg_distance / max_reasonable_distance, 1))
            daily_scores.append(day_score)
        
        return np.mean(daily_scores) if daily_scores else 100
    
    def _calculate_max_possible_distance(self, locations: List[Dict]) -> float:
        """计算给定地点集合可能的最大距离"""
        if len(locations) < 2:
            return 0
            
        max_distance = 0
        for i in range(len(locations)):
            for j in range(i + 1, len(locations)):
                distance = haversine_distance(
                    locations[i]['lat'],
                    locations[i]['lng'],
                    locations[j]['lat'],
                    locations[j]['lng']
                )
                max_distance = max(max_distance, distance)
        
        return max_distance * (len(locations) - 1)
    
    def _is_time_in_window(self, 
                          start: time, 
                          end: time, 
                          window: Dict[str, time]) -> bool:
        """检查时间是否在指定窗口内"""
        return (window['start'] <= start <= window['end'] and
                window['start'] <= end <= window['end'])