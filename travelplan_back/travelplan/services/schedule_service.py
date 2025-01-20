# services/schedule_service.py
from typing import List, Dict
from datetime import datetime
import logging
from .clustering import PlaceConstraints, preprocess_places, hierarchical_clustering
from .routing import optimize_day_route, generate_day_schedule
from .utils import (
    calculate_distance_matrix,
    validate_schedule,
    combine_schedules,
    calculate_schedule_metrics
)

logger = logging.getLogger(__name__)

class ScheduleService:
    def __init__(self):
        self.distance_matrix_cache = {}

    async def generate_schedule(
        self,
        places: List[Dict],
        start_date: str,
        end_date: str,
        transport_mode: str = 'driving'
    ) -> Dict:
        """生成行程安排"""
        try:
            # 1. 基本验证
            if not places:
                return {
                    'success': False,
                    'error': 'No places provided',
                    'schedule_status': {
                        'is_reasonable': False,
                        'warnings': [{
                            'type': 'error',
                            'message': 'No places were provided',
                            'suggestion': 'Please select some places to visit'
                        }],
                        'severity': 'severe'
                    }
                }
    
            # 2. 预处理地点数据
            processed_places = preprocess_places(places)
            if not processed_places:
                return {
                    'success': False,
                    'error': 'No valid places after preprocessing',
                    'schedule_status': {
                        'is_reasonable': False,
                        'warnings': [{
                            'type': 'error',
                            'message': 'No valid places found after processing',
                            'suggestion': 'Please check your place selection'
                        }],
                        'severity': 'severe'
                    }
                }
    
            # 3. 计算天数和验证合理性
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            num_days = (end - start).days + 1
            
            total_places = len(processed_places)
            restaurants = len([p for p in processed_places if p.get('is_restaurant', False)])
            attractions = total_places - restaurants
    
            # 验证天数和地点数的合理性
            if num_days * 8 < total_places:  # 假设每天最多安排8个地点
                return {
                    'success': False,
                    'schedule_status': {
                        'is_reasonable': False,
                        'warnings': [{
                            'type': 'error',
                            'message': f'Too many places ({total_places}) for {num_days} day(s)',
                            'suggestion': f'Consider either increasing the number of days or reducing the number of places. Recommended maximum is 8 places per day.'
                        }],
                        'severity': 'severe'
                    }
                }
    
            # 4. 继续现有的处理逻辑...
            # 获取距离矩阵
            distance_matrix, time_matrix = calculate_distance_matrix(
                processed_places,
                transport_mode,
                use_api=False
            )
            
            # 执行聚类
            clusters = hierarchical_clustering(
                processed_places,
                num_days,
                transport_mode
            )
            logger.info(f"Created {len(clusters)} clusters")
            for i, cluster in enumerate(clusters):
                logger.info(f"Cluster {i} has {len(cluster)} places")
                logger.debug(f"Cluster {i} first place: {cluster[0] if cluster else 'Empty cluster'}")
            
            # 添加已使用餐厅的跟踪
            used_restaurants_by_day = {i: set() for i in range(num_days)}
        
            # 5. 优化每天的路线
            all_schedules = []
            
            for day_index, cluster in enumerate(clusters):
                logger.info(f"Processing day {day_index}")
                if not cluster:
                    logger.warning(f"Empty cluster for day {day_index}, skipping")
                    continue
                    
                # 只过滤掉当天已使用的餐厅
                filtered_cluster = [
                    place for place in cluster 
                    if not (place.get('is_restaurant') and 
                           place.get('place_id') in used_restaurants_by_day[day_index])
                ]
                logger.debug(f"Filtered out {len(cluster) - len(filtered_cluster)} used restaurants")
                
                # 获取当天的距离矩阵
                day_distance_matrix, day_time_matrix = calculate_distance_matrix(
                    filtered_cluster,
                    transport_mode,
                    use_api=False
                )
                logger.info(f"Day {day_index} distance matrix shape: {day_distance_matrix.shape}")
                
                # 优化当天路线
                logger.info(f"Optimizing route for day {day_index}")
                try:
                    optimized_route, score = optimize_day_route(
                        filtered_cluster,
                        day_distance_matrix,
                        transport_mode
                    )
                    logger.info(f"Day {day_index} route optimized with score {score}")
                    
                    # 记录这一天使用的餐厅
                    for event in optimized_route:
                        if event['place'].get('is_restaurant'):
                            used_restaurants_by_day[day_index].add(
                                event['place'].get('place_id')
                            )
                            logger.debug(f"Added restaurant {event['place'].get('name')} to used list")
                    
                    # 为优化后的路线重新计算距离矩阵
                    optimized_places = [event['place'] for event in optimized_route]
                    optimized_distance_matrix, optimized_time_matrix = calculate_distance_matrix(
                        optimized_places,
                        transport_mode,
                        use_api=False
                    )
                    
                    # 生成当天的详细行程
                    day_schedule = generate_day_schedule(
                        optimized_route,
                        optimized_distance_matrix,  # 使用新的距离矩阵
                        optimized_time_matrix,      # 使用新的时间矩阵
                        transport_mode,
                        day_index
                    )
                    logger.info(f"Generated schedule for day {day_index} with {len(day_schedule)} events")
                    all_schedules.append(day_schedule)
                except Exception as e:
                    logger.error(f"Error processing day {day_index}: {str(e)}")
                    raise
            
            # 6. 合并所有日程
            combined_schedule = combine_schedules(all_schedules)
            logger.info(f"Combined schedule has {len(combined_schedule)} total events")
            
            # 7. 计算统计指标
            metrics = calculate_schedule_metrics(combined_schedule)
            logger.info("Schedule metrics calculated")
            
            # 在返回结果前添加合理性检查
            schedule_status = self.check_schedule_reasonability(
                processed_places,
                clusters,
                combined_schedule
            )
    
            return {
                'success': True,
                'events': combined_schedule,
                'metrics': metrics,
                'schedule_status': schedule_status  # 添加状态信息到返回结果
            }
                    
        except Exception as e:
            logger.error(f"Error in generate_schedule: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'schedule_status': {
                    'is_reasonable': False,
                    'warnings': [{
                        'type': 'error',
                        'message': 'Failed to generate schedule due to technical error',
                        'suggestion': 'Please try adjusting your selection or try again later'
                    }],
                    'severity': 'severe'
                }
            }
        


    def check_schedule_reasonability(
        self,
        processed_places: List[Dict],
        clusters: List[List[Dict]],
        combined_schedule: List[Dict]
    ) -> Dict:
        """检查行程安排的合理性并生成警告信息"""
        try:
            schedule_status = {
                'is_reasonable': True,
                'warnings': [],
                'severity': 'normal'  # normal/warning/severe
            }
    
            # 1. 检查空天数（只有虚拟餐厅的天数）
            empty_days = sum(1 for cluster in clusters if 
                            all(place.get('is_empty', False) for place in cluster))
            if empty_days > 0:
                schedule_status['warnings'].append({
                    'type': 'empty_days',
                    'message': f'Found {empty_days} days with only virtual restaurants. Your schedule might be too sparse.',
                    'suggestion': 'Consider reducing the number of days or adding more places to visit.'
                })
                schedule_status['severity'] = 'warning'
    
            # 2. 检查未被安排的地点
            scheduled_place_ids = set()
            for event in combined_schedule:
                if event.get('type') == 'place' and not event.get('place', {}).get('is_empty', False):
                    place_id = event.get('place', {}).get('place_id')
                    if place_id:
                        scheduled_place_ids.add(place_id)
    
            original_place_ids = set(
                place['place_id'] for place in processed_places 
                if not place.get('is_empty', False)
            )
            
            unscheduled_count = len(original_place_ids - scheduled_place_ids)
            if unscheduled_count > 0:
                schedule_status['warnings'].append({
                    'type': 'unscheduled_places',
                    'message': f'{unscheduled_count} places could not be scheduled. Your schedule might be too packed.',
                    'suggestion': 'Consider increasing the number of days or reducing the number of places.'
                })
                schedule_status['severity'] = 'severe'
    
            # 3. 检查每天的时间安排是否过满
            days_over_time = 0
            for day_events in clusters:
                last_event = next(
                    (event for event in reversed(combined_schedule) 
                    if event.get('type') == 'place' and 
                    event.get('day') == clusters.index(day_events)),
                    None
                )
                if last_event:
                    end_time = datetime.strptime(last_event['endTime'], '%I:%M %p').time()
                    if end_time > PlaceConstraints.DAY_CONSTRAINTS['end']:
                        days_over_time += 1
    
            if days_over_time > 0:
                schedule_status['warnings'].append({
                    'type': 'overtime_days',
                    'message': f'{days_over_time} days exceed the recommended end time of {PlaceConstraints.DAY_CONSTRAINTS["end"].strftime("%I:%M %p")}.',
                    'suggestion': 'Consider extending your trip duration or reducing the number of places per day.'
                })
                schedule_status['severity'] = 'severe'
    
            return schedule_status
    
        except Exception as e:
            logger.error(f"Error in check_schedule_reasonability: {str(e)}")
            return {
                'is_reasonable': False,
                'warnings': [{
                    'type': 'error',
                    'message': 'An error occurred while checking schedule reasonability.',
                    'suggestion': 'Please try again or contact support if the problem persists.'
                }],
                'severity': 'severe'
            }